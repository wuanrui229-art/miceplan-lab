from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT / "system"
DATASET = ROOT / "data" / os.getenv("MICEPLAN_DATASET_DIR", "miceplan_eval_v1_1")
sys.path.insert(0, str(SYSTEM_ROOT))

from miceplan.geometry import GeometryValidator
from miceplan.models import HallLayout, LayoutEditIR
from miceplan.solver import DeterministicLayoutSolver, SolveError


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def semantic_errors(row: dict, hall: HallLayout) -> list[str]:
    """Check that visible request content and gold IR carry the same semantics."""
    errors: list[str] = []
    text = row["text"]
    ir = LayoutEditIR.from_dict(row["gold_ir"])
    operations = list(ir.operations)
    visible_numbers = set(re.findall(r"\b[A-Z]\d{3}\b", text.upper()))
    id_to_number = {booth.id: booth.number for booth in hall.booths}
    expected_confirmation = row["category"] in {"ambiguous", "contradictory", "protected_object"}
    if ir.requires_confirmation != expected_confirmation:
        errors.append("confirmation_policy")
    detected_language = "zh" if re.search(r"[\u4e00-\u9fff]", text) else "en"
    if detected_language != row["language"] or ir.language != row["language"]:
        errors.append("language")
    for operation in operations:
        for target_id in operation.target_ids:
            if id_to_number.get(target_id) not in visible_numbers:
                errors.append(f"target_not_visible:{target_id}")

    category = row["category"]
    if category == "capacity_stress":
        if len(operations) != 1 or operations[0].type.value != "ADD_BOOTH":
            errors.append("capacity_operation")
        else:
            op = operations[0]
            if (op.count, op.width, op.height, op.booth_type) != (100, 6.0, 6.0, "custom"):
                errors.append("capacity_slots")
            if not re.search(r"100", text) or not re.search(r"6\s*[x×]\s*6", text, re.I):
                errors.append("capacity_text_values")
    elif category == "ambiguous":
        unknowns = set(re.findall(r"\bZ\d{3}\b", text.upper()))
        if len(operations) != 1 or operations[0].type.value != "MOVE_BOOTH":
            errors.append("ambiguous_operation")
        elif operations[0].target_ids or operations[0].region != "north":
            errors.append("ambiguous_slots")
        if set(ir.unresolved_references) != unknowns:
            errors.append("ambiguous_reference")
    elif category == "contradictory":
        if operations:
            errors.append("contradictory_operations_not_empty")
        if set(ir.unresolved_references) != {"contradictory_booth_count"}:
            errors.append("contradictory_reason")
        if not re.search(r"\b4\b", text) or not re.search(r"\b8\b", text):
            errors.append("contradictory_text_values")
    elif category == "protected_object":
        if len(operations) != 1 or operations[0].type.value != "MOVE_BOOTH":
            errors.append("protected_operation")
        else:
            op = operations[0]
            target_number = id_to_number.get(op.target_ids[0]) if len(op.target_ids) == 1 else None
            if op.region != "west" or target_number not in visible_numbers:
                errors.append("protected_slots")
            if set(ir.unresolved_references) != {f"protected:{target_number}"}:
                errors.append("protected_reference")
    elif category == "revision":
        if len(operations) != 1 or operations[0].type.value != "RESIZE_BOOTH":
            errors.append("revision_operation")
        elif (operations[0].width, operations[0].height) != (3.0, 3.0):
            errors.append("revision_dimensions")
    elif category == "compound":
        if [op.type.value for op in operations] != ["REMOVE_BOOTH", "ADD_BOOTH"]:
            errors.append("compound_operations")
        else:
            remove, add = operations
            if len(remove.target_ids) != 1 or id_to_number.get(remove.target_ids[0]) not in visible_numbers:
                errors.append("compound_remove_target")
            if (add.count, add.width, add.height, add.region, add.booth_type) != (2, 3.0, 3.0, "east", "standard"):
                errors.append("compound_add_slots")
    elif category == "simple":
        if len(operations) != 1:
            errors.append("simple_operation_count")
        else:
            op = operations[0]
            expected_by_type = {
                "ADD_BOOTH": (op.count, op.width, op.height, op.region, op.booth_type) == (2, 3.0, 3.0, "south", "standard"),
                "MOVE_BOOTH": len(op.target_ids) == 1 and op.region == "east",
                "RESIZE_BOOTH": len(op.target_ids) == 1 and (op.width, op.height) == (3.0, 3.0),
                "REMOVE_BOOTH": len(op.target_ids) == 1,
                "SPLIT_BOOTH": len(op.target_ids) == 1 and (op.count, op.width, op.height, op.booth_type) == (4, 3.0, 3.0, "standard"),
                "RESERVE_AISLE": (op.width, op.height) == (3.0, 6.0),
            }
            if not expected_by_type.get(op.type.value, False):
                errors.append(f"simple_slots:{op.type.value}")
            if op.type.value == "RESERVE_AISLE":
                coordinate = re.search(r"x\s*=\s*(-?\d+(?:\.\d+)?)\D+?y\s*=\s*(-?\d+(?:\.\d+)?)", text, re.I)
                if not coordinate or (float(coordinate.group(1)), float(coordinate.group(2))) != (op.x, op.y):
                    errors.append("aisle_coordinate_text_gold")
    else:
        errors.append(f"unknown_category:{category}")
    return sorted(set(errors))


def main() -> None:
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    hall_rows = load_jsonl(DATASET / "halls.jsonl")
    request_rows = load_jsonl(DATASET / "requests.jsonl")
    assert len(hall_rows) == manifest["hall_count"] == 40
    assert len(request_rows) == manifest["request_count"] == 160
    assert len({row["hall_id"] for row in hall_rows}) == len(hall_rows)
    assert len({row["request_id"] for row in request_rows}) == len(request_rows)
    assert sha256(DATASET / "halls.jsonl") == manifest["files"]["halls.jsonl"]["sha256"]
    assert sha256(DATASET / "requests.jsonl") == manifest["files"]["requests.jsonl"]["sha256"]

    halls: dict[str, HallLayout] = {}
    validator = GeometryValidator()
    for row in hall_rows:
        layout = HallLayout.from_dict(row)
        report = validator.validate(layout, layout)
        assert report.valid, (layout.hall_id, [check.rule for check in report.checks if not check.passed])
        assert len({booth.id for booth in layout.booths}) == len(layout.booths)
        assert len({booth.number for booth in layout.booths}) == len(layout.booths)
        assert any(booth.status == "sold" for booth in layout.booths)
        assert any(booth.status == "locked" for booth in layout.booths)
        halls[layout.hall_id] = layout

    state_counts: Counter[str] = Counter()
    operation_counts: Counter[str] = Counter()
    language_by_category: dict[str, Counter[str]] = defaultdict(Counter)
    split_by_category: dict[str, Counter[str]] = defaultdict(Counter)
    state_mismatches: list[str] = []
    invalid_references: list[str] = []
    semantic_mismatches: dict[str, list[str]] = {}
    for row in request_rows:
        hall = halls[row["hall_id"]]
        ir = LayoutEditIR.from_dict(row["gold_ir"])
        assert ir.request_id == row["request_id"]
        assert ir.language == row["language"]
        assert row["split"] in {"development", "test"}
        known_ids = {booth.id for booth in hall.booths}
        row_semantic_errors = semantic_errors(row, hall)
        if row_semantic_errors:
            semantic_mismatches[row["request_id"]] = row_semantic_errors
        for operation in ir.operations:
            operation_counts[operation.type.value] += 1
            for target in operation.target_ids:
                if target not in known_ids:
                    invalid_references.append(row["request_id"])
        if ir.requires_confirmation:
            observed = "needs_confirmation"
        elif row["category"] == "capacity_stress":
            requested_area = sum((operation.count or 0) * (operation.width or 0) * (operation.height or 0) for operation in ir.operations)
            polygon_area = abs(sum(hall.boundary[index][0] * hall.boundary[(index + 1) % len(hall.boundary)][1] - hall.boundary[(index + 1) % len(hall.boundary)][0] * hall.boundary[index][1] for index in range(len(hall.boundary)))) / 2
            assert requested_area > polygon_area
            observed = "infeasible"
        else:
            try:
                candidate = DeterministicLayoutSolver().solve(hall, ir)
                report = validator.validate(hall, candidate, ir)
                observed = "awaiting_approval" if report.valid else "blocked"
            except SolveError:
                observed = "infeasible"
        if observed != row["expected_pipeline_state"]:
            state_mismatches.append(row["request_id"])
        state_counts[observed] += 1
        language_by_category[row["category"]][row["language"]] += 1
        split_by_category[row["category"]][row["split"]] += 1

    assert not invalid_references, invalid_references
    assert not state_mismatches, state_mismatches
    assert not semantic_mismatches, semantic_mismatches
    assert set(operation_counts) == {"ADD_BOOTH", "MOVE_BOOTH", "RESIZE_BOOTH", "REMOVE_BOOTH", "SPLIT_BOOTH", "RESERVE_AISLE"}
    assert Counter(row["language"] for row in request_rows) == Counter({"zh": 80, "en": 80})
    assert all(row["manual_review_status"] == "pending" for row in request_rows)

    report = {
        "status": "passed",
        "hall_count": len(hall_rows),
        "request_count": len(request_rows),
        "schema_valid_gold_ir": len(request_rows),
        "geometrically_valid_source_halls": len(hall_rows),
        "state_replay_matches": len(request_rows),
        "machine_semantic_audit": {
            "status": "passed",
            "checked_requests": len(request_rows),
            "passed_requests": len(request_rows) - len(semantic_mismatches),
            "failed_requests": len(semantic_mismatches),
            "checks": [
                "language",
                "operation_family",
                "visible_target_mapping",
                "count_and_dimensions",
                "region",
                "aisle_coordinates",
                "confirmation_policy",
                "unresolved_reference_policy",
            ],
        },
        "state_counts": dict(sorted(state_counts.items())),
        "operation_counts": dict(sorted(operation_counts.items())),
        "language_by_category": {key: dict(sorted(value.items())) for key, value in sorted(language_by_category.items())},
        "split_by_category": {key: dict(sorted(value.items())) for key, value in sorted(split_by_category.items())},
        "manual_review_status": "pending",
    }
    (DATASET / "audit_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
