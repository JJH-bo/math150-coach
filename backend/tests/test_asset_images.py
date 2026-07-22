from __future__ import annotations

import io

import pytest
from PIL import Image

from app.assets.images import (
    AssetImageError,
    normalize_image,
    transform_image,
)


def image_bytes(
    image_format: str,
    *,
    size: tuple[int, int] = (120, 80),
    mode: str = "RGB",
    color=(30, 120, 210),
    exif_orientation: int | None = None,
) -> bytes:
    image = Image.new(mode, size, color)
    options = {}
    if exif_orientation is not None:
        exif = Image.Exif()
        exif[274] = exif_orientation
        options["exif"] = exif
    output = io.BytesIO()
    image.save(output, format=image_format, **options)
    return output.getvalue()


def animated_png_bytes() -> bytes:
    first = Image.new("RGB", (32, 32), "red")
    second = Image.new("RGB", (32, 32), "blue")
    output = io.BytesIO()
    first.save(
        output,
        format="PNG",
        save_all=True,
        append_images=[second],
        duration=100,
        loop=0,
    )
    return output.getvalue()


def test_normalization_sniffs_type_strips_metadata_and_is_repeatable() -> None:
    source = image_bytes("JPEG", exif_orientation=6)

    first = normalize_image(source, "image/jpeg", "png")
    second = normalize_image(source, "image/jpeg", "png")

    assert (first.width, first.height) == (80, 120)
    assert first.media_type == "image/png"
    assert first.extension == "png"
    assert first.source_format == "JPEG"
    assert first.data == second.data
    assert first.second_decode_verified is True
    assert first.metadata_removed is True
    with Image.open(io.BytesIO(first.data)) as image:
        image.load()
        assert image.getexif() == {}
        assert not {"exif", "icc_profile", "comment"} & {
            key.lower() for key in image.info
        }


def test_normalization_supports_png_jpeg_and_webp_outputs() -> None:
    source = image_bytes("PNG", mode="RGBA", color=(20, 60, 100, 128))

    png = normalize_image(source, "image/png", "png")
    jpeg = normalize_image(source, "image/png", "jpeg", background="#ffffff")
    webp = normalize_image(source, "image/png", "webp")

    assert (png.media_type, jpeg.media_type, webp.media_type) == (
        "image/png",
        "image/jpeg",
        "image/webp",
    )
    with Image.open(io.BytesIO(jpeg.data)) as image:
        assert image.mode == "RGB"


@pytest.mark.parametrize(
    "data,declared,error",
    [
        (image_bytes("PNG"), "image/jpeg", "does not match"),
        (animated_png_bytes(), "image/png", "animated"),
        (image_bytes("PNG", size=(8, 32)), "image/png", "dimensions"),
        (b"not an image", "image/png", "decode"),
    ],
)
def test_invalid_images_are_rejected(data: bytes, declared: str, error: str) -> None:
    with pytest.raises(AssetImageError, match=error):
        normalize_image(data, declared, "png")


def test_image_pixel_limit_is_enforced(monkeypatch) -> None:
    monkeypatch.setattr("app.assets.images.MAX_SOURCE_PIXELS", 200)

    with pytest.raises(AssetImageError, match="pixel limit"):
        normalize_image(
            image_bytes("PNG", size=(16, 16)),
            "image/png",
            "png",
        )


def test_cover_transform_uses_exact_geometry_and_lanczos(tmp_path) -> None:
    source_path = tmp_path / "source.png"
    source_path.write_bytes(image_bytes("PNG", size=(200, 100)))

    output = transform_image(
        source_path,
        source_media_type="image/png",
        width=100,
        height=100,
        mode="cover",
        output_format="webp",
        quality=88,
        allow_upscale=False,
        background="#ffffff",
    )

    assert (output.width, output.height) == (100, 100)
    assert output.media_type == "image/webp"
    assert output.resampling == "lanczos"
    assert output.second_decode_verified is True


def test_contain_transform_does_not_upscale_source_pixels(tmp_path) -> None:
    source_path = tmp_path / "source.png"
    source_path.write_bytes(image_bytes("PNG", size=(100, 50), color=(255, 0, 0)))

    output = transform_image(
        source_path,
        source_media_type="image/png",
        width=200,
        height=200,
        mode="contain",
        output_format="png",
        quality=90,
        allow_upscale=False,
        background="#ffffff",
    )

    with Image.open(io.BytesIO(output.data)) as image:
        assert image.size == (200, 200)
        assert image.getpixel((100, 100))[:3] == (255, 0, 0)
        assert image.getpixel((10, 10))[:3] == (255, 255, 255)
    assert output.source_render_width == 100
    assert output.source_render_height == 50


@pytest.mark.parametrize(
    "overrides,error",
    [
        ({"width": 31}, "dimensions"),
        ({"width": 4097}, "dimensions"),
        ({"quality": 39}, "quality"),
        ({"mode": "stretch"}, "mode"),
        ({"background": "red"}, "background"),
    ],
)
def test_transform_rejects_invalid_options(tmp_path, overrides, error: str) -> None:
    source_path = tmp_path / "source.png"
    source_path.write_bytes(image_bytes("PNG"))
    arguments = {
        "source_media_type": "image/png",
        "width": 320,
        "height": 180,
        "mode": "contain",
        "output_format": "png",
        "quality": 90,
        "allow_upscale": False,
        "background": "#ffffff",
        **overrides,
    }

    with pytest.raises(AssetImageError, match=error):
        transform_image(source_path, **arguments)
