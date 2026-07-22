from __future__ import annotations

import argparse
import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


EXPECTED_VERIFIED_TOOLS = {
    "asset.ingest",
    "asset.transform",
    "classroom.patch",
    "export.html",
    "export.package",
    "export.pdf",
    "export.pptx",
    "export.reveal",
    "math.graph",
    "math.numeric",
    "math.symbolic",
    "math.verify",
    "page.preview",
    "template.instantiate",
    "template.list",
    "visualization.animation",
    "visualization.diagram",
    "visualization.geometry2d",
    "visualization.plot",
    "visualization.scene3d",
}


def _request(
    origin: str,
    path: str,
    api_key: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> tuple[bytes, str]:
    headers = {"Authorization": f"Bearer {api_key}"}
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if idempotency_key is not None:
        headers["Idempotency-Key"] = idempotency_key
    request = urllib.request.Request(
        f"{origin.rstrip('/')}{path}", data=data, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read(), response.headers.get_content_type()
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise AssertionError(f"{method} {path} failed with HTTP {exc.code}: {body}") from exc


def _json_request(
    origin: str,
    path: str,
    api_key: str,
    *,
    method: str = "GET",
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
) -> dict[str, Any]:
    body, media_type = _request(
        origin,
        path,
        api_key,
        method=method,
        payload=payload,
        idempotency_key=idempotency_key,
    )
    assert media_type == "application/json", f"expected JSON from {path}, got {media_type}"
    value = json.loads(body)
    assert isinstance(value, dict), f"expected an object from {path}"
    return value


def validate_registry_payload(payload: dict[str, Any]) -> None:
    tools = payload.get("tools")
    assert isinstance(tools, list), "verified tool catalog did not contain a tools list"
    actual = {
        item.get("tool_id")
        for item in tools
        if isinstance(item, dict) and item.get("quality_tier") == "verified"
    }
    if payload.get("total") != len(EXPECTED_VERIFIED_TOOLS) or actual != EXPECTED_VERIFIED_TOOLS:
        missing = sorted(EXPECTED_VERIFIED_TOOLS - actual)
        unexpected = sorted(actual - EXPECTED_VERIFIED_TOOLS)
        raise AssertionError(
            "verified tool catalog mismatch: "
            f"total={payload.get('total')}, missing={missing}, unexpected={unexpected}"
        )


def verify_runtime(origin: str, api_key: str, specification: dict[str, Any]) -> None:
    registry = _json_request(origin, "/api/studio/v1/tools?quality_tier=verified", api_key)
    validate_registry_payload(registry)

    job = _json_request(
        origin,
        "/api/studio/v1/tool-jobs",
        api_key,
        method="POST",
        payload={
            "tool_id": "visualization.animation",
            "tool_version": "1.0.0",
            "arguments": specification,
        },
        idempotency_key="production-image-animation-smoke-v1",
    )
    job_id = job.get("job_id")
    assert isinstance(job_id, str), "animation submission did not return a job ID"
    deadline = time.monotonic() + 240
    while job.get("state") in {"queued", "running"} and time.monotonic() < deadline:
        time.sleep(1)
        job = _json_request(origin, f"/api/studio/v1/tool-jobs/{job_id}", api_key)
    assert job.get("state") == "succeeded", f"animation smoke job failed: {job.get('error')}"

    validation = (job.get("result") or {}).get("validation") or {}
    assert validation.get("passed") is True, "animation validation did not pass"
    assert validation.get("manim_version") == "0.20.1", "unexpected Manim version"
    assert validation.get("nonblank") is True, "animation output was visually blank"
    assert validation.get("distinct_frame_count", 0) >= 3, "animation did not change over time"

    artifacts = {item.get("name"): item for item in job.get("artifacts", [])}
    required = {
        "animation.json",
        "animation.mp4",
        "poster.png",
        "frame-sheet.png",
        "captions.vtt",
        "alt.txt",
        "validation.json",
    }
    assert required <= artifacts.keys(), f"animation artifacts missing: {sorted(required - artifacts.keys())}"
    video, media_type = _request(
        origin,
        artifacts["animation.mp4"]["download_path"],
        api_key,
    )
    assert media_type == "video/mp4", f"unexpected animation media type: {media_type}"
    assert b"ftyp" in video[:32] and len(video) > 1_000, "downloaded animation is not a real MP4"

    print(
        json.dumps(
            {
                "status": "passed",
                "verified_tool_count": len(EXPECTED_VERIFIED_TOOLS),
                "animation_job_id": job_id,
                "animation_bytes": len(video),
                "manim_version": validation["manim_version"],
                "distinct_frame_count": validation["distinct_frame_count"],
            },
            sort_keys=True,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify the production Studio tool runtime.")
    parser.add_argument("--origin", default="http://127.0.0.1:8000")
    parser.add_argument(
        "--spec",
        type=Path,
        default=Path("tools/fixtures/production-animation.json"),
    )
    args = parser.parse_args()
    api_key = os.getenv("STUDIO_API_KEY", "")
    if not api_key:
        raise SystemExit("STUDIO_API_KEY must be configured for the production smoke test")
    specification = json.loads(args.spec.read_text(encoding="utf-8"))
    verify_runtime(args.origin, api_key, specification)


if __name__ == "__main__":
    main()
