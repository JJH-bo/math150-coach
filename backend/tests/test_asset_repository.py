from __future__ import annotations

import json

import pytest

from app.assets.repository import (
    AssetCorruptionError,
    AssetPathError,
    AssetRepository,
    AssetRepositoryError,
)


def test_repository_is_content_addressed_and_deduplicates(tmp_path) -> None:
    repository = AssetRepository(tmp_path)

    first, duplicate = repository.put(
        b"verified-image-bytes",
        media_type="image/png",
        extension="png",
        width=64,
        height=48,
        display_filename="diagram.png",
    )
    second, repeated = repository.put(
        b"verified-image-bytes",
        media_type="image/png",
        extension="png",
        width=64,
        height=48,
        display_filename="renamed.png",
    )

    assert first.asset_id == second.asset_id
    assert first.asset_id == "a-" + first.content_hash.removeprefix("sha256:")
    assert first.uri == f"/api/classroom/v1/assets/{first.asset_id}"
    assert duplicate is False
    assert repeated is True
    assert repository.path(first.asset_id).read_bytes() == b"verified-image-bytes"
    assert repository.get(first.asset_id) == first


def test_repository_uses_safe_content_addressed_paths(tmp_path) -> None:
    repository = AssetRepository(tmp_path)
    record, _ = repository.put(
        b"bytes",
        media_type="image/webp",
        extension="webp",
        width=32,
        height=32,
        display_filename="../../unsafe name.webp",
    )

    path = repository.path(record.asset_id)
    digest = record.content_hash.removeprefix("sha256:")

    assert path == (
        tmp_path.resolve()
        / "assets"
        / "sha256"
        / digest[:2]
        / digest
        / "asset.webp"
    )
    assert record.display_filename == "unsafe-name.webp"


@pytest.mark.parametrize(
    "asset_id",
    ["../outside", "a-xyz", "A-" + "1" * 64, "a-" + "1" * 63],
)
def test_repository_rejects_unsafe_asset_ids(tmp_path, asset_id: str) -> None:
    with pytest.raises(AssetPathError):
        AssetRepository(tmp_path).get(asset_id)


def test_repository_detects_byte_and_record_corruption(tmp_path) -> None:
    repository = AssetRepository(tmp_path)
    record, _ = repository.put(
        b"original",
        media_type="image/jpeg",
        extension="jpg",
        width=80,
        height=60,
        display_filename="photo.jpg",
    )
    asset_path = repository.path(record.asset_id)
    asset_path.write_bytes(b"tampered")

    with pytest.raises(AssetCorruptionError, match="hash"):
        repository.get(record.asset_id)

    asset_path.write_bytes(b"original")
    record_path = asset_path.with_name("record.json")
    payload = json.loads(record_path.read_text(encoding="utf-8"))
    payload["width"] = 999
    record_path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(AssetCorruptionError, match="metadata"):
        repository.get(record.asset_id)


def test_repository_rejects_invalid_storage_metadata(tmp_path) -> None:
    repository = AssetRepository(tmp_path)

    with pytest.raises(AssetRepositoryError):
        repository.put(
            b"bytes",
            media_type="image/png",
            extension="jpg",
            width=32,
            height=32,
            display_filename="mismatch.jpg",
        )
    with pytest.raises(AssetRepositoryError):
        repository.put(
            b"",
            media_type="image/png",
            extension="png",
            width=32,
            height=32,
            display_filename="empty.png",
        )
