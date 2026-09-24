from __future__ import annotations

import copy
import json
from itertools import product
from pathlib import Path
from typing import Any, Iterable

from jsonschema import Draft202012Validator
from shapely.geometry import Polygon

from .contracts import IR_SCHEMA
from .execution import load_jsonl
from .oracle import apply_ir, intent_signature_correct


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
OUTPUT = DATA / "fault_seeds_composite_v1_2.jsonl"
AUDIT = DATA / "fault_seed_composite_audit_v1_2.json"
GENERATOR_VERSION = "miceplan-lab-intent-preserving-composite-fault-seeds-v1.0"
POSITIONAL_OPERATIONS = {"ADD_BOOTH", "MOVE_BOOTH", "SPLIT_BOOTH", "RESERVE_AISLE"}
RULE_SETS = (
    ("BOUNDARY", "OVERLAP"),
    ("BOUNDARY", "PROTECTED_POLYGON"),
    ("OVERLAP", "PROTECTED_POLYGON"),
    ("BOUNDARY", "OVERLAP", "PROTECTED_POLYGON"),
)


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


def _axis_values(lower: float, upper: float, size: float, objects: list[tuple[float, float]]) -> set[float]:
    values = {
        lower - size - 1.0,
        lower - size / 2.0,
        lower - 0.5,
        lower - 0.25,
        lower,
        lower + 0.25,
        upper - size - 0.25,
        upper - size,
        upper - size + 0.25,
        upper - 0.25,
        upper,
        upper + 0.25,
        upper + 1.0,
    }
    for object_lower, object_upper in objects:
        values.update(
            {
                object_lower - size + 0.25,
                object_lower - 0.25,
                object_lower,
                object_lower + 0.25,
                object_upper - size - 0.25,
                object_upper - size,
                object_upper - size + 0.25,
                object_upper - 0.25,
                object_upper,
                object_upper + 0.25,
            }
        )
    return {round(value, 3) for value in values}


def _candidate_positions(
    scene: dict[str, Any], width: float, height: float, original_x: float, original_y: float
) -> Iterable[tuple[float, float]]:
    min_x, min_y, max_x, max_y = Polygon(scene["boundary"]).bounds
    rectangular = [
        Polygon(item["polygon"]).bounds
        for item in scene.get("obstacles", [])
        + scene.get("fixed_aisles", [])
        + scene.get("exits", [])
    ]
    rectangular.extend(
        (
            float(item["x"]),
            float(item["y"]),
            float(item["x"]) + float(item["width"]),
            float(item["y"]) + float(item["height"]),
        )
        for item in scene["booths"]
    )
    x_values = _axis_values(min_x, max_x, width, [(row[0], row[2]) for row in rectangular])
    y_values = _axis_values(min_y, max_y, height, [(row[1], row[3]) for row in rectangular])
    yield from sorted(
        product(x_values, y_values),
        key=lambda point: (
            (point[0] - original_x) ** 2 + (point[1] - original_y) ** 2,
            point[0],
            point[1],
        ),
    )


def make_composite_seed(
    scene: dict[str, Any], gold: dict[str, Any], rule_ids: tuple[str, ...]
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
    if size is None or primary.get("x") is None or primary.get("y") is None:
        return None
    width, height = size
    for x, y in _candidate_positions(
        scene, width, height, float(primary["x"]), float(primary["y"])
    ):
        candidate = copy.deepcopy(witness)
        candidate["request_id"] = (
            f"{gold['semantic_task_id']}-{'-'.join(value.lower() for value in rule_ids)}-seed"
        )
        candidate["operations"][operation_index]["x"] = x
        candidate["operations"][operation_index]["y"] = y
        Draft202012Validator(IR_SCHEMA).validate(candidate)
        if not intent_signature_correct(scene, gold, candidate):
            continue
        result = apply_ir(scene, candidate)
        if result.status != "FAIL" or tuple(result.rule_ids) != rule_ids:
            continue
        suffix = "+".join(value.lower() for value in rule_ids)
        return {
            "seed_id": f"seed-{gold['semantic_task_id']}-{suffix}",
            "semantic_task_id": gold["semantic_task_id"],
            "scene_id": gold["scene_id"],
            "split": scene["split"],
            "operation_family": gold["intended_operation_family"],
            "complexity": gold["complexity"],
            "rule_ids": list(rule_ids),
            "fault_cardinality": len(rule_ids),
            "ir": candidate,
            "intent_signature_preserved": True,
            "oracle_status": result.status,
            "oracle_rule_ids": list(result.rule_ids),
            "generator_version": GENERATOR_VERSION,
            "source": "coordinate_mutation_of_machine_audited_valid_witness",
        }
    return None


def make_all_composite_seeds(scene: dict[str, Any], gold: dict[str, Any]) -> list[dict[str, Any]]:
    """Find all requested rule sets in one lattice pass for faster deterministic generation."""

    witness = gold.get("valid_witness_ir")
    if witness is None or gold["admissible_final_outcome"] != "VALID_EDIT":
        return []
    if gold["intent_requirements"].get("required_anchor") is not None:
        return []
    primary_value = _primary_operation(gold, witness)
    if primary_value is None:
        return []
    operation_index, primary = primary_value
    if primary["type"] not in POSITIONAL_OPERATIONS:
        return []
    size = _operation_size(scene, primary)
    if size is None or primary.get("x") is None or primary.get("y") is None:
        return []
    width, height = size
    found: dict[tuple[str, ...], dict[str, Any]] = {}
    for x, y in _candidate_positions(
        scene, width, height, float(primary["x"]), float(primary["y"])
    ):
        candidate = copy.deepcopy(witness)
        candidate["operations"][operation_index]["x"] = x
        candidate["operations"][operation_index]["y"] = y
        if not intent_signature_correct(scene, gold, candidate):
            continue
        result = apply_ir(scene, candidate)
        rule_ids = tuple(result.rule_ids)
        if result.status != "FAIL" or rule_ids not in RULE_SETS or rule_ids in found:
            continue
        candidate["request_id"] = (
            f"{gold['semantic_task_id']}-{'-'.join(value.lower() for value in rule_ids)}-seed"
        )
        Draft202012Validator(IR_SCHEMA).validate(candidate)
        suffix = "+".join(value.lower() for value in rule_ids)
        found[rule_ids] = {
            "seed_id": f"seed-{gold['semantic_task_id']}-{suffix}",
            "semantic_task_id": gold["semantic_task_id"],
            "scene_id": gold["scene_id"],
            "split": scene["split"],
            "operation_family": gold["intended_operation_family"],
            "complexity": gold["complexity"],
            "rule_ids": list(rule_ids),
            "fault_cardinality": len(rule_ids),
            "ir": candidate,
            "intent_signature_preserved": True,
            "oracle_status": result.status,
            "oracle_rule_ids": list(result.rule_ids),
            "generator_version": GENERATOR_VERSION,
            "source": "coordinate_mutation_of_machine_audited_valid_witness",
        }
        if len(found) == len(RULE_SETS):
            break
    return [found[rule_ids] for rule_ids in RULE_SETS if rule_ids in found]


def generate() -> list[dict[str, Any]]:
    scenes = {row["scene_id"]: row for row in load_jsonl(DATA / "scenes.jsonl")}
    seeds: list[dict[str, Any]] = []
    for gold in load_jsonl(DATA / "gold.jsonl"):
        scene = scenes[gold["scene_id"]]
        seeds.extend(make_all_composite_seeds(scene, gold))
    seeds.sort(key=lambda row: (row["split"], row["semantic_task_id"], row["rule_ids"]))
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
        if result.status != "FAIL" or list(result.rule_ids) != seed["rule_ids"]:
            raise AssertionError(f"Non-isolated composite fault: {seed['seed_id']}")
    report: dict[str, Any] = {}
    for split in ("development", "test"):
        rows = [row for row in seeds if row["split"] == split]
        report[split] = {
            "total": len(rows),
            "semantic_tasks": len({row["semantic_task_id"] for row in rows}),
            "by_fault_cardinality": {
                str(cardinality): sum(row["fault_cardinality"] == cardinality for row in rows)
                for cardinality in (2, 3)
            },
            "by_rule_set": {
                "+".join(rule_ids): sum(row["rule_ids"] == list(rule_ids) for row in rows)
                for rule_ids in RULE_SETS
            },
        }
    return report


def main() -> None:
    seeds = generate()
    report = audit(seeds)
    OUTPUT.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in seeds),
        encoding="utf-8",
    )
    AUDIT.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
