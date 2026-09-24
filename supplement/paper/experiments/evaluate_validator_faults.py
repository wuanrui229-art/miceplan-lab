from __future__ import annotations

import json
import os
import statistics
import sys
import time
from collections import Counter
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT / "system"
DATASET = ROOT / "data" / os.getenv("MICEPLAN_DATASET_DIR", "miceplan_eval_v1_1")
OUTPUT = ROOT / "experiments" / "results"
sys.path.insert(0, str(SYSTEM_ROOT))

from miceplan.geometry import GeometryValidator
from miceplan.models import Booth, HallLayout


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def mutate(layout: HallLayout, fault: str) -> HallLayout:
    booths = list(layout.booths)
    editable_index = next(index for index, booth in enumerate(booths) if booth.status in {"available", "reserved"})
    editable = booths[editable_index]
    if fault == "overlap":
        target = next(booth for index, booth in enumerate(booths) if index != editable_index)
        booths[editable_index] = replace(editable, x=target.x, y=target.y)
    elif fault == "outside_boundary":
        booths[editable_index] = replace(editable, x=-editable.width - 1)
    elif fault == "protected_intersection":
        area = (layout.fixed_aisles + layout.obstacles + layout.exits)[0]
        min_x = min(point[0] for point in area.polygon)
        min_y = min(point[1] for point in area.polygon)
        booths[editable_index] = replace(editable, x=min_x, y=min_y)
    elif fault == "duplicate_identifier":
        target = next(booth for index, booth in enumerate(booths) if index != editable_index)
        booths[editable_index] = replace(editable, number=target.number)
    elif fault == "protected_object_mutation":
        protected_index = next(index for index, booth in enumerate(booths) if booth.status in {"sold", "locked"})
        protected = booths[protected_index]
        booths[protected_index] = replace(protected, x=protected.x + 0.5)
    else:
        raise ValueError(fault)
    return replace(layout, version=f"fault-{fault}", booths=tuple(booths))


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    validator = GeometryValidator()
    test_halls = [HallLayout.from_dict(row) for row in load_jsonl(DATASET / "halls.jsonl") if row["split"] == "test"]
    fault_rules = {
        "overlap": "no_overlap",
        "outside_boundary": "within_boundary",
        "protected_intersection": "avoid_protected_polygons",
        "duplicate_identifier": "unique_identifiers",
        "protected_object_mutation": "preserve_sold_and_locked",
    }
    rows: list[dict[str, Any]] = []
    for layout in test_halls:
        cases = [("clean", layout)] + [(fault, mutate(layout, fault)) for fault in fault_rules]
        for fault, candidate in cases:
            started = time.perf_counter_ns()
            report = validator.validate(layout, candidate)
            latency_ms = (time.perf_counter_ns() - started) / 1_000_000
            failed_rules = [check.rule for check in report.checks if not check.passed]
            gold_fault = fault != "clean"
            rows.append(
                {
                    "hall_id": layout.hall_id,
                    "geometry_category": next(row["geometry_category"] for row in load_jsonl(DATASET / "halls.jsonl") if row["hall_id"] == layout.hall_id),
                    "fault": fault,
                    "gold_fault": gold_fault,
                    "primary_rule": fault_rules.get(fault),
                    "predicted_fault": not report.valid,
                    "failed_rules": failed_rules,
                    "primary_rule_detected": not gold_fault or fault_rules[fault] in failed_rules,
                    "latency_ms": latency_ms,
                }
            )

    tp = sum(row["gold_fault"] and row["predicted_fault"] for row in rows)
    fp = sum(not row["gold_fault"] and row["predicted_fault"] for row in rows)
    fn = sum(row["gold_fault"] and not row["predicted_fault"] for row in rows)
    tn = sum(not row["gold_fault"] and not row["predicted_fault"] for row in rows)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    fault_rows = [row for row in rows if row["gold_fault"]]
    latencies = [row["latency_ms"] for row in rows]
    report = {
        "dataset": "MICEPlan-Eval-v1.1 test halls",
        "run_date": "2026-07-16",
        "test_halls": len(test_halls),
        "clean_cases": len(test_halls),
        "injected_fault_cases": len(fault_rows),
        "confusion": {"tp": tp, "fp": fp, "fn": fn, "tn": tn},
        "fault_detection_precision": precision,
        "fault_detection_recall": recall,
        "fault_detection_f1": f1,
        "primary_rule_attribution_accuracy": sum(row["primary_rule_detected"] for row in fault_rows) / len(fault_rows),
        "primary_rule_detection_by_fault": {
            fault: sum(row["primary_rule_detected"] for row in fault_rows if row["fault"] == fault) / sum(row["fault"] == fault for row in fault_rows)
            for fault in fault_rules
        },
        "median_latency_ms": statistics.median(latencies),
        "p95_latency_ms": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)],
        "additional_rule_failures": dict(Counter(rule for row in fault_rows for rule in row["failed_rules"] if rule != row["primary_rule"])),
        "limitations": [
            "Faults are controlled synthetic mutations of synthetic hall models.",
            "Perfect detection on these five injectors does not imply coverage of real CAD or regulatory errors.",
            "Rules are configurable software invariants rather than official compliance rules.",
        ],
    }
    with (OUTPUT / "validator_fault_v1_1_cases.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (OUTPUT / "validator_fault_v1_1_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
