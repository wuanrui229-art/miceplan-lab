from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

from analyze_formal_natural_statistics import build_records, mean
from analyze_formal_seeded_statistics import BOOTSTRAP_REPLICATES, interval
from miceplan_lab.journal import AppendOnlyHashChain


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "paper" / "data" / "miceplan_lab_v1_1" / "runs"
OUTPUT = (
    ROOT
    / "paper"
    / "data"
    / "miceplan_lab_v1_1"
    / "formal_cross_model_natural_statistics.json"
)
MODELS = {
    "kimi": (
        RUNS / "formal-natural-kimi-v1-2",
        ROOT
        / "paper"
        / "experiments"
        / "miceplan_lab"
        / "PRICING_KIMI_K27_HIGHSPEED_2026-07-21.json",
    ),
    "deepseek": (
        RUNS / "formal-natural-deepseek-v1-2",
        ROOT
        / "paper"
        / "experiments"
        / "miceplan_lab"
        / "PRICING_DEEPSEEK_V4_PRO_2026-07-21.json",
    ),
}


def load_model_records(run: Path, pricing_path: Path) -> dict[tuple[str, int], dict[str, Any]]:
    pricing = json.loads(pricing_path.read_text(encoding="utf-8"))
    outcomes = AppendOnlyHashChain(run / "outcomes.jsonl").payloads
    records = build_records(outcomes, pricing)
    return {(str(row["key"][0]), int(row["key"][1])): row for row in records}


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
    values: list[float] = []
    for _ in range(BOOTSTRAP_REPLICATES):
        sample: list[dict[str, Any]] = []
        for cluster in rng.choices(clusters, k=len(clusters)):
            sample.extend(by_cluster[cluster])
        values.append(metric(sample))
    return values


def main() -> None:
    source = {
        name: load_model_records(run, pricing) for name, (run, pricing) in MODELS.items()
    }
    if set(source["kimi"]) != set(source["deepseek"]):
        raise RuntimeError("Kimi and DeepSeek formal Track N job keys differ")

    records: list[dict[str, Any]] = []
    for key in sorted(source["kimi"]):
        kimi = source["kimi"][key]
        deepseek = source["deepseek"][key]
        if kimi["cluster"] != deepseek["cluster"]:
            raise RuntimeError(f"Cluster mismatch for {key}")
        records.append(
            {
                "key": list(key),
                "cluster": kimi["cluster"],
                "models": {
                    "kimi": kimi["policies"],
                    "deepseek": deepseek["policies"],
                },
            }
        )
    if len(records) != 216:
        raise RuntimeError(f"Expected 216 cross-model pairs, observed {len(records)}")

    comparisons = {
        "validate_block_minus_llm_only": (
            "VALIDATE_AND_BLOCK",
            "LLM_ONLY",
            ("rule_invalid_exposure", "unsafe_exposure", "safe_task_success", "over_defer"),
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
            ("safe_task_success", "safe_resolution", "unsafe_exposure"),
        ),
    }

    def model_effect(
        sample: list[dict[str, Any]], model: str, policy_a: str, policy_b: str, metric: str
    ) -> float:
        return mean(
            [
                row["models"][model][policy_a][metric]
                - row["models"][model][policy_b][metric]
                for row in sample
            ]
        )

    result: dict[str, Any] = {
        "analysis": {
            "paired_jobs": len(records),
            "semantic_task_clusters": len({row["cluster"] for row in records}),
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "difference_direction": "(DeepSeek policy effect) minus (Kimi policy effect)",
        },
        "comparisons": {},
    }
    seed = 20260722
    offset = 0
    for name, (policy_a, policy_b, metrics) in comparisons.items():
        result["comparisons"][name] = {}
        for metric in metrics:
            kimi_effect = model_effect(records, "kimi", policy_a, policy_b, metric)
            deepseek_effect = model_effect(records, "deepseek", policy_a, policy_b, metric)

            def interaction(sample: list[dict[str, Any]]) -> float:
                return model_effect(sample, "deepseek", policy_a, policy_b, metric) - model_effect(
                    sample, "kimi", policy_a, policy_b, metric
                )

            boot = bootstrap(records, interaction, seed=seed + offset)
            result["comparisons"][name][metric] = {
                "kimi_effect": kimi_effect,
                "deepseek_effect": deepseek_effect,
                "cross_model_effect_difference": interaction(records),
                "cluster_bootstrap_95_ci": interval(boot),
            }
            offset += 1

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
