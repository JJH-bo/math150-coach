from __future__ import annotations

import re

import pytest

from app.challenge.chapter_galaxy_asset import build_chapter_galaxy_asset
from test_chapter_galaxy_builder import _chapter_markdown


def test_canonical_galaxy_asset_preserves_semantic_links() -> None:
    asset = build_chapter_galaxy_asset(_chapter_markdown())

    assert asset["chapterId"] == "demo"
    assert asset["metrics"] == {
        "systemCount": 2,
        "planetCount": 6,
        "bossCount": 1,
    }
    assert asset["systems"][0]["links"] == [
        {
            "sourceId": "demo.system_01.concept",
            "targetId": "demo.system_01.trigger",
            "edgeType": "supports",
        },
        {
            "sourceId": "demo.system_01.trigger",
            "targetId": "demo.system_01.method",
            "edgeType": "supports",
        },
    ]


def test_canonical_galaxy_asset_rejects_disconnected_system() -> None:
    disconnected = re.sub(
        r"(?m)^\|\s*demo\.edge\.02\s*\|.*(?:\n|$)",
        "",
        _chapter_markdown(),
    )

    with pytest.raises(ValueError, match="missing visible supports edges"):
        build_chapter_galaxy_asset(disconnected)
