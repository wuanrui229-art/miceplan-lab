from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from analyze_formal_natural_statistics import mean
from analyze_formal_seeded_statistics import BOOTSTRAP_REPLICATES, interval
from compare_formal_natural_models import bootstrap, load_model_records


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "paper" / "data" / "miceplan_lab_v1_1" / "runs"
OUTPUT = (
    ROOT
    / "paper"
    / "data"
    / "miceplan_lab_v1_1"
    / "formal_cross_model_natural_statistics_3model.json"
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
    "openai_gpt_5_6_sol": (
        RUNS / "formal-natural-openai-v1-2-extension",
        ROOT
        / "paper"
        / "experiments"
        / "miceplan_lab"
        / "PRICING_OPENAI_GPT56_SOL_2026-09-01.json",
    ),
}


def model_effect(
    records: list[dict[str, Any]],
    model: str,
    policy_a: str,
    policy_b: str,
    metric: str,
) -> float:
    return mean(
        [
            row["models"][model][policy_a][metric]
            - row["models"][model][policy_b][metric]
            for row in records
        ]
    )


def main() -> None:
    source = {
        name: load_model_records(run, pricing)
        for name, (run, pricing) in MODELS.items()
    }
    reference_keys = set(source["kimi"])
    for model, rows in source.items():
        if set(rows) != reference_keys:
            raise RuntimeError(f"{model} formal Track N job keys differ")

    records: list[dict[str, Any]] = []
    for key in sorted(reference_keys):
        cluster = source["kimi"][key]["cluster"]
        if any(source[model][key]["cluster"] != cluster for model in MODELS):
            raise RuntimeError(f"Cluster mismatch for {key}")
        records.append(
            {
                "key": list(key),
                "cluster": cluster,
                "models": {
                    model: source[model][key]["policies"] for model in MODELS
                },
            }
        )
    if len(records) != 216:
        raise RuntimeError(f"Expected 216 three-model pairs, observed {len(records)}")

    comparisons = {
        "validate_block_minus_llm_only": (
            "VALIDATE_AND_BLOCK",
            "LLM_ONLY",
            (
                "rule_invalid_exposure",
                "unsafe_exposure",
                "safe_task_success",
                "safe_resolution",
                "over_defer",
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
                "over_defer",
            ),
        ),
        "rule_repair_minus_blind_retry": (
            "VALIDATE_AND_REPAIR",
            "VALIDATE_AND_BLIND_RETRY",
            (
                "unsafe_exposure",
                "safe_task_success",
                "safe_resolution",
                "over_defer",
            ),
        ),
    }
    pairs = (
        ("kimi", "deepseek"),
        ("kimi", "openai_gpt_5_6_sol"),
        ("deepseek", "openai_gpt_5_6_sol"),
    )
    result: dict[str, Any] = {
        "analysis": {
            "paired_jobs": len(records),
            "semantic_task_clusters": len({row["cluster"] for row in records}),
            "bootstrap_replicates": BOOTSTRAP_REPLICATES,
            "models": list(MODELS),
            "pairwise_difference_direction": "second model effect minus first model effect",
        },
        "comparisons": {},
    }
    seed = 20260902
    offset = 0
    for name, (policy_a, policy_b, metrics) in comparisons.items():
        result["comparisons"][name] = {}
        for metric in metrics:
            effects = {
                model: model_effect(records, model, policy_a, policy_b, metric)
                for model in MODELS
            }
            pairwise: dict[str, Any] = {}
            for first, second in pairs:
                def interaction(
                    sample: list[dict[str, Any]],
                    first_model: str = first,
                    second_model: str = second,
                ) -> float:
                    return model_effect(
                        sample, second_model, policy_a, policy_b, metric
                    ) - model_effect(sample, first_model, policy_a, policy_b, metric)

                boot = bootstrap(records, interaction, seed=seed + offset)
                pairwise[f"{second}_minus_{first}"] = {
                    "effect_difference": interaction(records),
                    "cluster_bootstrap_95_ci": interval(boot),
                }
                offset += 1
            result["comparisons"][name][metric] = {
                "model_effects": effects,
                "pairwise_effect_differences": pairwise,
            }

    OUTPUT.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
