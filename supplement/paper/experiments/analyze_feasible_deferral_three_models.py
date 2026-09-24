#!/usr/bin/env python3
"""Analyse executable-job deferral and its cross-model heterogeneity.

This post-review analysis keeps the preregistered strict over-deferral metric
unchanged, but separately reports deferral among jobs whose gold outcome is an
executable VALID_EDIT.  It uses semantic-task-cluster bootstrap intervals.
"""

from __future__ import annotations

import json
import math
import random
from collections import Counter, defaultdict
from pathlib import Path


PAPER_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = PAPER_ROOT / "data" / "miceplan_lab_v1_1"
OUT_PATH = DATA_ROOT / "formal_feasible_deferral_statistics_3model.json"
BOOTSTRAP_REPS = 10_000
BOOTSTRAP_SEED = 20260903

RUNS = {
    "Kimi": "formal-natural-kimi-v1-2",
    "DeepSeek": "formal-natural-deepseek-v1-2",
    "OpenAI": "formal-natural-openai-v1-2-extension",
}


def read_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def payload(row: dict) -> dict:
    return row.get("payload", row)


def job_key(row: dict) -> str:
    return f"{row['request_id']}::{row['replicate_id']}"


def percentile_interval(values: list[float]) -> list[float]:
    ordered = sorted(values)
    lo = ordered[int(0.025 * len(ordered))]
    hi = ordered[min(len(ordered) - 1, math.ceil(0.975 * len(ordered)) - 1)]
    return [lo, hi]


def cluster_bootstrap(records: list[dict], value_key: str, seed: int) -> list[float]:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for row in records:
        grouped[row["semantic_task_id"]].append(row)
    clusters = sorted(grouped)
    rng = random.Random(seed)
    estimates: list[float] = []
    for _ in range(BOOTSTRAP_REPS):
        sampled: list[dict] = []
        for cluster in rng.choices(clusters, k=len(clusters)):
            sampled.extend(grouped[cluster])
        estimates.append(sum(row[value_key] for row in sampled) / len(sampled))
    return percentile_interval(estimates)


def load_shared_inputs() -> tuple[dict[str, dict], dict[str, dict]]:
    requests = {
        row["request_id"]: row
        for row in read_jsonl(DATA_ROOT / "requests.jsonl")
    }
    gold = {
        row["semantic_task_id"]: row
        for row in read_jsonl(DATA_ROOT / "gold.jsonl")
    }
    return requests, gold


def analyse_model(
    model: str,
    run_name: str,
    requests: dict[str, dict],
    gold: dict[str, dict],
) -> tuple[dict, dict[str, dict]]:
    run_dir = DATA_ROOT / "runs" / run_name
    outcomes = [payload(row) for row in read_jsonl(run_dir / "outcomes.jsonl")]
    gates = [payload(row) for row in read_jsonl(run_dir / "gate_events.jsonl")]

    by_policy: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in outcomes:
        if row["policy"] in {"LLM_ONLY", "VALIDATE_AND_BLOCK"}:
            by_policy[row["policy"]][job_key(row)] = row

    common = sorted(set(by_policy["LLM_ONLY"]) & set(by_policy["VALIDATE_AND_BLOCK"]))
    paired: dict[str, dict] = {}
    strict_gold_decomp: Counter[str] = Counter()
    for key in common:
        llm = by_policy["LLM_ONLY"][key]
        block = by_policy["VALIDATE_AND_BLOCK"][key]
        request = requests[llm["request_id"]]
        gold_row = gold[llm["semantic_task_id"]]
        llm_defer = int(llm["final_action"] == "DEFER")
        block_defer = int(block["final_action"] == "DEFER")
        record = {
            "job_key": key,
            "semantic_task_id": request["semantic_task_id"],
            "gold_outcome": gold_row["admissible_final_outcome"],
            "llm_defer": llm_defer,
            "block_defer": block_defer,
            "deferral_change": block_defer - llm_defer,
        }
        paired[key] = record
        if block_defer and not llm_defer:
            strict_gold_decomp[record["gold_outcome"]] += 1

    feasible = [row for row in paired.values() if row["gold_outcome"] == "VALID_EDIT"]
    n = len(feasible)
    llm_count = sum(row["llm_defer"] for row in feasible)
    block_count = sum(row["block_defer"] for row in feasible)
    diff = sum(row["deferral_change"] for row in feasible) / n
    ci = cluster_bootstrap(feasible, "deferral_change", BOOTSTRAP_SEED)

    gate_issue_codes: Counter[str] = Counter()
    unknown_sources: Counter[str] = Counter()
    validator_gold: Counter[str] = Counter()
    for row in gates:
        gate = row.get("event", {}).get("gate", {})
        if row.get("policy") != "VALIDATE_AND_BLOCK" or gate.get("status") != "UNKNOWN":
            continue
        issues = gate.get("issues") or []
        codes = [issue.get("message_code", "unknown") for issue in issues]
        gate_issue_codes.update(codes)
        if "model_requested_clarification" in codes:
            unknown_sources["model_explicit_clarification"] += 1
        else:
            unknown_sources["validator_added_unknown"] += 1
            request = requests[row["request_id"]]
            validator_gold[gold[request["semantic_task_id"]]["admissible_final_outcome"]] += 1

    summary = {
        "run_name": run_name,
        "paired_jobs": len(common),
        "feasible_jobs": n,
        "feasible_semantic_task_clusters": len({r["semantic_task_id"] for r in feasible}),
        "llm_only_deferrals": llm_count,
        "validate_and_block_deferrals": block_count,
        "added_feasible_deferrals": block_count - llm_count,
        "llm_only_rate": llm_count / n,
        "validate_and_block_rate": block_count / n,
        "paired_change": diff,
        "cluster_bootstrap_95_ci": ci,
        "strict_new_deferrals_by_gold_outcome": dict(sorted(strict_gold_decomp.items())),
        "unknown_sources": dict(sorted(unknown_sources.items())),
        "validator_added_unknown_by_gold_outcome": dict(sorted(validator_gold.items())),
        "unknown_gate_issue_codes": dict(sorted(gate_issue_codes.items())),
    }
    return summary, paired


def main() -> None:
    requests, gold = load_shared_inputs()
    models: dict[str, dict] = {}
    paired_by_model: dict[str, dict[str, dict]] = {}
    for model, run_name in RUNS.items():
        models[model], paired_by_model[model] = analyse_model(
            model, run_name, requests, gold
        )

    interactions: dict[str, dict] = {}
    model_names = list(RUNS)
    for left_index, left in enumerate(model_names):
        for right in model_names[left_index + 1 :]:
            keys = sorted(set(paired_by_model[left]) & set(paired_by_model[right]))
            records: list[dict] = []
            for key in keys:
                lrow = paired_by_model[left][key]
                rrow = paired_by_model[right][key]
                if lrow["gold_outcome"] != "VALID_EDIT":
                    continue
                records.append(
                    {
                        "semantic_task_id": lrow["semantic_task_id"],
                        "interaction": rrow["deferral_change"] - lrow["deferral_change"],
                    }
                )
            effect = sum(row["interaction"] for row in records) / len(records)
            interactions[f"{right}_minus_{left}"] = {
                "paired_feasible_jobs": len(records),
                "interaction": effect,
                "cluster_bootstrap_95_ci": cluster_bootstrap(
                    records,
                    "interaction",
                    BOOTSTRAP_SEED + 100 + len(interactions),
                ),
            }

    output = {
        "analysis": "post-review executable-job deferral decomposition",
        "bootstrap_replicates": BOOTSTRAP_REPS,
        "bootstrap_unit": "semantic_task_id",
        "models": models,
        "cross_model_interactions": interactions,
    }
    OUT_PATH.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
