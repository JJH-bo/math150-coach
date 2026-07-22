from __future__ import annotations

import io

from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.assets.images import normalize_image
from app.assets.repository import AssetRepository
from app.classroom.models import ClassroomPackage
from app.classroom.repository import ClassroomRepository
from app.classroom.runtime import ClassroomRuntimeService
from app.classroom.validation import ClassroomPackageValidator
from classroom_fixtures import classroom_package_payload


def source_png() -> bytes:
    image = Image.new("RGB", (160, 100), (242, 248, 252))
    for x in range(30, 130):
        for y in range(25, 75):
            image.putpixel((x, y), (28, 132, 214))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def stored_asset(repository: AssetRepository):
    normalized = normalize_image(source_png(), "image/png", "png")
    return repository.put(
        normalized.data,
        media_type=normalized.media_type,
        extension=normalized.extension,
        width=normalized.width,
        height=normalized.height,
        display_filename="limit-neighborhood.png",
    )[0]


def package_with_image(record) -> ClassroomPackage:
    payload = classroom_package_payload()
    block = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]
    block["kind"] = "image"
    block["data"] = {
        "asset_id": record.asset_id,
        "uri": record.uri,
        "alt": "A blue neighborhood rectangle centered on a pale coordinate plane.",
        "caption": "Verified visual of the local neighborhood.",
    }
    payload["assets"] = [
        {
            "asset_id": record.asset_id,
            "media_type": record.media_type,
            "uri": record.uri,
            "content_hash": record.content_hash,
        }
    ]
    return ClassroomPackage.model_validate(payload)


def test_registered_image_asset_passes_cross_object_validation(tmp_path) -> None:
    assets = AssetRepository(tmp_path)
    record = stored_asset(assets)

    report = ClassroomPackageValidator(asset_resolver=assets.get).validate(
        package_with_image(record)
    )

    assert report.passed is True
    assert report.issues == []


def test_package_rejects_missing_registry_and_undeclared_image(tmp_path) -> None:
    assets = AssetRepository(tmp_path)
    record = stored_asset(assets)
    package = package_with_image(record)
    package.assets.clear()

    no_registry = ClassroomPackageValidator().validate(package_with_image(record))
    undeclared = ClassroomPackageValidator(asset_resolver=assets.get).validate(package)

    assert "asset_registry_unavailable" in {issue.code for issue in no_registry.issues}
    assert "undeclared_image_asset" in {issue.code for issue in undeclared.issues}


def test_package_rejects_tampered_declarations_and_noncanonical_uri(tmp_path) -> None:
    assets = AssetRepository(tmp_path)
    record = stored_asset(assets)
    payload = package_with_image(record).model_dump(mode="json")
    payload["assets"][0]["content_hash"] = "sha256:" + "0" * 64
    payload["assets"][0]["media_type"] = "image/jpeg"
    payload["assets"][0]["uri"] = "https://example.test/image.png"
    image = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]
    image["data"]["uri"] = "https://example.test/image.png"

    report = ClassroomPackageValidator(asset_resolver=assets.get).validate(
        ClassroomPackage.model_validate(payload)
    )

    assert {
        "asset_content_hash_mismatch",
        "asset_media_type_mismatch",
        "noncanonical_asset_uri",
        "noncanonical_image_uri",
    } <= {issue.code for issue in report.issues}


def test_image_block_requires_meaningful_alt_text_and_known_asset(tmp_path) -> None:
    assets = AssetRepository(tmp_path)
    record = stored_asset(assets)
    payload = package_with_image(record).model_dump(mode="json")
    image = payload["courses"][0]["chapters"][0]["modules"][0]["segments"][0][
        "blocks"
    ][0]
    image["data"]["asset_id"] = "a-" + "1" * 64
    image["data"]["uri"] = "/api/classroom/v1/assets/a-" + "1" * 64
    image["data"]["alt"] = "  "

    report = ClassroomPackageValidator(asset_resolver=assets.get).validate(
        ClassroomPackage.model_validate(payload)
    )

    assert {"undeclared_image_asset", "image_alt_text_required"} <= {
        issue.code for issue in report.issues
    }


def test_learner_asset_response_is_immutable_and_conditional(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setenv("CLASSROOM_DATA_ROOT", str(tmp_path))
    assets = AssetRepository(tmp_path)
    record = stored_asset(assets)
    client = TestClient(create_app("mixed"))
    etag = f'"{record.content_hash.removeprefix("sha256:")}"'

    response = client.get(f"/api/classroom/v1/assets/{record.asset_id}")
    unchanged = client.get(
        f"/api/classroom/v1/assets/{record.asset_id}",
        headers={"If-None-Match": etag},
    )
    missing = client.get("/api/classroom/v1/assets/a-" + "1" * 64)

    assert response.status_code == 200
    assert response.headers["etag"] == etag
    assert response.headers["cache-control"] == (
        "public, max-age=31536000, immutable"
    )
    assert response.headers["content-type"] == "image/png"
    assert response.content == assets.path(record.asset_id).read_bytes()
    assert unchanged.status_code == 304
    assert unchanged.content == b""
    assert missing.status_code == 404


def test_module_runtime_returns_only_referenced_asset_declarations(tmp_path) -> None:
    assets = AssetRepository(tmp_path)
    record = stored_asset(assets)
    classrooms = ClassroomRepository(tmp_path)
    package = package_with_image(record)
    draft = classrooms.create_draft("asset-classroom", package)
    classrooms.publish(draft.draft_id, draft.revision)
    runtime = ClassroomRuntimeService(classrooms, asset_repository=assets)

    payload = runtime.module(package.package_id, "limit-core")

    assert payload["assets"] == [package.assets[0].model_dump(mode="json")]
