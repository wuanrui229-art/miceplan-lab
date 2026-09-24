from __future__ import annotations

import json
import math
import os
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from miceplan_lab.analyze_seeded_run import compute_cost
from miceplan_lab.journal import AppendOnlyHashChain


ROOT = Path(__file__).resolve().parents[2]
RUN = Path(
    os.environ.get(
        "MICEPLAN_SEEDED_RUN",
        str(
            ROOT
            / "paper"
            / "data"
            / "miceplan_lab_v1_1"
            / "runs"
            / "formal-seeded-kimi-v1-2"
        ),
    )
)
PRICING_PATH = Path(
    os.environ.get(
        "MICEPLAN_SEEDED_PRICING",
        str(
            ROOT
            / "paper"
            / "experiments"
            / "miceplan_lab"
            / "PRICING_KIMI_K27_HIGHSPEED_2026-07-21.json"
        ),
    )
)
RULE = "SEEDED_VALIDATE_AND_REPAIR"
BLIND = "SEEDED_VALIDATE_AND_BLIND_RETRY"
BLOCK = "SEEDED_VALIDATE_AND_BLOCK"
BOOTSTRAP_REPLICATES = 10_000


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        raise ValueError("Cannot compute a percentile of an empty sample")
    index = (len(ordered) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def interval(values: list[float]) -> list[float]:
    return [percentile(values, 0.025), percentile(values, 0.975)]


def exact_mcnemar(rule_only: int, blind_only: int) -> float | None:
    discordant = rule_only + blind_only
    if discordant == 0:
        return None
    tail = sum(math.comb(discordant, k) for k in range(min(rule_only, blind_only) + 1))
    return min(1.0, 2.0 * tail / (2**discordant))


def average_ranks(values: list[float]) -> tuple[list[float], list[int]]:
    ordered = sorted(enumerate(values), key=lambda item: item[1])
    ranks = [0.0] * len(values)
    tie_sizes: list[int] = []
    position = 0
    while position < len(ordered):
        end = position + 1
        while end < len(ordered) and ordered[end][1] == ordered[position][1]:
            end += 1
        average = ((position + 1) + end) / 2.0
        for original_index, _ in ordered[position:end]:
            ranks[original_index] = average
        tie_sizes.append(end - position)
        position = end
    return ranks, tie_sizes


def wilcoxon_signed_rank_normal(differences: list[float]) -> dict[str, Any]:
    nonzero = [value for value in differences if value != 0]
    if not nonzero:
        return {"n_nonzero": 0, "w_plus": 0.0, "p_two_sided_approx": None}
    ranks, ties = average_ranks([abs(value) for value in nonzero])
    w_plus = sum(rank for rank, value in zip(ranks, nonzero) if value > 0)
    n = len(nonzero)
    mean = n * (n + 1) / 4.0
    variance = n * (n + 1) * (2 * n + 1) / 24.0
    variance -= sum(size**3 - size for size in ties) / 48.0
    if variance <= 0:
        p_value = None
    else:
        correction = 0.5 if w_plus > mean else (-0.5 if w_plus < mean else 0.0)
        z = (w_plus - mean - correction) / math.sqrt(variance)
        p_value = math.erfc(abs(z) / math.sqrt(2.0))
    return {
        "n_nonzero": n,
        "w_plus": w_plus,
        "p_two_sided_approx": p_value,
    }


def call_usage(call: dict[str, Any]) -> dict[str, int]:
    usage = call.get("usage", {})
    return {
        key: int(usage.get(key, 0) or 0)
        for key in ("prompt_tokens", "completion_tokens", "cached_tokens", "total_tokens")
    }


def row_cost(row: dict[str, Any], pricing: dict[str, Any]) -> float:
    aggregate = Counter()
    for call in row["model_calls"]:
        aggregate.update(call_usage(call))
    return compute_cost(dict(aggregate), pricing)


def row_metrics(row: dict[str, Any], pricing: dict[str, Any]) -> dict[str, float]:
    calls = row["model_calls"]
    return {
        "calls": float(len(calls)),
        "latency_ms": sum(float(call["latency_ms"]) for call in calls),
        "tokens": float(sum(call_usage(call)["total_tokens"] for call in calls)),
        "cost_usd": row_cost(row, pricing),
    }


def paired_records(
    outcomes: list[dict[str, Any]], pricing: dict[str, Any]
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in outcomes:
        key = (row["seed_id"], row["request_id"], int(row["replicate_id"]))
        grouped[key][row["policy"]] = row
    records: list[dict[str, Any]] = []
    for key, policies in grouped.items():
        if RULE not in policies or BLIND not in policies:
            continue
        rule = policies[RULE]
        blind = policies[BLIND]
        rule_metrics = row_metrics(rule, pricing)
        blind_metrics = row_metrics(blind, pricing)
        records.append(
            {
                "key": list(key),
                "cluster": rule["semantic_task_id"],
                "fault_cardinality": int(rule["fault_cardinality"]),
                "rule_at_1": float(
                    bool(rule["offline_evaluation"]["safe_task_success"])
                    and int(rule["semantic_attempts"]) <= 1
                ),
                "blind_at_1": float(
                    bool(blind["offline_evaluation"]["safe_task_success"])
                    and int(blind["semantic_attempts"]) <= 1
                ),
                "rule_at_3": float(bool(rule["offline_evaluation"]["safe_task_success"])),
                "blind_at_3": float(bool(blind["offline_evaluation"]["safe_task_success"])),
                **{
                    f"{metric}_difference_rule_minus_blind": (
                        rule_metrics[metric] - blind_metrics[metric]
                    )
                    for metric in ("calls", "latency_ms", "tokens", "cost_usd")
                },
            }
        )
    return records


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def estimate(records: list[dict[str, Any]], field: str) -> float:
    return mean([float(row[field]) for row in records])


def bootstrap(
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
    estimates: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled: list[dict[str, Any]] = []
        for cluster in rng.choices(clusters, k=len(clusters)):
            sampled.extend(by_cluster[cluster])
        estimates.append(metric(sampled))
    return estimates


def paired_binary_summary(
    records: list[dict[str, Any]], rule_field: str, blind_field: str, seed: int
) -> dict[str, Any]:
    rule_values = [int(row[rule_field]) for row in records]
    blind_values = [int(row[blind_field]) for row in records]
    both = sum(rule and blind for rule, blind in zip(rule_values, blind_values))
    rule_only = sum(rule and not blind for rule, blind in zip(rule_values, blind_values))
    blind_only = sum(blind and not rule for rule, blind in zip(rule_values, blind_values))
    neither = len(records) - both - rule_only - blind_only

    def risk_difference(sample: list[dict[str, Any]]) -> float:
        return mean([float(row[rule_field]) - float(row[blind_field]) for row in sample])

    boot = bootstrap(records, risk_difference, seed=seed)
    return {
        "n": len(records),
        "rule_successes": sum(rule_values),
        "rule_rate": mean([float(value) for value in rule_values]),
        "blind_successes": sum(blind_values),
        "blind_rate": mean([float(value) for value in blind_values]),
        "paired_risk_difference_rule_minus_blind": risk_difference(records),
        "cluster_bootstrap_95_ci": interval(boot),
        "both_succeeded": both,
        "rule_only_succeeded": rule_only,
        "blind_only_succeeded": blind_only,
        "neither_succeeded": neither,
        "exact_mcnemar_p_two_sided": exact_mcnemar(rule_only, blind_only),
    }


def continuous_summary(
    records: list[dict[str, Any]], field: str, seed: int
) -> dict[str, Any]:
    differences = [float(row[field]) for row in records]
    boot = bootstrap(records, lambda sample: estimate(sample, field), seed=seed)
    return {
        "n": len(differences),
        "mean_difference_rule_minus_blind": mean(differences),
        "cluster_bootstrap_95_ci": interval(boot),
        "wilcoxon_signed_rank_sensitivity": wilcoxon_signed_rank_normal(differences),
    }


def policy_audit(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    values: dict[str, Any] = {}
    for policy in (BLOCK, RULE, BLIND):
        rows = [row for row in outcomes if row["policy"] == policy]
        values[policy] = {
            "n": len(rows),
            "safe_task_successes": sum(
                bool(row["offline_evaluation"]["safe_task_success"]) for row in rows
            ),
            "invalid_operation_exposures": sum(
                bool(row["offline_evaluation"]["invalid_operation_exposed"]) for row in rows
            ),
            "unsafe_candidate_exposures": sum(
                bool(row["offline_evaluation"]["unsafe_candidate_exposed"]) for row in rows
            ),
            "intent_signature_failures": sum(
                not bool(
                    row["offline_evaluation"].get(
                        "intent_signature_correct",
                        row["offline_evaluation"].get("intent_correct", False),
                    )
                )
                for row in rows
            ),
            "blocks": sum(row["final_action"] == "BLOCK" for row in rows),
            "defers": sum(row["final_action"] == "DEFER" for row in rows),
            "exposes": sum(row["final_action"] == "EXPOSE" for row in rows),
        }
    return values


def main() -> None:
    manifest = json.loads((RUN / "run_manifest.json").read_text(encoding="utf-8"))
    pricing = json.loads(PRICING_PATH.read_text(encoding="utf-8"))
    outcomes = AppendOnlyHashChain(RUN / "outcomes.jsonl").payloads
    records = paired_records(outcomes, pricing)
    if len(records) != 210:
        raise RuntimeError(f"Expected 210 paired cases, observed {len(records)}")

    bootstrap_seed = int(manifest["schedule_seed"])
    primary = {
        "recovery_at_1": paired_binary_summary(
            records, "rule_at_1", "blind_at_1", bootstrap_seed
        ),
        "recovery_at_3": paired_binary_summary(
            records, "rule_at_3", "blind_at_3", bootstrap_seed + 1
        ),
    }

    cardinality: dict[str, Any] = {}
    for value in (1, 2):
        subset = [row for row in records if row["fault_cardinality"] == value]
        cardinality[str(value)] = {
            "recovery_at_1": paired_binary_summary(
                subset, "rule_at_1", "blind_at_1", bootstrap_seed + 10 + value
            ),
            "recovery_at_3": paired_binary_summary(
                subset, "rule_at_3", "blind_at_3", bootstrap_seed + 20 + value
            ),
        }

    def interaction(sample: list[dict[str, Any]], suffix: str) -> float:
        single = [row for row in sample if row["fault_cardinality"] == 1]
        double = [row for row in sample if row["fault_cardinality"] == 2]
        single_rd = mean([row[f"rule_at_{suffix}"] - row[f"blind_at_{suffix}"] for row in single])
        double_rd = mean([row[f"rule_at_{suffix}"] - row[f"blind_at_{suffix}"] for row in double])
        return double_rd - single_rd

    interactions: dict[str, Any] = {}
    for suffix, offset in (("1", 31), ("3", 33)):
        point = interaction(records, suffix)
        boot = bootstrap(
            records,
            lambda sample, suffix=suffix: interaction(sample, suffix),
            seed=bootstrap_seed + offset,
        )
        interactions[f"recovery_at_{suffix}"] = {
            "paired_risk_difference_interaction_two_minus_single": point,
            "cluster_bootstrap_95_ci": interval(boot),
        }

    overhead = {
        metric: continuous_summary(
            records,
            f"{metric}_difference_rule_minus_blind",
            bootstrap_seed + 100 + index,
        )
        for index, metric in enumerate(("calls", "latency_ms", "tokens", "cost_usd"))
    }

    result = {
        "run_id": manifest["run_id"],
        "analysis": {
            "cluster_unit": "semantic_task_id",
            "unique_clusters": len({row["cluster"] for row in records}),
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_seed": bootstrap_seed,
            "effect_direction": "rule_feedback_minus_blind_retry",
        },
        "primary_paired_results": primary,
        "fault_cardinality": cardinality,
        "fault_cardinality_interaction": interactions,
        "paired_overhead": overhead,
        "policy_audit": policy_audit(outcomes),
    }
    (RUN / "seeded_statistics.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
