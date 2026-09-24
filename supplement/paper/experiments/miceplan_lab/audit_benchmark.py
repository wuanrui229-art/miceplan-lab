from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from shapely.geometry import Polygon, box

from . import GENERATOR_VERSION, ORACLE_VERSION, PROTOCOL_VERSION
from .contracts import (
    COMPLEXITIES,
    FAIL_STRESS_CLASSES,
    GOLD_SCHEMA,
    OPERATION_FAMILIES,
    REQUEST_SCHEMA,
    SCENE_SCHEMA,
    STRESS_CLASSES,
    UNKNOWN_STRESS_CLASSES,
)
from .oracle import apply_ir, intent_correct, validate_candidate


ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / "data" / "miceplan_lab_v1_1"

EXPECTED_TEST_STRESS = {
    "FEASIBLE_CONTROL": 18,
    "BOUNDARY": 9,
    "OVERLAP": 9,
    "PROTECTED_POLYGON": 9,
    "LOCKED_MUTATION": 9,
    "AMBIGUOUS_TARGET": 9,
    "MISSING_EVIDENCE": 9,
}

LEAK_OR_VAGUE_PATTERNS = (
    r"没有说明",
    r"没有提供",
    r"当前视图",
    r"靠近同一排",
    r"最靠外侧",
    r"does not identify",
    r"provides no",
    r"no (?:entrance|target|scale|unit).*(?:given|provided)",
    r"close to the other booths",
    r"outermost",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def schema_errors(rows: list[dict[str, Any]], schema: dict[str, Any], label: str) -> list[str]:
    validator = Draft202012Validator(schema)
    failures: list[str] = []
    for index, row in enumerate(rows, start=1):
        for error in sorted(validator.iter_errors(row), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in error.path) or "<root>"
            failures.append(f"{label}[{index}].{location}: {error.message}")
    return failures


def split_for_task(requests_by_task: dict[str, list[dict[str, Any]]], task_id: str) -> str:
    splits = {row["split"] for row in requests_by_task[task_id]}
    if len(splits) != 1:
        raise AssertionError(f"Task crosses splits: {task_id} {splits}")
    return next(iter(splits))


def bilingual_audit(rows: list[dict[str, Any]]) -> list[str]:
    failures: list[str] = []
    by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_task[row["semantic_task_id"]].append(row)
    for task_id, pair in sorted(by_task.items()):
        if {row["language"] for row in pair} != {"zh", "en"} or len(pair) != 2:
            failures.append(f"{task_id}: missing bilingual pair")
            continue
        zh = next(row for row in pair if row["language"] == "zh")
        en = next(row for row in pair if row["language"] == "en")
        fields = ("semantic_task_id", "split", "scene_id", "operation_family", "complexity", "pair_id", "context_mask")
        if any(zh[field] != en[field] for field in fields):
            failures.append(f"{task_id}: bilingual metadata mismatch")
        if not re.search(r"[\u4e00-\u9fff]", zh["text"]):
            failures.append(f"{task_id}: Chinese text has no CJK characters")
        if re.search(r"[\u4e00-\u9fff]", en["text"]):
            failures.append(f"{task_id}: English text contains CJK characters")
    return failures


def spatial_signature(scene: dict[str, Any]) -> tuple[Any, ...]:
    booths = sorted(
        (
            booth["status"],
            booth["type"],
            float(booth["x"]),
            float(booth["y"]),
            float(booth["width"]),
            float(booth["height"]),
        )
        for booth in scene["booths"]
    )
    aisles = sorted(
        tuple((float(point[0]), float(point[1])) for point in aisle["polygon"])
        for aisle in scene["fixed_aisles"]
    )
    return tuple(booths), tuple(aisles)


def request_quality_audit(
    requests_by_task: dict[str, list[dict[str, Any]]],
    gold_rows: list[dict[str, Any]],
    scenes: dict[str, dict[str, Any]],
) -> list[str]:
    failures: list[str] = []
    for gold in gold_rows:
        task_id = gold["semantic_task_id"]
        pair = requests_by_task[task_id]
        for request in pair:
            lowered = request["text"].lower()
            for pattern in LEAK_OR_VAGUE_PATTERNS:
                if re.search(pattern, lowered, flags=re.IGNORECASE):
                    failures.append(f"{request['request_id']}: leaked or vague wording matched {pattern!r}")

        stress = gold["target_stress_class"]
        if stress == "MISSING_EVIDENCE":
            if not all(("网格" in row["text"] if row["language"] == "zh" else "grid" in row["text"].lower()) for row in pair):
                failures.append(f"{task_id}: missing-evidence request is not operation-specific grid language")

        if stress == "AMBIGUOUS_TARGET":
            scene = scenes[gold["scene_id"]]
            if len(scene["exits"]) < 2:
                failures.append(f"{task_id}: ambiguous entrance request has fewer than two entrances")
            if gold["intended_operation_family"] not in {"ADD_BOOTH", "RESERVE_AISLE"}:
                exit_shapes = [Polygon(item["polygon"]) for item in scene["exits"]]
                candidates_by_exit = []
                for exit_shape in exit_shapes:
                    candidates_by_exit.append(
                        [
                            booth["id"]
                            for booth in scene["booths"]
                            if box(
                                booth["x"],
                                booth["y"],
                                booth["x"] + booth["width"],
                                booth["y"] + booth["height"],
                            ).distance(exit_shape)
                            <= 4.0
                        ]
                    )
                if sum(bool(items) for items in candidates_by_exit) < 2:
                    failures.append(f"{task_id}: fewer than two entrances have plausible adjacent booth targets")
    return failures


def create_review_packet(
    path: Path,
    scenes: dict[str, dict[str, Any]],
    requests_by_task: dict[str, list[dict[str, Any]]],
    gold_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# MICEPlan-Lab v1.1 Blinded Surface-Form Review Packet",
        "",
        "This packet contains no model outputs. Review each bilingual task against the",
        "scene, intended operation family, context mask, and hidden witness/probe design.",
        "Mark PASS or record a correction before formal model calls. This is internal",
        "benchmark quality control, not practitioner or domain-expert validation.",
        "",
    ]
    for gold in gold_rows:
        task_id = gold["semantic_task_id"]
        pair = sorted(requests_by_task[task_id], key=lambda row: row["language"], reverse=True)
        scene = scenes[gold["scene_id"]]
        lines.extend(
            [
                f"## {task_id} — {gold['intended_operation_family']} / {gold['complexity']} / {gold['target_stress_class']}",
                "",
                f"- Scene: `{scene['scene_id']}`; booths={len(scene['booths'])}; boundary vertices={len(scene['boundary'])}",
                f"- Admissible outcome: `{gold['admissible_final_outcome']}`",
                f"- Context mask: `{json.dumps(pair[0]['context_mask'], sort_keys=True)}`",
                f"- Chinese: {next(row['text'] for row in pair if row['language'] == 'zh')}",
                f"- English: {next(row['text'] for row in pair if row['language'] == 'en')}",
                f"- Intent requirements: `{json.dumps(gold['intent_requirements'], ensure_ascii=False, sort_keys=True)}`",
                f"- Witness present: `{gold['valid_witness_ir'] is not None}`",
                f"- Probe rules: `{json.dumps((gold['invalid_probe_ir'] or {}).get('expected_rule_ids', []))}`",
                "- Review decision: **PENDING**",
                "- Review notes:",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    manifest_path = DATASET / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes_rows = load_jsonl(DATASET / "scenes.jsonl")
    request_rows = load_jsonl(DATASET / "requests.jsonl")
    gold_rows = load_jsonl(DATASET / "gold.jsonl")

    failures: list[str] = []
    failures.extend(schema_errors(scenes_rows, SCENE_SCHEMA, "scene"))
    failures.extend(schema_errors(request_rows, REQUEST_SCHEMA, "request"))
    failures.extend(schema_errors(gold_rows, GOLD_SCHEMA, "gold"))
    failures.extend(bilingual_audit(request_rows))

    if (len(scenes_rows), len(gold_rows), len(request_rows)) != (8, 90, 180):
        failures.append(f"counts: expected 8/90/180, got {len(scenes_rows)}/{len(gold_rows)}/{len(request_rows)}")

    scenes = {row["scene_id"]: row for row in scenes_rows}
    if len(scenes) != len(scenes_rows):
        failures.append("duplicate scene_id")
    gold_by_task = {row["semantic_task_id"]: row for row in gold_rows}
    if len(gold_by_task) != len(gold_rows):
        failures.append("duplicate semantic_task_id in gold")
    requests_by_task: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in request_rows:
        requests_by_task[row["semantic_task_id"]].append(row)
        if row["scene_id"] not in scenes:
            failures.append(f"{row['request_id']}: unknown scene")
        elif row["split"] != scenes[row["scene_id"]]["split"]:
            failures.append(f"{row['request_id']}: request/scene split mismatch")
    if set(requests_by_task) != set(gold_by_task):
        failures.append("request/gold task ID mismatch")
    failures.extend(request_quality_audit(requests_by_task, gold_rows, scenes))

    scene_split_counts = Counter(row["split"] for row in scenes_rows)
    request_split_counts = Counter(row["split"] for row in request_rows)
    if scene_split_counts != Counter({"development": 2, "test": 6}):
        failures.append(f"scene split counts: {scene_split_counts}")
    if request_split_counts != Counter({"development": 36, "test": 144}):
        failures.append(f"request split counts: {request_split_counts}")

    cell_counts = Counter((gold["intended_operation_family"], gold["complexity"]) for gold in gold_rows)
    expected_cells = {(operation, complexity) for operation in OPERATION_FAMILIES for complexity in COMPLEXITIES}
    if set(cell_counts) != expected_cells or any(count != 5 for count in cell_counts.values()):
        failures.append(f"operation/complexity balance: {dict(cell_counts)}")

    test_stress = Counter(
        gold["target_stress_class"]
        for gold in gold_rows
        if split_for_task(requests_by_task, gold["semantic_task_id"]) == "test"
    )
    if dict(test_stress) != EXPECTED_TEST_STRESS:
        failures.append(f"test stress quota: {dict(test_stress)}")

    source_pass_count = 0
    witness_pass_count = 0
    probe_pass_count = 0
    unknown_task_count = 0
    for scene in scenes_rows:
        result = validate_candidate(scene, scene)
        if result.status == "PASS":
            source_pass_count += 1
        else:
            failures.append(f"{scene['scene_id']}: invalid source {result.rule_ids}")

    for gold in gold_rows:
        task_id = gold["semantic_task_id"]
        scene = scenes[gold["scene_id"]]
        stress = gold["target_stress_class"]
        pair = requests_by_task[task_id]
        mask = pair[0]["context_mask"]
        if stress in UNKNOWN_STRESS_CLASSES:
            unknown_task_count += 1
            if gold["admissible_final_outcome"] != "DEFER" or gold["valid_witness_ir"] is not None or gold["invalid_probe_ir"] is not None:
                failures.append(f"{task_id}: UNKNOWN task carries witness/probe or wrong outcome")
            if stress == "AMBIGUOUS_TARGET" and not mask["hide_disambiguating_labels"]:
                failures.append(f"{task_id}: ambiguous task lacks label mask")
            if stress == "MISSING_EVIDENCE" and not (mask["hide_scale"] and mask["hide_unit"]):
                failures.append(f"{task_id}: missing-evidence task lacks scale/unit mask")
            continue

        if any(mask.values()):
            failures.append(f"{task_id}: non-UNKNOWN task unexpectedly masks context")
        witness = gold["valid_witness_ir"]
        if witness is None:
            failures.append(f"{task_id}: missing valid witness")
            continue
        witness_result = apply_ir(scene, witness)
        if witness_result.status == "PASS" and intent_correct(scene, gold, witness, witness_result):
            witness_pass_count += 1
            if gold["complexity"] == "C3" and spatial_signature(scene) == spatial_signature(witness_result.scene_after):
                failures.append(f"{task_id}: C3 witness has no meaningful spatial change")
        else:
            failures.append(f"{task_id}: witness failed {witness_result.status}/{witness_result.rule_ids}")

        probe_record = gold["invalid_probe_ir"]
        if stress == "FEASIBLE_CONTROL":
            if probe_record is not None:
                failures.append(f"{task_id}: control task unexpectedly has invalid probe")
            continue
        if stress not in FAIL_STRESS_CLASSES:
            failures.append(f"{task_id}: unsupported deterministic stress {stress}")
            continue
        if probe_record is None:
            failures.append(f"{task_id}: missing invalid probe")
            continue
        probe_result = apply_ir(scene, probe_record["ir"])
        expected_rules = tuple(probe_record["expected_rule_ids"])
        if probe_result.status == "FAIL" and probe_result.rule_ids == expected_rules == (stress,):
            probe_pass_count += 1
        else:
            failures.append(f"{task_id}: probe mismatch expected={expected_rules} observed={probe_result.status}/{probe_result.rule_ids}")

    if failures:
        report = {"status": "failed", "failure_count": len(failures), "failures": failures}
        (DATASET / "audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise SystemExit(json.dumps(report, ensure_ascii=False, indent=2))

    for gold in gold_rows:
        gold["machine_audit"] = "PASS"
    write_jsonl(DATASET / "gold.jsonl", gold_rows)

    review_status = {
        "dataset": manifest["dataset"],
        "packet": "AUTHOR_REVIEW_PACKET.md",
        "reviewer_role": "author",
        "reviewed_tasks": 0,
        "passed_tasks": 0,
        "failed_tasks": 0,
        "pending_tasks": len(gold_rows),
        "status": "PENDING",
        "note": "This is not expert annotation. Complete before formal model calls.",
    }
    (DATASET / "review_status.json").write_text(json.dumps(review_status, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    create_review_packet(DATASET / "AUTHOR_REVIEW_PACKET.md", scenes, requests_by_task, gold_rows)

    report = {
        "status": "passed",
        "protocol_version": PROTOCOL_VERSION,
        "scene_count": len(scenes_rows),
        "semantic_task_count": len(gold_rows),
        "request_count": len(request_rows),
        "schema_valid_records": len(scenes_rows) + len(gold_rows) + len(request_rows),
        "source_scenes_oracle_pass": source_pass_count,
        "valid_witnesses_oracle_and_intent_pass": witness_pass_count,
        "invalid_probes_expected_rule_pass": probe_pass_count,
        "unknown_tasks_context_mask_pass": unknown_task_count,
        "operation_complexity_cells": {f"{operation}/{complexity}": cell_counts[(operation, complexity)] for operation in OPERATION_FAMILIES for complexity in COMPLEXITIES},
        "test_stress_strata": dict(sorted(test_stress.items())),
        "bilingual_pairs": len(gold_rows),
        "machine_audit": "PASS",
        "author_review": "PENDING",
    }
    (DATASET / "audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    tracked_paths = [
        DATASET / "scenes.jsonl",
        DATASET / "requests.jsonl",
        DATASET / "gold.jsonl",
        DATASET / "review_status.json",
        DATASET / "AUTHOR_REVIEW_PACKET.md",
        DATASET / "audit_report.json",
        *sorted((DATASET / "schemas").glob("*.json")),
        *sorted((DATASET / "prompts").glob("*.txt")),
    ]
    manifest["protocol_version"] = PROTOCOL_VERSION
    manifest["generator_version"] = GENERATOR_VERSION
    manifest["oracle_version"] = ORACLE_VERSION
    manifest["machine_audit_status"] = "PASS"
    manifest["author_review_status"] = "PENDING"
    manifest["files"] = {
        path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
        for path in tracked_paths
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
