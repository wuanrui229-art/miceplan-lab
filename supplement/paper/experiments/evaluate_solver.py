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
from miceplan.solver import DeterministicLayoutSolver, SolveError


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def area_certificate(layout: HallLayout, ir: LayoutEditIR) -> bool:
    requested_area = sum((operation.count or 0) * (operation.width or 0) * (operation.height or 0) for operation in ir.operations if operation.type.value == "ADD_BOOTH")
    polygon_area = abs(sum(layout.boundary[index][0] * layout.boundary[(index + 1) % len(layout.boundary)][1] - layout.boundary[(index + 1) % len(layout.boundary)][0] * layout.boundary[index][1] for index in range(len(layout.boundary)))) / 2
    return requested_area > polygon_area


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    solver_times = [row["solver_ms"] for row in rows]
    validation_times = [row["validation_ms"] for row in rows]
    candidates = [row for row in rows if row["candidate_generated"]]
    return {
        "n": len(rows),
        "outcomes": dict(Counter(row["outcome"] for row in rows)),
        "candidate_generation_rate": len(candidates) / len(rows),
        "validated_feasible_rate_all_requests": sum(row["validated_feasible"] for row in rows) / len(rows),
        "validated_feasible_rate_generated_candidates": sum(row["validated_feasible"] for row in candidates) / len(candidates) if candidates else 0.0,
        "mean_failed_hard_checks_per_candidate": sum(row["failed_hard_checks"] for row in candidates) / len(candidates) if candidates else 0.0,
        "median_solver_ms": statistics.median(solver_times),
        "p95_solver_ms": sorted(solver_times)[max(0, int(len(solver_times) * 0.95) - 1)],
        "median_validation_ms": statistics.median(validation_times),
        "p95_validation_ms": sorted(validation_times)[max(0, int(len(validation_times) * 0.95) - 1)],
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    halls = {row["hall_id"]: HallLayout.from_dict(row) for row in load_jsonl(DATASET / "halls.jsonl")}
    requests = [row for row in load_jsonl(DATASET / "requests.jsonl") if row["split"] == "test"]
    rows: list[dict[str, Any]] = []
    for row in requests:
        ir = LayoutEditIR.from_dict(row["gold_ir"])
        if ir.requires_confirmation:
            continue
        layout = halls[row["hall_id"]]
        candidate = None
        solver_started = time.perf_counter_ns()
        if area_certificate(layout, ir):
            outcome = "infeasible"
            solver_error = "requested booth area exceeds total hall polygon area"
        else:
            try:
                candidate = DeterministicLayoutSolver().solve(layout, ir)
                outcome = "candidate"
                solver_error = None
            except SolveError as exc:
                outcome = "infeasible"
                solver_error = str(exc)
        solver_ms = (time.perf_counter_ns() - solver_started) / 1_000_000
        validation_ms = 0.0
        failed_rules: list[str] = []
        valid = False
        if candidate is not None:
            validation_started = time.perf_counter_ns()
            report = GeometryValidator().validate(layout, candidate, ir)
            validation_ms = (time.perf_counter_ns() - validation_started) / 1_000_000
            valid = report.valid
            failed_rules = [check.rule for check in report.checks if not check.passed]
            outcome = "awaiting_approval" if valid else "blocked"
        rows.append(
            {
                "request_id": row["request_id"],
                "hall_id": row["hall_id"],
                "language": row["language"],
                "category": row["category"],
                "geometry_category": row["hall_geometry_category"],
                "outcome": outcome,
                "expected_outcome": row["expected_pipeline_state"],
                "outcome_matches_reference": outcome == row["expected_pipeline_state"],
                "candidate_generated": candidate is not None,
                "validated_feasible": valid,
                "failed_hard_checks": len(failed_rules),
                "failed_rules": failed_rules,
                "solver_error": solver_error,
                "solver_ms": solver_ms,
                "validation_ms": validation_ms,
            }
        )

    assert all(row["outcome_matches_reference"] for row in rows)
    report = {
        "dataset": "MICEPlan-Eval-v1.1 held-out test split",
        "run_date": "2026-07-16",
        "scope": "Gold executable IR only; clarification cases excluded before solving.",
        "overall": summarize(rows),
        "by_request_category": {category: summarize([row for row in rows if row["category"] == category]) for category in sorted({row["category"] for row in rows})},
        "by_geometry_category": {category: summarize([row for row in rows if row["geometry_category"] == category]) for category in sorted({row["geometry_category"] for row in rows})},
        "failed_rule_counts": dict(Counter(rule for row in rows for rule in row["failed_rules"])),
        "limitations": [
            "Gold IR is template-derived and human review is pending.",
            "The bounded grid solver is evaluated on synthetic normalized halls, not arbitrary CAD files.",
            "Blocked and infeasible requests are valid safety outcomes, not necessarily algorithm failures.",
        ],
    }
    with (OUTPUT / "solver_v1_1_cases.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    (OUTPUT / "solver_v1_1_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
