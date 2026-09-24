from __future__ import annotations

import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main() -> None:
    schema_rows = load_jsonl(
        RESULTS / "kimi_schema_test_v0_3_canonical_predictions.jsonl"
    )
    solver_rows = load_jsonl(RESULTS / "solver_v1_1_cases.jsonl")
    solver_report = load_json(RESULTS / "solver_v1_1_report.json")
    comparison = load_json(RESULTS / "kimi_formal_test_v0_3_comparison.json")

    if len(schema_rows) != 128:
        raise RuntimeError(f"Expected 128 schema rows, found {len(schema_rows)}")
    if not all(row["pipeline_state_correct"] for row in schema_rows):
        raise RuntimeError("The frozen schema run does not have perfect routing accuracy")

    routes = Counter(row["pred_pipeline_state"] for row in schema_rows)
    generated = [row for row in solver_rows if row["candidate_generated"]]
    blocked = [row for row in generated if row["outcome"] == "blocked"]
    admitted = [row for row in generated if row["outcome"] == "awaiting_approval"]

    llm_median_ms = comparison["latency_ms"]["schema"]["median"]
    llm_p95_ms = comparison["latency_ms"]["schema"]["p95"]
    validation_median_ms = solver_report["overall"]["median_validation_ms"]
    validation_p95_ms = solver_report["overall"]["p95_validation_ms"]

    report = {
        "analysis_version": "review-gate-v1",
        "dataset": "MICEPlan-Eval-v1.1 held-out test split",
        "schema_pipeline_requests": len(schema_rows),
        "automatic_routing_accuracy": 1.0,
        "routes": dict(sorted(routes.items())),
        "candidate_screening": {
            "generated_candidates": len(generated),
            "invalid_candidates_detected_before_approval": len(blocked),
            "candidates_admitted_to_approval": len(admitted),
            "invalid_candidate_exposure_without_validation": len(blocked) / len(generated),
            "invalid_candidate_exposure_with_validation": 0.0,
            "candidate_screening_load_reduction": len(blocked) / len(generated),
        },
        "pre_approval_diversion": {
            "requests_not_sent_to_final_approval": len(schema_rows) - routes["awaiting_approval"],
            "rate": (len(schema_rows) - routes["awaiting_approval"]) / len(schema_rows),
            "note": "This includes clarification, infeasible, and blocked states; clarification may still require user interaction.",
        },
        "overhead": {
            "schema_llm_median_ms": llm_median_ms,
            "schema_llm_p95_ms": llm_p95_ms,
            "validation_median_ms": validation_median_ms,
            "validation_p95_ms": validation_p95_ms,
            "validation_to_llm_median_ratio": validation_median_ms / llm_median_ms,
            "validation_to_llm_p95_ratio": validation_p95_ms / llm_p95_ms,
        },
        "failed_rule_counts": solver_report["failed_rule_counts"],
        "limitations": [
            "Review burden is represented by invalid-candidate exposure, not measured professional time.",
            "The experiment uses synthetic normalized halls and template-derived gold IR.",
            "The gate prevents known invalid candidates from entering final approval but does not repair them.",
            "No exhibition practitioner has validated the rule set.",
        ],
    }
    output = RESULTS / "review_gate_v1_report.json"
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
