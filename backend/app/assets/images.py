from __future__ import annotations

import io
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from PIL import Image, ImageColor, ImageOps, UnidentifiedImageError


MAX_DECODED_BYTES = 8 * 1024 * 1024
MAX_SOURCE_PIXELS = 20_000_000
MAX_OUTPUT_PIXELS = 16_000_000
SOURCE_DIMENSION_MIN = 16
SOURCE_DIMENSION_MAX = 6000
OUTPUT_DIMENSION_MIN = 32
OUTPUT_DIMENSION_MAX = 4096
BACKGROUND = re.compile(r"^#[a-fA-F0-9]{6}$")
SUPPORTED_SOURCE = {
    "PNG": "image/png",
    "JPEG": "image/jpeg",
    "WEBP": "image/webp",
}
OUTPUTS = {
    "png": ("PNG", "image/png", "png"),
    "jpeg": ("JPEG", "image/jpeg", "jpg"),
    "webp": ("WEBP", "image/webp", "webp"),
}


class AssetImageError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class NormalizedImage:
    data: bytes
    media_type: str
    extension: str
    width: int
    height: int
    source_format: str
    source_render_width: int
    source_render_height: int
    metadata_removed: bool
    second_decode_verified: bool
    resampling: str | None = None


def normalize_image(
    data: bytes,
    declared_media_type: str,
    output_format: str,
    *,
    quality: int = 90,
    background: str = "#ffffff",
) -> NormalizedImage:
    source, source_format = _load_source(data, declared_media_type)
    _validate_source_geometry(source.width, source.height)
    _validate_encoding_options(output_format, quality, background)
    return _encode_pixels(
        source,
        output_format=output_format,
        quality=quality,
        background=background,
        source_format=source_format,
        source_render_width=source.width,
        source_render_height=source.height,
        resampling=None,
    )


def transform_image(
    source_path: Path,
    *,
    source_media_type: str,
    width: int,
    height: int,
    mode: Literal["contain", "cover"] | str,
    output_format: str,
    quality: int,
    allow_upscale: bool,
    background: str,
) -> NormalizedImage:
    if not source_path.is_file():
        raise AssetImageError("source image path does not exist")
    if isinstance(width, bool) or isinstance(height, bool):
        raise AssetImageError("transform dimensions must be integers")
    if not isinstance(width, int) or not isinstance(height, int):
        raise AssetImageError("transform dimensions must be integers")
    if not (
        OUTPUT_DIMENSION_MIN <= width <= OUTPUT_DIMENSION_MAX
        and OUTPUT_DIMENSION_MIN <= height <= OUTPUT_DIMENSION_MAX
    ):
        raise AssetImageError("transform dimensions must be from 32 to 4096")
    if width * height > MAX_OUTPUT_PIXELS:
        raise AssetImageError("transform exceeds the 16000000 pixel limit")
    if mode not in {"contain", "cover"}:
        raise AssetImageError("transform mode must be contain or cover")
    if not isinstance(allow_upscale, bool):
        raise AssetImageError("allow_upscale must be a boolean")
    _validate_encoding_options(output_format, quality, background)

    try:
        data = source_path.read_bytes()
    except OSError as exc:
        raise AssetImageError("source image bytes could not be read") from exc
    source, source_format = _load_source(data, source_media_type)
    _validate_source_geometry(source.width, source.height)

    width_scale = width / source.width
    height_scale = height / source.height
    scale = min(width_scale, height_scale) if mode == "contain" else max(
        width_scale, height_scale
    )
    if not allow_upscale and scale > 1:
        if mode == "cover":
            raise AssetImageError(
                "cover transform requires upscaling but allow_upscale is false"
            )
        scale = 1.0
    render_width = max(1, int(round(source.width * scale)))
    render_height = max(1, int(round(source.height * scale)))
    resized = source.resize(
        (render_width, render_height),
        resample=Image.Resampling.LANCZOS,
    )

    if mode == "cover":
        left = max(0, (render_width - width) // 2)
        top = max(0, (render_height - height) // 2)
        pixels = resized.crop((left, top, left + width, top + height))
    else:
        canvas_mode = "RGBA" if "A" in resized.getbands() else "RGB"
        fill = (*ImageColor.getrgb(background), 255) if canvas_mode == "RGBA" else (
            ImageColor.getrgb(background)
        )
        pixels = Image.new(canvas_mode, (width, height), fill)
        left = (width - render_width) // 2
        top = (height - render_height) // 2
        if "A" in resized.getbands():
            pixels.paste(resized, (left, top), resized.getchannel("A"))
        else:
            pixels.paste(resized, (left, top))

    return _encode_pixels(
        pixels,
        output_format=output_format,
        quality=quality,
        background=background,
        source_format=source_format,
        source_render_width=render_width,
        source_render_height=render_height,
        resampling="lanczos",
    )


def _load_source(data: bytes, declared_media_type: str) -> tuple[Image.Image, str]:
    if not isinstance(data, bytes) or not 0 < len(data) <= MAX_DECODED_BYTES:
        raise AssetImageError(
            "decoded image must contain from 1 to 8388608 bytes"
        )
    if declared_media_type not in set(SUPPORTED_SOURCE.values()):
        raise AssetImageError("declared media type is unsupported")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as verifying:
                verifying.verify()
            with Image.open(io.BytesIO(data)) as opened:
                source_format = str(opened.format or "")
                actual_media_type = SUPPORTED_SOURCE.get(source_format)
                if actual_media_type != declared_media_type:
                    raise AssetImageError(
                        "declared media type does not match image signature"
                    )
                if getattr(opened, "n_frames", 1) != 1:
                    raise AssetImageError("animated images are not accepted")
                opened.seek(0)
                opened.load()
                oriented = ImageOps.exif_transpose(opened)
                if oriented.mode not in {"RGB", "RGBA", "L", "LA"}:
                    oriented = oriented.convert("RGBA" if "A" in oriented.getbands() else "RGB")
                else:
                    oriented = oriented.copy()
    except AssetImageError:
        raise
    except (
        OSError,
        SyntaxError,
        UnidentifiedImageError,
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
    ) as exc:
        raise AssetImageError("image decode or verification failed") from exc
    return oriented, source_format


def _validate_source_geometry(width: int, height: int) -> None:
    if not (
        SOURCE_DIMENSION_MIN <= width <= SOURCE_DIMENSION_MAX
        and SOURCE_DIMENSION_MIN <= height <= SOURCE_DIMENSION_MAX
    ):
        raise AssetImageError("source image dimensions must be from 16 to 6000")
    if width * height > MAX_SOURCE_PIXELS:
        raise AssetImageError("source image exceeds the 20000000 pixel limit")


def _validate_encoding_options(
    output_format: str,
    quality: int,
    background: str,
) -> None:
    if output_format not in OUTPUTS:
        raise AssetImageError("output format must be png, jpeg, or webp")
    if isinstance(quality, bool) or not isinstance(quality, int) or not 40 <= quality <= 100:
        raise AssetImageError("quality must be an integer from 40 to 100")
    if not isinstance(background, str) or BACKGROUND.fullmatch(background) is None:
        raise AssetImageError("background must be a six-digit hexadecimal color")


def _encode_pixels(
    pixels: Image.Image,
    *,
    output_format: str,
    quality: int,
    background: str,
    source_format: str,
    source_render_width: int,
    source_render_height: int,
    resampling: str | None,
) -> NormalizedImage:
    pillow_format, media_type, extension = OUTPUTS[output_format]
    prepared = _prepare_mode(pixels, output_format, background)
    output = io.BytesIO()
    if output_format == "png":
        prepared.save(output, format="PNG", compress_level=9, optimize=False)
    elif output_format == "jpeg":
        prepared.save(
            output,
            format="JPEG",
            quality=quality,
            subsampling=0,
            optimize=False,
            progressive=False,
        )
    else:
        prepared.save(
            output,
            format="WEBP",
            quality=quality,
            method=6,
            lossless=False,
            exact=True,
        )
    encoded = output.getvalue()
    if not 0 < len(encoded) <= MAX_DECODED_BYTES:
        raise AssetImageError("normalized image exceeds the 8388608 byte limit")
    _verify_output(
        encoded,
        expected_format=pillow_format,
        expected_size=prepared.size,
    )
    return NormalizedImage(
        data=encoded,
        media_type=media_type,
        extension=extension,
        width=prepared.width,
        height=prepared.height,
        source_format=source_format,
        source_render_width=source_render_width,
        source_render_height=source_render_height,
        metadata_removed=True,
        second_decode_verified=True,
        resampling=resampling,
    )


def _prepare_mode(
    pixels: Image.Image,
    output_format: str,
    background: str,
) -> Image.Image:
    if output_format == "jpeg":
        if "A" in pixels.getbands():
            base = Image.new("RGB", pixels.size, ImageColor.getrgb(background))
            rgba = pixels.convert("RGBA")
            base.paste(rgba, (0, 0), rgba.getchannel("A"))
            return base
        return pixels.convert("RGB")
    if "A" in pixels.getbands():
        return pixels.convert("RGBA")
    return pixels.convert("RGB")


def _verify_output(
    data: bytes,
    *,
    expected_format: str,
    expected_size: tuple[int, int],
) -> None:
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format != expected_format:
                raise AssetImageError("normalized image format verification failed")
            if image.size != expected_size:
                raise AssetImageError("normalized image dimensions changed after encoding")
            if getattr(image, "n_frames", 1) != 1:
                raise AssetImageError("normalized image unexpectedly contains animation")
            image.load()
            forbidden = {"exif", "icc_profile", "comment"}
            if forbidden & {key.lower() for key in image.info}:
                raise AssetImageError("normalized image still contains submitted metadata")
    except AssetImageError:
        raise
    except (OSError, UnidentifiedImageError) as exc:
        raise AssetImageError("normalized image failed second decode") from exc
