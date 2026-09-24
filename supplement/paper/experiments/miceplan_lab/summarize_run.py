from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .journal import AppendOnlyHashChain
from .policy_runner import POLICIES


def _mean(values: list[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["policy"]].append(row)
    policies: dict[str, Any] = {}
    for policy in POLICIES:
        items = grouped.get(policy, [])
        n = len(items)
        call_counts = [len(item["model_calls"]) for item in items]
        latencies = [sum(call["latency_ms"] for call in item["model_calls"]) for item in items]
        total_tokens = [
            sum(int(call["usage"].get("total_tokens", 0) or 0) for call in item["model_calls"])
            for item in items
        ]
        invalid_exposures = sum(item["offline_evaluation"]["invalid_operation_exposed"] for item in items)
        safe_successes = sum(item["offline_evaluation"]["safe_task_success"] for item in items)
        policies[policy] = {
            "n": n,
            "invalid_operation_exposure_rate": invalid_exposures / n if n else None,
            "safe_task_success_rate": safe_successes / n if n else None,
            "block_rate": sum(item["final_action"] == "BLOCK" for item in items) / n if n else None,
            "defer_rate": sum(item["final_action"] == "DEFER" for item in items) / n if n else None,
            "mean_semantic_call_count": _mean([float(value) for value in call_counts]),
            "mean_model_latency_ms": _mean(latencies),
            "mean_total_tokens": _mean([float(value) for value in total_tokens]),
        }
    return {"policies": policies, "row_count": len(rows)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Recompute MICEPlan-Lab descriptive metrics from raw outcomes")
    parser.add_argument("run_directory", type=Path)
    args = parser.parse_args()
    chain = AppendOnlyHashChain(args.run_directory / "outcomes.jsonl")
    result = summarize(chain.payloads)
    output = args.run_directory / "summary.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
