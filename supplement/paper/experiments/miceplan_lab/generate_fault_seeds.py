from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from shapely.geometry import Polygon

from .contracts import IR_SCHEMA
from .execution import load_jsonl
from .oracle import apply_ir, intent_signature_correct


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
OUTPUT = DATA / "fault_seeds_v1_2.jsonl"
GENERATOR_VERSION = "miceplan-lab-intent-preserving-fault-seeds-v1.0"
POSITIONAL_OPERATIONS = {"ADD_BOOTH", "MOVE_BOOTH", "SPLIT_BOOTH", "RESERVE_AISLE"}
RULES = ("BOUNDARY", "OVERLAP", "PROTECTED_POLYGON")


def _primary_operation(gold: dict[str, Any], ir: dict[str, Any]) -> tuple[int, dict[str, Any]] | None:
    for index, operation in enumerate(ir["operations"]):
        if operation["type"] == gold["intended_operation_family"]:
            return index, operation
    return None


def _operation_size(scene: dict[str, Any], operation: dict[str, Any]) -> tuple[float, float] | None:
    width = operation.get("width")
    height = operation.get("height")
    if width is not None and height is not None:
        return float(width), float(height)
    targets = operation.get("target_ids", [])
    if len(targets) != 1:
        return None
    booth = next((item for item in scene["booths"] if item["id"] == targets[0]), None)
    if booth is None:
        return None
    return float(booth["width"]), float(booth["height"])


def _boundary_candidates(scene: dict[str, Any], width: float, height: float) -> Iterable[tuple[float, float]]:
    min_x, min_y, max_x, max_y = Polygon(scene["boundary"]).bounds
    margin = 1.0
    values = [
        (min_x - width - margin, min_y + margin),
        (max_x + margin, min_y + margin),
        (min_x + margin, min_y - height - margin),
        (min_x + margin, max_y + margin),
        (max_x + margin, max_y + margin),
        (min_x - width - margin, max_y + margin),
    ]
    yield from values


def _overlap_candidates(scene: dict[str, Any]) -> Iterable[tuple[float, float]]:
    for booth in scene["booths"]:
        yield float(booth["x"]), float(booth["y"])
        yield float(booth["x"]) + 0.25, float(booth["y"]) + 0.25


def _protected_candidates(scene: dict[str, Any]) -> Iterable[tuple[float, float]]:
    protected = scene.get("obstacles", []) + scene.get("fixed_aisles", []) + scene.get("exits", [])
    for item in protected:
        min_x, min_y, max_x, max_y = Polygon(item["polygon"]).bounds
        yield min_x, min_y
        yield (min_x + max_x) / 2, (min_y + max_y) / 2


def _candidate_positions(
    rule_id: str, scene: dict[str, Any], width: float, height: float
) -> Iterable[tuple[float, float]]:
    if rule_id == "BOUNDARY":
        yield from _boundary_candidates(scene, width, height)
    elif rule_id == "OVERLAP":
        yield from _overlap_candidates(scene)
    elif rule_id == "PROTECTED_POLYGON":
        yield from _protected_candidates(scene)
    else:
        raise ValueError(rule_id)


def make_fault_seed(
    scene: dict[str, Any], gold: dict[str, Any], rule_id: str
) -> dict[str, Any] | None:
    witness = gold.get("valid_witness_ir")
    if witness is None or gold["admissible_final_outcome"] != "VALID_EDIT":
        return None
    if gold["intent_requirements"].get("required_anchor") is not None:
        return None
    primary_value = _primary_operation(gold, witness)
    if primary_value is None:
        return None
    operation_index, primary = primary_value
    if primary["type"] not in POSITIONAL_OPERATIONS:
        return None
    size = _operation_size(scene, primary)
    if size is None:
        return None
    width, height = size
    for x, y in _candidate_positions(rule_id, scene, width, height):
        candidate = copy.deepcopy(witness)
        candidate["request_id"] = f"{gold['semantic_task_id']}-{rule_id.lower()}-seed"
        candidate["operations"][operation_index]["x"] = round(float(x), 3)
        candidate["operations"][operation_index]["y"] = round(float(y), 3)
        Draft202012Validator(IR_SCHEMA).validate(candidate)
        if not intent_signature_correct(scene, gold, candidate):
            continue
        result = apply_ir(scene, candidate)
        if result.status != "FAIL" or tuple(result.rule_ids) != (rule_id,):
            continue
        return {
            "seed_id": f"seed-{gold['semantic_task_id']}-{rule_id.lower()}",
            "semantic_task_id": gold["semantic_task_id"],
            "scene_id": gold["scene_id"],
            "split": scene["split"],
            "operation_family": gold["intended_operation_family"],
            "complexity": gold["complexity"],
            "rule_id": rule_id,
            "ir": candidate,
            "intent_signature_preserved": True,
            "oracle_status": result.status,
            "oracle_rule_ids": list(result.rule_ids),
            "generator_version": GENERATOR_VERSION,
            "source": "coordinate_mutation_of_machine_audited_valid_witness",
        }
    return None


def generate() -> list[dict[str, Any]]:
    scenes = {row["scene_id"]: row for row in load_jsonl(DATA / "scenes.jsonl")}
    seeds: list[dict[str, Any]] = []
    for gold in load_jsonl(DATA / "gold.jsonl"):
        scene = scenes[gold["scene_id"]]
        for rule_id in RULES:
            seed = make_fault_seed(scene, gold, rule_id)
            if seed is not None:
                seeds.append(seed)
    seeds.sort(key=lambda row: (row["split"], row["semantic_task_id"], row["rule_id"]))
    return seeds


def audit(seeds: list[dict[str, Any]]) -> dict[str, Any]:
    scenes = {row["scene_id"]: row for row in load_jsonl(DATA / "scenes.jsonl")}
    gold = {row["semantic_task_id"]: row for row in load_jsonl(DATA / "gold.jsonl")}
    for seed in seeds:
        scene = scenes[seed["scene_id"]]
        item = gold[seed["semantic_task_id"]]
        if not intent_signature_correct(scene, item, seed["ir"]):
            raise AssertionError(f"Intent signature changed: {seed['seed_id']}")
        result = apply_ir(scene, seed["ir"])
        if result.status != "FAIL" or tuple(result.rule_ids) != (seed["rule_id"],):
            raise AssertionError(f"Non-isolated fault: {seed['seed_id']} -> {result.rule_ids}")
    counts: dict[str, Any] = {}
    for split in ("development", "test"):
        rows = [row for row in seeds if row["split"] == split]
        counts[split] = {
            "total": len(rows),
            "by_rule": {
                rule_id: sum(row["rule_id"] == rule_id for row in rows) for rule_id in RULES
            },
            "semantic_tasks": len({row["semantic_task_id"] for row in rows}),
        }
    return counts


def main() -> None:
    seeds = generate()
    counts = audit(seeds)
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in seeds),
        encoding="utf-8",
    )
    report = DATA / "fault_seed_audit_v1_2.json"
    report.write_text(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(counts, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
