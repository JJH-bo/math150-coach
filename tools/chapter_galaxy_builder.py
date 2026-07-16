from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


TABLE_SECTIONS = {"GalaxyPlan", "GalaxyBoss", "MacroNodes", "MicroNodes"}
MICRO_TYPES = {"concept", "trigger", "method", "transformation", "calculation", "expression"}


def build_chapter_asset(markdown: str) -> dict[str, Any]:
    metadata = _parse_metadata(markdown)
    tables = _parse_tables(markdown)
    missing = sorted(TABLE_SECTIONS - tables.keys())
    if missing:
        raise ValueError(f"missing chapter sections: {', '.join(missing)}")

    chapter_id = metadata.get("chapter_id", "").strip()
    title = metadata.get("title", "").strip()
    if not chapter_id or not title:
        raise ValueError("chapter_id and title are required")

    galaxy_rows = tables["GalaxyPlan"]
    macro_rows = {row["id"]: row for row in tables["MacroNodes"]}
    micro_rows = tables["MicroNodes"]
    training_assets = _parse_training_assets(markdown)
    boss_rows = tables["GalaxyBoss"]
    if len(boss_rows) != 1:
        raise ValueError("GalaxyBoss must contain exactly one row")

    systems: list[dict[str, Any]] = []
    seen_planets: set[str] = set()
    for galaxy in sorted(galaxy_rows, key=lambda row: _integer(row.get("learning_order"), 9999)):
        system_id = galaxy.get("system_id", "").strip()
        macro_id = galaxy.get("macro_node_id", "").strip()
        if not system_id or macro_id not in macro_rows:
            raise ValueError(f"GalaxyPlan references unknown MacroNode: {system_id or macro_id}")
        planets: list[dict[str, Any]] = []
        for micro in (row for row in micro_rows if row.get("macro_node_id", "").strip() == macro_id):
            node_id = micro.get("id", "").strip()
            node_type = micro.get("type", "").strip()
            if node_type not in MICRO_TYPES:
                raise ValueError(f"unsupported MicroNode type for {node_id}: {node_type}")
            training = training_assets.get(node_id)
            if not training:
                raise ValueError(f"missing TrainingAssets block for {node_id}")
            if node_id in seen_planets:
                raise ValueError(f"duplicate MicroNode id: {node_id}")
            seen_planets.add(node_id)
            planets.append({
                "id": node_id,
                "macroId": macro_id,
                "type": node_type,
                "title": micro.get("title", "").strip(),
                "description": micro.get("description", "").strip(),
                "training": training,
            })
        declared_count = _integer(galaxy.get("planet_count"), -1)
        if declared_count != len(planets):
            raise ValueError(
                f"planet_count mismatch for {system_id}: declared {declared_count}, actual {len(planets)}"
            )
        if not 3 <= len(planets) <= 5:
            raise ValueError(f"system {system_id} must contain 3-5 planets")
        systems.append({
            "id": system_id,
            "macroNodeId": macro_id,
            "title": galaxy.get("title", "").strip() or macro_rows[macro_id].get("title", "").strip(),
            "coreQuestion": galaxy.get("core_question", "").strip(),
            "learningOrder": _integer(galaxy.get("learning_order"), len(systems) + 1),
            "visualPriority": galaxy.get("visual_priority", "medium").strip(),
            "recommendedDepth": galaxy.get("recommended_depth", "middle").strip(),
            "preferredSector": galaxy.get("preferred_sector", "flexible").strip(),
            "prerequisiteSystemIds": _split_list(galaxy.get("prerequisite_system_ids", "")),
            "bossContribution": galaxy.get("boss_contribution", "").strip(),
            "spacingReason": galaxy.get("spacing_reason", "").strip(),
            "sourceEvidence": galaxy.get("source_evidence", "").strip(),
            "planets": planets,
        })

    boss_row = boss_rows[0]
    boss_training = _parse_boss_training_asset(markdown)
    boss_id = boss_row.get("id", "").strip()
    if boss_training.get("bossId") and boss_training["bossId"] != boss_id:
        raise ValueError("GalaxyBoss and BossTrainingAsset ids do not match")
    boss = {
        "id": boss_id,
        "title": boss_row.get("title", "").strip(),
        "coversSystemIds": _split_list(boss_row.get("covers_system_ids", "")),
        "integratedLearningGoal": boss_row.get("integrated_learning_goal", "").strip(),
        "challengeBrief": boss_row.get("challenge_brief", "").strip(),
        "successEvidence": boss_row.get("success_evidence", "").strip(),
        "failureRouting": boss_row.get("failure_routing", "").strip(),
        "sourceEvidence": boss_row.get("source_evidence", "").strip(),
        "training": boss_training,
    }
    if set(boss["coversSystemIds"]) != {system["id"] for system in systems}:
        raise ValueError("GalaxyBoss must cover every GalaxyPlan system exactly once")

    planet_count = sum(len(system["planets"]) for system in systems)
    return {
        "chapterId": chapter_id,
        "title": title,
        "systems": systems,
        "boss": boss,
        "metrics": {
            "systemCount": len(systems),
            "planetCount": planet_count,
            "bossCount": 1,
        },
    }


def write_javascript_module(asset: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(asset, ensure_ascii=False, indent=2, sort_keys=False)
    output.write_text(f"export default {payload};\n", encoding="utf-8", newline="\n")


def _parse_metadata(markdown: str) -> dict[str, str]:
    metadata: dict[str, str] = {}
    for line in markdown.splitlines():
        if line.startswith("## "):
            break
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line.strip())
        if match:
            metadata[match.group(1)] = match.group(2)
    return metadata


def _parse_tables(markdown: str) -> dict[str, list[dict[str, str]]]:
    lines = markdown.splitlines()
    tables: dict[str, list[dict[str, str]]] = {}
    index = 0
    while index < len(lines):
        heading = re.match(r"^##\s+(.+?)\s*$", lines[index])
        if not heading:
            index += 1
            continue
        section = heading.group(1)
        cursor = index + 1
        while cursor < len(lines) and not lines[cursor].strip():
            cursor += 1
        if cursor >= len(lines) or not lines[cursor].lstrip().startswith("|"):
            index += 1
            continue
        headers = _split_table_row(lines[cursor])
        cursor += 1
        if cursor < len(lines) and _is_separator_row(lines[cursor]):
            cursor += 1
        rows: list[dict[str, str]] = []
        while cursor < len(lines) and lines[cursor].lstrip().startswith("|"):
            values = _split_table_row(lines[cursor])
            values += [""] * max(0, len(headers) - len(values))
            rows.append({header: values[position] for position, header in enumerate(headers)})
            cursor += 1
        tables[section] = rows
        index = cursor
    return tables


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _is_separator_row(line: str) -> bool:
    cells = _split_table_row(line)
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in cells)


def _parse_training_assets(markdown: str) -> dict[str, dict[str, Any]]:
    section = _section_text(markdown, "TrainingAssets", "BossTrainingAsset")
    headings = list(re.finditer(r"(?m)^###\s+([^\n]+)\s*$", section))
    assets: dict[str, dict[str, Any]] = {}
    for position, heading in enumerate(headings):
        node_id = heading.group(1).strip()
        end = headings[position + 1].start() if position + 1 < len(headings) else len(section)
        block = section[heading.end():end]
        core, variant = _split_question_blocks(block)
        meta = _parse_fields(block.split("#### CoreQuestion", 1)[0])
        core_fields = _parse_fields(core)
        variant_fields = _parse_fields(variant)
        assets[node_id] = {
            "goal": meta.get("training_goal", ""),
            "entryTrigger": meta.get("entry_trigger", ""),
            "masteryCriteria": meta.get("mastery_criteria", ""),
            "repairTargetNodeId": meta.get("repair_target_node_id", ""),
            "questionId": core_fields.get("question_id", ""),
            "kind": core_fields.get("question_kind", ""),
            "difficulty": core_fields.get("difficulty", ""),
            "targetDimensions": _split_list(core_fields.get("target_dimensions", "")),
            "stem": core_fields.get("stem", ""),
            "expectedAnswer": core_fields.get("expected_answer", ""),
            "variant": {
                "questionId": variant_fields.get("question_id", ""),
                "relation": variant_fields.get("variant_relation", ""),
                "stem": variant_fields.get("stem", ""),
                "expectedAnswer": variant_fields.get("expected_answer", ""),
                "masteryEvidence": variant_fields.get("mastery_evidence", ""),
            },
        }
    return assets


def _parse_boss_training_asset(markdown: str) -> dict[str, Any]:
    block = _section_text(markdown, "BossTrainingAsset", "DeliveryChecklist")
    fields = _parse_fields(block)
    return {
        "bossId": fields.get("boss_id", ""),
        "kind": fields.get("question_kind", ""),
        "title": fields.get("title", ""),
        "coversSystemIds": _split_list(fields.get("covers_system_ids", "")),
        "coversMicroNodes": _split_list(fields.get("covers_micro_nodes", "")),
        "stem": fields.get("stem", ""),
        "expectedAnswer": fields.get("expected_answer", ""),
        "sourceEvidence": fields.get("source_evidence", ""),
    }


def _section_text(markdown: str, start_heading: str, end_heading: str | None = None) -> str:
    start = re.search(rf"(?m)^##\s+{re.escape(start_heading)}\s*$", markdown)
    if not start:
        raise ValueError(f"missing section: {start_heading}")
    if end_heading:
        end = re.search(rf"(?m)^##\s+{re.escape(end_heading)}\s*$", markdown[start.end():])
        if end:
            return markdown[start.end():start.end() + end.start()]
    return markdown[start.end():]


def _split_question_blocks(block: str) -> tuple[str, str]:
    core_marker = re.search(r"(?m)^#### CoreQuestion\s*$", block)
    variant_marker = re.search(r"(?m)^#### TransferVariant\s*$", block)
    if not core_marker or not variant_marker or variant_marker.start() <= core_marker.end():
        raise ValueError("each TrainingAssets node requires CoreQuestion and TransferVariant")
    return block[core_marker.end():variant_marker.start()], block[variant_marker.end():]


def _parse_fields(block: str) -> dict[str, str]:
    lines = block.splitlines()
    fields: dict[str, str] = {}
    index = 0
    while index < len(lines):
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", lines[index])
        if not match:
            index += 1
            continue
        key, value = match.group(1), match.group(2).strip()
        if value == "|":
            literal: list[str] = []
            index += 1
            while index < len(lines):
                line = lines[index]
                if line.startswith("  "):
                    literal.append(line[2:])
                    index += 1
                    continue
                if not line.strip():
                    literal.append("")
                    index += 1
                    continue
                break
            fields[key] = "\n".join(literal).strip()
            continue
        fields[key] = value
        index += 1
    return fields


def _split_list(value: str) -> list[str]:
    cleaned = value.strip().strip("[]")
    return [item.strip() for item in re.split(r"[,，;；]", cleaned) if item.strip()]


def _integer(value: str | None, fallback: int) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return fallback


def main() -> None:
    parser = argparse.ArgumentParser(description="Build browser galaxy data from structured chapter Markdown.")
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--copy-to", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    markdown = args.source.read_text(encoding="utf-8")
    if args.copy_to:
        args.copy_to.parent.mkdir(parents=True, exist_ok=True)
        args.copy_to.write_text(markdown, encoding="utf-8", newline="\n")
    if args.output:
        asset = build_chapter_asset(markdown)
        write_javascript_module(asset, args.output)
        print(json.dumps(asset["metrics"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
