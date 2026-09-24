from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from analyze_formal_seeded_statistics import (
    BOOTSTRAP_REPLICATES,
    exact_mcnemar,
    interval,
    wilcoxon_signed_rank_normal,
)
from miceplan_lab.analyze_development import compute_cost
from miceplan_lab.journal import AppendOnlyHashChain


POLICIES = (
    "LLM_ONLY",
    "CONSTRAINT_IN_PROMPT",
    "VALIDATE_AND_BLOCK",
    "VALIDATE_AND_REPAIR",
    "VALIDATE_AND_BLIND_RETRY",
)
BINARY_METRICS = (
    "rule_invalid_exposure",
    "unsafe_exposure",
    "safe_task_success",
    "safe_resolution",
    "block",
    "defer",
    "over_defer",
    "false_block",
)


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def call_usage(call: dict[str, Any]) -> dict[str, int]:
    usage = call.get("usage", {})
    return {
        key: int(usage.get(key, 0) or 0)
        for key in ("prompt_tokens", "completion_tokens", "cached_tokens", "total_tokens")
    }


def row_metrics(row: dict[str, Any], pricing: dict[str, Any]) -> dict[str, float]:
    evaluation = row["offline_evaluation"]
    calls = row["model_calls"]
    aggregate = Counter()
    for call in calls:
        aggregate.update(call_usage(call))
    oracle_status = evaluation.get("oracle", {}).get("status")
    final_action = row["final_action"]
    return {
        "rule_invalid_exposure": float(
            bool(evaluation.get("rule_invalid_operation_exposed"))
        ),
        "unsafe_exposure": float(bool(evaluation.get("unsafe_candidate_exposed"))),
        "safe_task_success": float(bool(evaluation.get("safe_task_success"))),
        "safe_resolution": float(bool(evaluation.get("safe_resolution"))),
        "block": float(final_action == "BLOCK"),
        "defer": float(final_action == "DEFER"),
        "over_defer": float(
            final_action == "DEFER" and not bool(evaluation.get("correct_defer"))
        ),
        "false_block": float(final_action == "BLOCK" and oracle_status == "PASS"),
        "calls": float(len(calls)),
        "latency_ms": sum(float(call["latency_ms"]) for call in calls),
        "tokens": float(sum(call_usage(call)["total_tokens"] for call in calls)),
        "cost_usd": compute_cost(dict(aggregate), pricing),
    }


def build_records(
    outcomes: list[dict[str, Any]], pricing: dict[str, Any]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in outcomes:
        grouped[(row["request_id"], int(row["replicate_id"]))][row["policy"]] = row
    records: list[dict[str, Any]] = []
    for key, policy_rows in grouped.items():
        if not all(policy in policy_rows for policy in POLICIES):
            continue
        first = policy_rows["LLM_ONLY"]
        records.append(
            {
                "key": list(key),
                "cluster": first["semantic_task_id"],
                "language": first["language"],
                "complexity": first["complexity"],
                "operation_family": first["operation_family"],
                "policies": {
                    policy: row_metrics(policy_rows[policy], pricing) for policy in POLICIES
                },
            }
        )
    return records


def cluster_bootstrap(
    records: list[dict[str, Any]],
    metric: Callable[[list[dict[str, Any]]], float],
    *,
    seed: int,
) -> list[float]:
    by_cluster: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in records:
        by_cluster[row["cluster"]].append(row)
    clusters = sorted(by_cluster)
    rng = random.Random(seed)
    values: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample: list[dict[str, Any]] = []
        for cluster in rng.choices(clusters, k=len(clusters)):
            sample.extend(by_cluster[cluster])
        values.append(metric(sample))
    return values


def policy_rate(
    records: list[dict[str, Any]], policy: str, metric: str, seed: int
) -> dict[str, Any]:
    point = mean([row["policies"][policy][metric] for row in records])
    boot = cluster_bootstrap(
        records,
        lambda sample: mean([row["policies"][policy][metric] for row in sample]),
        seed=seed,
    )
    return {
        "n": len(records),
        "count": int(sum(row["policies"][policy][metric] for row in records)),
        "rate": point,
        "cluster_bootstrap_95_ci": interval(boot),
    }


def binary_comparison(
    records: list[dict[str, Any]],
    policy_a: str,
    policy_b: str,
    metric: str,
    seed: int,
) -> dict[str, Any]:
    a = [int(row["policies"][policy_a][metric]) for row in records]
    b = [int(row["policies"][policy_b][metric]) for row in records]
    both = sum(x and y for x, y in zip(a, b))
    a_only = sum(x and not y for x, y in zip(a, b))
    b_only = sum(y and not x for x, y in zip(a, b))
    neither = len(records) - both - a_only - b_only

    def difference(sample: list[dict[str, Any]]) -> float:
        return mean(
            [
                row["policies"][policy_a][metric] - row["policies"][policy_b][metric]
                for row in sample
            ]
        )

    boot = cluster_bootstrap(records, difference, seed=seed)
    return {
        "n": len(records),
        "policy_a": policy_a,
        "policy_b": policy_b,
        "metric": metric,
        "policy_a_count": sum(a),
        "policy_a_rate": mean([float(value) for value in a]),
        "policy_b_count": sum(b),
        "policy_b_rate": mean([float(value) for value in b]),
        "paired_difference_a_minus_b": difference(records),
        "cluster_bootstrap_95_ci": interval(boot),
        "both": both,
        "a_only": a_only,
        "b_only": b_only,
        "neither": neither,
        "exact_mcnemar_p_two_sided": exact_mcnemar(a_only, b_only),
    }


def continuous_comparison(
    records: list[dict[str, Any]],
    policy_a: str,
    policy_b: str,
    metric: str,
    seed: int,
) -> dict[str, Any]:
    differences = [
        row["policies"][policy_a][metric] - row["policies"][policy_b][metric]
        for row in records
    ]

    def difference(sample: list[dict[str, Any]]) -> float:
        return mean(
            [
                row["policies"][policy_a][metric] - row["policies"][policy_b][metric]
                for row in sample
            ]
        )

    boot = cluster_bootstrap(records, difference, seed=seed)
    return {
        "n": len(records),
        "policy_a": policy_a,
        "policy_b": policy_b,
        "metric": metric,
        "mean_difference_a_minus_b": mean(differences),
        "cluster_bootstrap_95_ci": interval(boot),
        "wilcoxon_signed_rank_sensitivity": wilcoxon_signed_rank_normal(differences),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Paired statistics for formal natural Track N")
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--pricing", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads(
        (args.run_directory / "run_manifest.json").read_text(encoding="utf-8")
    )
    pricing = json.loads(args.pricing.read_text(encoding="utf-8"))
    outcomes = AppendOnlyHashChain(args.run_directory / "outcomes.jsonl").payloads
    records = build_records(outcomes, pricing)
    expected_jobs = int(manifest["expected"]["jobs"])
    if len(records) != expected_jobs:
        raise RuntimeError(f"Expected {expected_jobs} complete policy sets, observed {len(records)}")

    base_seed = int(manifest["schedule_seed"])
    policy_rates: dict[str, Any] = {}
    seed_offset = 0
    for policy in POLICIES:
        policy_rates[policy] = {}
        for metric in BINARY_METRICS:
            policy_rates[policy][metric] = policy_rate(
                records, policy, metric, base_seed + seed_offset
            )
            seed_offset += 1

    comparisons = {
        "validate_block_minus_llm_only": (
            "VALIDATE_AND_BLOCK",
            "LLM_ONLY",
            (
                "rule_invalid_exposure",
                "unsafe_exposure",
                "safe_task_success",
                "safe_resolution",
                "defer",
                "over_defer",
                "false_block",
            ),
        ),
        "constraint_prompt_minus_llm_only": (
            "CONSTRAINT_IN_PROMPT",
            "LLM_ONLY",
            (
                "rule_invalid_exposure",
                "unsafe_exposure",
                "safe_task_success",
                "safe_resolution",
            ),
        ),
        "rule_repair_minus_blind_retry": (
            "VALIDATE_AND_REPAIR",
            "VALIDATE_AND_BLIND_RETRY",
            (
                "rule_invalid_exposure",
                "unsafe_exposure",
                "safe_task_success",
                "safe_resolution",
                "defer",
                "over_defer",
            ),
        ),
        "rule_repair_minus_block": (
            "VALIDATE_AND_REPAIR",
            "VALIDATE_AND_BLOCK",
            (
                "rule_invalid_exposure",
                "unsafe_exposure",
                "safe_task_success",
                "safe_resolution",
                "defer",
                "over_defer",
            ),
        ),
    }
    paired: dict[str, Any] = {}
    for comparison_index, (name, (policy_a, policy_b, metrics)) in enumerate(
        comparisons.items()
    ):
        paired[name] = {
            metric: binary_comparison(
                records,
                policy_a,
                policy_b,
                metric,
                base_seed + 1000 + comparison_index * 100 + metric_index,
            )
            for metric_index, metric in enumerate(metrics)
        }

    overhead: dict[str, Any] = {}
    for comparison_index, (name, policy_a, policy_b) in enumerate(
        (
            (
                "rule_repair_minus_blind_retry",
                "VALIDATE_AND_REPAIR",
                "VALIDATE_AND_BLIND_RETRY",
            ),
            ("rule_repair_minus_block", "VALIDATE_AND_REPAIR", "VALIDATE_AND_BLOCK"),
        )
    ):
        overhead[name] = {
            metric: continuous_comparison(
                records,
                policy_a,
                policy_b,
                metric,
                base_seed + 2000 + comparison_index * 100 + metric_index,
            )
            for metric_index, metric in enumerate(("calls", "latency_ms", "tokens", "cost_usd"))
        }

    result = {
        "run_id": manifest["run_id"],
        "analysis": {
            "jobs": len(records),
            "unique_semantic_task_clusters": len({row["cluster"] for row in records}),
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_seed_base": base_seed,
        },
        "policy_rates": policy_rates,
        "paired_comparisons": paired,
        "paired_overhead": overhead,
    }
    (args.run_directory / "natural_statistics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
