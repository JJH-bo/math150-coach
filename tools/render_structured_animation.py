from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

import av
from PIL import Image, ImageStat
from manim import (
    Arrow,
    Axes,
    Circle,
    Create,
    Dot,
    FadeIn,
    FadeOut,
    Indicate,
    Line,
    Rectangle,
    Scene,
    Text,
    Transform,
    VMobject,
    Write,
    __version__ as manim_version,
    tempconfig,
)


def point(value: list[float]) -> list[float]:
    return [float(value[0]), float(value[1]), 0.0]


def make_objects(specification: dict) -> dict[str, object]:
    objects: dict[str, object] = {}
    for item in specification["objects"]:
        kind = item["type"]
        color = item["color"]
        if kind == "axes":
            value = Axes(
                x_range=item["x_range"],
                y_range=item["y_range"],
                x_length=item["x_length"],
                y_length=item["y_length"],
                tips=False,
                axis_config={"color": color, "stroke_width": 2},
            ).move_to(point(item["position"]))
        elif kind == "polyline":
            axes = objects.get(item.get("axes_id"))
            points = [
                axes.c2p(*coordinate) if axes is not None else point(coordinate)
                for coordinate in item["points"]
            ]
            value = VMobject(color=color, stroke_width=item["stroke_width"])
            value.set_points_smoothly(points)
        elif kind == "dot":
            value = Dot(
                point=point(item["position"]),
                radius=item["radius"],
                color=color,
            )
        elif kind == "line":
            value = Line(
                start=point(item["start"]),
                end=point(item["end"]),
                color=color,
                stroke_width=item["stroke_width"],
            )
        elif kind == "arrow":
            value = Arrow(
                start=point(item["start"]),
                end=point(item["end"]),
                color=color,
                stroke_width=item["stroke_width"],
                buff=0,
            )
        elif kind == "circle":
            value = Circle(
                radius=item["radius"],
                color=color,
                fill_opacity=item["fill_opacity"],
            ).move_to(point(item["position"]))
        elif kind == "rectangle":
            value = Rectangle(
                width=item["width"],
                height=item["height"],
                color=color,
                fill_opacity=item["fill_opacity"],
            ).move_to(point(item["position"]))
        elif kind == "text":
            value = Text(
                item["text"],
                font_size=item["font_size"],
                color=color,
            ).move_to(point(item["position"]))
        else:
            raise ValueError(f"unsupported object type: {kind}")
        objects[item["id"]] = value
    return objects


def scene_class(specification: dict):
    class StructuredAnimation(Scene):
        def construct(self) -> None:
            objects = make_objects(specification)
            for action in specification["timeline"]:
                kind = action["action"]
                duration = action["duration"]
                if kind == "wait":
                    self.wait(duration)
                    continue
                value = objects[action["object_id"]]
                if kind == "create":
                    self.play(Create(value), run_time=duration)
                elif kind == "write":
                    self.play(Write(value), run_time=duration)
                elif kind == "fade_in":
                    self.play(FadeIn(value), run_time=duration)
                elif kind == "fade_out":
                    self.play(FadeOut(value), run_time=duration)
                elif kind == "move_to":
                    self.play(value.animate.move_to(point(action["to"])), run_time=duration)
                elif kind == "set_color":
                    self.play(value.animate.set_color(action["color"]), run_time=duration)
                elif kind == "indicate":
                    self.play(Indicate(value, color=action["color"]), run_time=duration)
                elif kind == "transform":
                    self.play(
                        Transform(value, objects[action["target_id"]]),
                        run_time=duration,
                    )
                else:
                    raise ValueError(f"unsupported timeline action: {kind}")

    return StructuredAnimation


def render(specification: dict, output_root: Path) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)
    output_format = specification["output_format"]
    settings = {
        "pixel_width": specification["width"],
        "pixel_height": specification["height"],
        "frame_rate": specification["fps"],
        "background_color": specification["background"],
        "media_dir": str(output_root / "media"),
        "output_file": "structured-animation",
        "format": output_format,
        "write_to_movie": True,
        "disable_caching": True,
        "verbosity": "WARNING",
        "progress_bar": "none",
    }
    with tempconfig(settings):
        scene = scene_class(specification)()
        scene.render()
        generated = Path(scene.renderer.file_writer.movie_file_path)
    if not generated.is_file():
        matches = list((output_root / "media").rglob(f"structured-animation.{output_format}"))
        if len(matches) == 1:
            generated = matches[0]
    if not generated.is_file() or generated.stat().st_size == 0:
        raise RuntimeError("Manim did not produce a video artifact")
    target = output_root / f"animation.{output_format}"
    shutil.copyfile(generated, target)
    return target


def video_samples(video_path: Path) -> tuple[dict, list[Image.Image]]:
    with av.open(str(video_path)) as container:
        stream = container.streams.video[0]
        expected_frames = int(stream.frames or 0)
        rate = float(stream.average_rate or 0)
        codec = stream.codec_context.name
        width = int(stream.width)
        height = int(stream.height)
    if expected_frames <= 0:
        with av.open(str(video_path)) as container:
            expected_frames = sum(1 for _ in container.decode(video=0))
    targets = sorted(
        {
            0,
            max(0, expected_frames // 4),
            max(0, expected_frames // 2),
            max(0, (3 * expected_frames) // 4),
            max(0, expected_frames - 1),
        }
    )
    samples: dict[int, Image.Image] = {}
    decoded = 0
    last: Image.Image | None = None
    with av.open(str(video_path)) as container:
        for index, frame in enumerate(container.decode(video=0)):
            image = frame.to_image().convert("RGB")
            decoded += 1
            last = image
            if index in targets:
                samples[index] = image.copy()
    if last is not None:
        samples[decoded - 1] = last
    if decoded <= 0 or not samples:
        raise RuntimeError("rendered animation contains no decodable video frames")
    ordered = [samples[index] for index in sorted(samples)]
    return (
        {
            "width": width,
            "height": height,
            "fps": rate,
            "frame_count": decoded,
            "duration_seconds": decoded / rate if rate else 0,
            "codec": codec,
        },
        ordered,
    )


def image_metrics(image: Image.Image) -> dict:
    sample = image.copy()
    sample.thumbnail((160, 90))
    colors = sample.getcolors(maxcolors=160 * 90)
    unique = len(colors) if colors is not None else 160 * 90
    variance = sum(float(value) for value in ImageStat.Stat(sample).var)
    digest = hashlib.sha256(sample.tobytes()).hexdigest()
    return {"unique_colors": unique, "channel_variance": variance, "sha256": digest}


def write_visual_evidence(
    samples: list[Image.Image],
    output_root: Path,
) -> tuple[Path, Path, list[dict]]:
    metrics = [image_metrics(image) for image in samples]
    poster_index = max(range(len(samples)), key=lambda index: metrics[index]["channel_variance"])
    poster_path = output_root / "poster.png"
    samples[poster_index].save(poster_path)
    thumbnails = []
    for image in samples:
        thumbnail = image.copy()
        thumbnail.thumbnail((320, 180))
        frame = Image.new("RGB", (320, 180), "#0B1119")
        frame.paste(
            thumbnail,
            ((320 - thumbnail.width) // 2, (180 - thumbnail.height) // 2),
        )
        thumbnails.append(frame)
    sheet = Image.new("RGB", (320 * len(thumbnails), 180), "#0B1119")
    for index, image in enumerate(thumbnails):
        sheet.paste(image, (index * 320, 0))
    sheet_path = output_root / "frame-sheet.png"
    sheet.save(sheet_path)
    return poster_path, sheet_path, metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spec", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    arguments = parser.parse_args()
    specification = json.loads(arguments.spec.read_text(encoding="utf-8"))
    video_path = render(specification, arguments.output)
    video, samples = video_samples(video_path)
    poster_path, sheet_path, metrics = write_visual_evidence(samples, arguments.output)
    expected_duration = specification["timeline"][-1]["end_seconds"]
    distinct = len({item["sha256"] for item in metrics})
    nonblank_samples = sum(
        item["unique_colors"] >= 20 and item["channel_variance"] > 1
        for item in metrics
    )
    nonblank = nonblank_samples >= max(2, len(metrics) - 1)
    fps_tolerance = 2.0 if specification["output_format"] == "gif" else 0.1
    report = {
        "passed": (
            video["width"] == specification["width"]
            and video["height"] == specification["height"]
            and abs(video["fps"] - specification["fps"]) <= fps_tolerance
            and video["frame_count"] >= max(2, int(expected_duration * specification["fps"] * 0.8))
            and distinct >= 3
            and nonblank
        ),
        "manim_version": manim_version,
        **video,
        "expected_duration_seconds": expected_duration,
        "requested_fps": specification["fps"],
        "fps_tolerance": fps_tolerance,
        "distinct_frame_count": distinct,
        "nonblank": nonblank,
        "nonblank_sample_count": nonblank_samples,
        "sample_metrics": metrics,
        "video_bytes": video_path.stat().st_size,
        "poster_bytes": poster_path.stat().st_size,
        "frame_sheet_bytes": sheet_path.stat().st_size,
    }
    arguments.report.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    if not report["passed"]:
        raise RuntimeError(f"animation quality gates failed: {report}")


if __name__ == "__main__":
    main()
