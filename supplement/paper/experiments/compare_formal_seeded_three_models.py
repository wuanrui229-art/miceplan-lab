from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from miceplan_lab.journal import AppendOnlyHashChain


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
RUNS = DATA / "runs"
OUTPUT = DATA / "formal_cross_model_seeded_statistics_3model.json"
RULE = "SEEDED_VALIDATE_AND_REPAIR"
BLIND = "SEEDED_VALIDATE_AND_BLIND_RETRY"
BOOTSTRAP_REPLICATES = 10_000
BOOTSTRAP_SEED = 20260902

MODELS = {
    "kimi": "formal-seeded-kimi-v1-2",
    "deepseek": "formal-seeded-deepseek-v1-2",
    "openai_gpt_5_6_sol": "formal-seeded-openai-v1-2-extension",
}
PAIRS = (
    ("kimi", "deepseek"),
    ("kimi", "openai_gpt_5_6_sol"),
    ("deepseek", "openai_gpt_5_6_sol"),
)


def percentile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    index = (len(ordered) - 1) * probability
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return ordered[lower]
    fraction = index - lower
    return ordered[lower] * (1 - fraction) + ordered[upper] * fraction


def interval(values: list[float]) -> list[float]:
    return [percentile(values, 0.025), percentile(values, 0.975)]


def load_model(run_name: str) -> dict[tuple[str, str, int], dict[str, Any]]:
    outcomes = AppendOnlyHashChain(RUNS / run_name / "outcomes.jsonl").payloads
    grouped: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in outcomes:
        key = (row["seed_id"], row["request_id"], int(row["replicate_id"]))
        grouped[key][row["policy"]] = row

    records: dict[tuple[str, str, int], dict[str, Any]] = {}
    for key, policies in grouped.items():
        if RULE not in policies or BLIND not in policies:
            continue
        rule = policies[RULE]
        blind = policies[BLIND]
        records[key] = {
            "cluster": rule["semantic_task_id"],
            "recovery_at_1": int(
                bool(rule["offline_evaluation"]["safe_task_success"])
                and int(rule["semantic_attempts"]) <= 1
            )
            - int(
                bool(blind["offline_evaluation"]["safe_task_success"])
                and int(blind["semantic_attempts"]) <= 1
            ),
            "recovery_at_3": int(
                bool(rule["offline_evaluation"]["safe_task_success"])
            )
            - int(bool(blind["offline_evaluation"]["safe_task_success"])),
        }
    if len(records) != 210:
        raise RuntimeError(f"{run_name}: expected 210 paired cases, observed {len(records)}")
    return records


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def interaction_interval(
    rows: list[dict[str, Any]], first: str, second: str, metric: str, seed: int
) -> list[float]:
    by_cluster: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_cluster[row["cluster"]].append(row)
    clusters = sorted(by_cluster)
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sampled: list[dict[str, Any]] = []
        for cluster in rng.choices(clusters, k=len(clusters)):
            sampled.extend(by_cluster[cluster])
        estimates.append(
            mean(
                [
                    float(row["models"][second][metric])
                    - float(row["models"][first][metric])
                    for row in sampled
                ]
            )
        )
    return interval(estimates)


def main() -> None:
    source = {model: load_model(run) for model, run in MODELS.items()}
    keys = set(source["kimi"])
    if any(set(rows) != keys for rows in source.values()):
        raise RuntimeError("Three seeded schedules do not match exactly")

    records: list[dict[str, Any]] = []
    for key in sorted(keys):
        cluster = source["kimi"][key]["cluster"]
        if any(source[model][key]["cluster"] != cluster for model in MODELS):
            raise RuntimeError(f"Cluster mismatch for {key}")
        records.append(
            {
                "cluster": cluster,
                "models": {
                    model: {
                        metric: source[model][key][metric]
                        for metric in ("recovery_at_1", "recovery_at_3")
                    }
                    for model in MODELS
                },
            }
        )

    result: dict[str, Any] = {
        "analysis": {
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "effect": "rule_feedback_minus_blind_retry",
            "models": list(MODELS),
            "paired_cases": len(records),
            "pairwise_interaction_direction": (
                "second model effect minus first model effect"
            ),
            "unique_semantic_task_clusters": len(
                {row["cluster"] for row in records}
            ),
        },
        "results": {},
    }

    offset = 0
    for metric in ("recovery_at_1", "recovery_at_3"):
        model_effects = {
            model: mean(
                [float(row["models"][model][metric]) for row in records]
            )
            for model in MODELS
        }
        interactions: dict[str, Any] = {}
        for first, second in PAIRS:
            difference = model_effects[second] - model_effects[first]
            interactions[f"{second}_minus_{first}"] = {
                "effect_difference": difference,
                "semantic_task_cluster_bootstrap_95_ci": interaction_interval(
                    records,
                    first,
                    second,
                    metric,
                    BOOTSTRAP_SEED + offset,
                ),
            }
            offset += 1
        result["results"][metric] = {
            "model_effects": model_effects,
            "pairwise_interactions": interactions,
        }

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()

