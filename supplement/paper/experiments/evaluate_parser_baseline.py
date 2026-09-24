from __future__ import annotations

import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT / "system"
DATASET = ROOT / "data" / os.getenv("MICEPLAN_DATASET_DIR", "miceplan_eval_v1_1")
OUTPUT = ROOT / "experiments" / "results"
sys.path.insert(0, str(SYSTEM_ROOT))

from miceplan.geometry import GeometryValidator
from miceplan.models import HallLayout, LayoutEditIR
from miceplan.parser import DeterministicBaselineParser
from miceplan.solver import DeterministicLayoutSolver, SolveError


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def operation_slots(ir: LayoutEditIR) -> set[str]:
    slots: set[str] = set()
    for index, operation in enumerate(ir.operations):
        data = operation.to_dict()
        slots.add(f"op:{index}:type={data['type']}")
        for target in data["target_ids"]:
            slots.add(f"op:{index}:target_id={target}")
        for key in ("count", "width", "height", "x", "y", "region", "booth_type"):
            if data[key] is not None:
                slots.add(f"op:{index}:{key}={data[key]}")
    for reference in ir.unresolved_references:
        slots.add(f"unresolved={reference}")
    return slots


def operations_equal(first: LayoutEditIR, second: LayoutEditIR) -> bool:
    return [operation.to_dict() for operation in first.operations] == [operation.to_dict() for operation in second.operations]


def quick_area_infeasible(layout: HallLayout, ir: LayoutEditIR) -> bool:
    requested_area = sum((operation.count or 0) * (operation.width or 0) * (operation.height or 0) for operation in ir.operations if operation.type.value == "ADD_BOOTH")
    polygon_area = abs(sum(layout.boundary[index][0] * layout.boundary[(index + 1) % len(layout.boundary)][1] - layout.boundary[(index + 1) % len(layout.boundary)][0] * layout.boundary[index][1] for index in range(len(layout.boundary)))) / 2
    return requested_area > polygon_area


def compile_state(layout: HallLayout, ir: LayoutEditIR) -> str:
    if ir.requires_confirmation:
        return "needs_confirmation"
    if quick_area_infeasible(layout, ir):
        return "infeasible"
    try:
        candidate = DeterministicLayoutSolver().solve(layout, ir)
        report = GeometryValidator().validate(layout, candidate, ir)
        return "awaiting_approval" if report.valid else "blocked"
    except SolveError:
        return "infeasible"


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(row["slot_tp"] for row in rows)
    fp = sum(row["slot_fp"] for row in rows)
    fn = sum(row["slot_fn"] for row in rows)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    confirmation_labels = [True, False]
    per_label_f1: list[float] = []
    for label in confirmation_labels:
        label_tp = sum(row["gold_confirmation"] == label and row["pred_confirmation"] == label for row in rows)
        label_fp = sum(row["gold_confirmation"] != label and row["pred_confirmation"] == label for row in rows)
        label_fn = sum(row["gold_confirmation"] == label and row["pred_confirmation"] != label for row in rows)
        label_precision = label_tp / (label_tp + label_fp) if label_tp + label_fp else 0.0
        label_recall = label_tp / (label_tp + label_fn) if label_tp + label_fn else 0.0
        label_f1 = 2 * label_precision * label_recall / (label_precision + label_recall) if label_precision + label_recall else 0.0
        per_label_f1.append(label_f1)
    latencies = [row["latency_ms"] for row in rows]
    return {
        "n": len(rows),
        "schema_valid_rate": sum(row["schema_valid"] for row in rows) / len(rows),
        "operation_exact_match": sum(row["operation_exact"] for row in rows) / len(rows),
        "ir_decision_exact_match": sum(row["ir_decision_exact"] for row in rows) / len(rows),
        "slot_precision": precision,
        "slot_recall": recall,
        "slot_f1": f1,
        "confirmation_accuracy": sum(row["confirmation_correct"] for row in rows) / len(rows),
        "confirmation_macro_f1": sum(per_label_f1) / len(per_label_f1),
        "pipeline_state_accuracy": sum(row["pipeline_state_correct"] for row in rows) / len(rows),
        "hallucinated_reference_rate": sum(row["hallucinated_reference"] for row in rows) / len(rows),
        "median_latency_ms": statistics.median(latencies),
        "p95_latency_ms": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)],
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    halls = {row["hall_id"]: HallLayout.from_dict(row) for row in load_jsonl(DATASET / "halls.jsonl")}
    requests = load_jsonl(DATASET / "requests.jsonl")
    parser = DeterministicBaselineParser()
    result_rows: list[dict[str, Any]] = []
    for row in requests:
        layout = halls[row["hall_id"]]
        gold = LayoutEditIR.from_dict(row["gold_ir"])
        started = time.perf_counter_ns()
        predicted = parser.parse(row["text"], layout)
        latency_ms = (time.perf_counter_ns() - started) / 1_000_000
        predicted = LayoutEditIR.from_dict(predicted.to_dict())
        gold_slots = operation_slots(gold)
        predicted_slots = operation_slots(predicted)
        known_ids = {booth.id for booth in layout.booths}
        predicted_targets = {target for operation in predicted.operations for target in operation.target_ids}
        predicted_state = compile_state(layout, predicted)
        operation_exact = operations_equal(gold, predicted)
        confirmation_correct = gold.requires_confirmation == predicted.requires_confirmation
        result_rows.append(
            {
                "request_id": row["request_id"],
                "split": row["split"],
                "language": row["language"],
                "category": row["category"],
                "schema_valid": True,
                "operation_exact": operation_exact,
                "confirmation_correct": confirmation_correct,
                "ir_decision_exact": operation_exact and confirmation_correct and set(gold.unresolved_references) == set(predicted.unresolved_references),
                "slot_tp": len(gold_slots & predicted_slots),
                "slot_fp": len(predicted_slots - gold_slots),
                "slot_fn": len(gold_slots - predicted_slots),
                "gold_confirmation": gold.requires_confirmation,
                "pred_confirmation": predicted.requires_confirmation,
                "gold_pipeline_state": row["expected_pipeline_state"],
                "pred_pipeline_state": predicted_state,
                "pipeline_state_correct": predicted_state == row["expected_pipeline_state"],
                "hallucinated_reference": bool(predicted_targets - known_ids),
                "latency_ms": latency_ms,
                "prediction": predicted.to_dict(),
            }
        )

    predictions_path = OUTPUT / "deterministic_parser_v1_1_predictions.jsonl"
    with predictions_path.open("w", encoding="utf-8") as handle:
        for row in result_rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    report: dict[str, Any] = {
        "system": "DeterministicBaselineParser",
        "dataset": "MICEPlan-Eval-v1.1",
        "run_date": "2026-07-16",
        "overall": aggregate(result_rows),
        "by_split": {split: aggregate([row for row in result_rows if row["split"] == split]) for split in ("development", "test")},
        "by_language_test": {language: aggregate([row for row in result_rows if row["split"] == "test" and row["language"] == language]) for language in ("zh", "en")},
        "by_category_test": {category: aggregate([row for row in result_rows if row["split"] == "test" and row["category"] == category]) for category in sorted({row["category"] for row in result_rows})},
        "confirmation_confusion_test": dict(Counter(f"gold_{row['gold_confirmation']}_pred_{row['pred_confirmation']}" for row in result_rows if row["split"] == "test")),
        "pipeline_state_confusion_test": dict(Counter(f"gold_{row['gold_pipeline_state']}__pred_{row['pred_pipeline_state']}" for row in result_rows if row["split"] == "test")),
        "limitations": [
            "This is a deterministic pattern baseline, not an LLM result.",
            "Gold annotations are template-derived and human review is pending.",
            "Pipeline-state replay uses the prototype compiler and independent validator on synthetic rules.",
        ],
    }
    (OUTPUT / "deterministic_parser_v1_1_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
