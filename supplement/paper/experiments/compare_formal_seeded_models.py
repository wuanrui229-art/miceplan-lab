from __future__ import annotations

import json
import math
import random
from collections import defaultdict
from pathlib import Path
from typing import Any

from miceplan_lab.journal import AppendOnlyHashChain


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "paper" / "data" / "miceplan_lab_v1_1" / "runs"
OUTPUT = (
    ROOT
    / "paper"
    / "data"
    / "miceplan_lab_v1_1"
    / "formal_cross_model_seeded_statistics.json"
)
RULE = "SEEDED_VALIDATE_AND_REPAIR"
BLIND = "SEEDED_VALIDATE_AND_BLIND_RETRY"
BOOTSTRAP_REPLICATES = 10_000


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
    run = RUNS / run_name
    outcomes = AppendOnlyHashChain(run / "outcomes.jsonl").payloads
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
            "fault_cardinality": int(rule["fault_cardinality"]),
            "rule_at_1": int(
                bool(rule["offline_evaluation"]["safe_task_success"])
                and int(rule["semantic_attempts"]) <= 1
            ),
            "blind_at_1": int(
                bool(blind["offline_evaluation"]["safe_task_success"])
                and int(blind["semantic_attempts"]) <= 1
            ),
            "rule_at_3": int(bool(rule["offline_evaluation"]["safe_task_success"])),
            "blind_at_3": int(bool(blind["offline_evaluation"]["safe_task_success"])),
        }
    if len(records) != 210:
        raise RuntimeError(f"{run_name}: expected 210 paired cases, observed {len(records)}")
    return records


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def bootstrap_interaction(
    rows: list[dict[str, Any]], field: str, seed: int
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
        estimates.append(mean([float(row[field]) for row in sampled]))
    return estimates


def metric_summary(rows: list[dict[str, Any]], suffix: str, seed: int) -> dict[str, Any]:
    kimi_rule = [int(row[f"kimi_rule_at_{suffix}"]) for row in rows]
    kimi_blind = [int(row[f"kimi_blind_at_{suffix}"]) for row in rows]
    deepseek_rule = [int(row[f"deepseek_rule_at_{suffix}"]) for row in rows]
    deepseek_blind = [int(row[f"deepseek_blind_at_{suffix}"]) for row in rows]
    field = f"interaction_at_{suffix}"
    point = mean([float(row[field]) for row in rows])
    boot = bootstrap_interaction(rows, field, seed)
    return {
        "n": len(rows),
        "kimi": {
            "rule_successes": sum(kimi_rule),
            "rule_rate": mean([float(value) for value in kimi_rule]),
            "blind_successes": sum(kimi_blind),
            "blind_rate": mean([float(value) for value in kimi_blind]),
            "paired_risk_difference_rule_minus_blind": mean(
                [float(r - b) for r, b in zip(kimi_rule, kimi_blind)]
            ),
        },
        "deepseek": {
            "rule_successes": sum(deepseek_rule),
            "rule_rate": mean([float(value) for value in deepseek_rule]),
            "blind_successes": sum(deepseek_blind),
            "blind_rate": mean([float(value) for value in deepseek_blind]),
            "paired_risk_difference_rule_minus_blind": mean(
                [float(r - b) for r, b in zip(deepseek_rule, deepseek_blind)]
            ),
        },
        "cross_model_interaction_deepseek_minus_kimi": point,
        "semantic_task_cluster_bootstrap_95_ci": interval(boot),
    }


def main() -> None:
    kimi = load_model("formal-seeded-kimi-v1-2")
    deepseek = load_model("formal-seeded-deepseek-v1-2")
    if set(kimi) != set(deepseek):
        raise RuntimeError("Kimi and DeepSeek seeded schedules do not match exactly")

    rows: list[dict[str, Any]] = []
    for key in sorted(kimi):
        k = kimi[key]
        d = deepseek[key]
        if k["cluster"] != d["cluster"] or k["fault_cardinality"] != d["fault_cardinality"]:
            raise RuntimeError(f"Cross-model case metadata mismatch: {key}")
        row: dict[str, Any] = {
            "key": list(key),
            "cluster": k["cluster"],
            "fault_cardinality": k["fault_cardinality"],
        }
        for suffix in ("1", "3"):
            row[f"kimi_rule_at_{suffix}"] = k[f"rule_at_{suffix}"]
            row[f"kimi_blind_at_{suffix}"] = k[f"blind_at_{suffix}"]
            row[f"deepseek_rule_at_{suffix}"] = d[f"rule_at_{suffix}"]
            row[f"deepseek_blind_at_{suffix}"] = d[f"blind_at_{suffix}"]
            row[f"interaction_at_{suffix}"] = (
                d[f"rule_at_{suffix}"]
                - d[f"blind_at_{suffix}"]
                - k[f"rule_at_{suffix}"]
                + k[f"blind_at_{suffix}"]
            )
        rows.append(row)

    manifest = json.loads(
        (RUNS / "formal-seeded-kimi-v1-2" / "run_manifest.json").read_text(
            encoding="utf-8"
        )
    )
    seed = int(manifest["schedule_seed"])
    result = {
        "analysis": {
            "paired_cases": len(rows),
            "unique_semantic_task_clusters": len({row["cluster"] for row in rows}),
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "bootstrap_seed": seed,
            "interaction_direction": (
                "(DeepSeek rule-minus-blind) minus (Kimi rule-minus-blind)"
            ),
        },
        "recovery_at_1": metric_summary(rows, "1", seed + 401),
        "recovery_at_3": metric_summary(rows, "3", seed + 403),
    }
    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
