from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

from evaluate_kimi_parser import DATASET, aggregate, load_jsonl


ROOT = Path(__file__).resolve().parent
RESULTS = ROOT / "results"
MODES = ("schema", "prompt_only")
METRICS = (
    "schema_valid",
    "operation_exact",
    "ir_decision_exact",
    "confirmation_correct",
    "pipeline_state_correct",
)


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(
        proportion * (1 - proportion) / total + z * z / (4 * total * total)
    ) / denominator
    return [centre - margin, centre + margin]


def exact_mcnemar(schema_only: int, prompt_only: int) -> float:
    discordant = schema_only + prompt_only
    if discordant == 0:
        return 1.0
    lower = min(schema_only, prompt_only)
    tail = sum(math.comb(discordant, k) for k in range(lower + 1)) / (2 ** discordant)
    return min(1.0, 2 * tail)


def canonical_rows(mode: str, expected_ids: set[str]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw_path = RESULTS / f"kimi_{mode}_test_v0_3_predictions.jsonl"
    raw_rows = load_jsonl(raw_path)
    first_by_id: dict[str, dict[str, Any]] = {}
    counts: Counter[str] = Counter()
    for row in raw_rows:
        request_id = row["request_id"]
        counts[request_id] += 1
        first_by_id.setdefault(request_id, row)

    actual_ids = set(first_by_id)
    if actual_ids != expected_ids:
        raise RuntimeError(
            f"{mode} IDs differ from the held-out split: "
            f"missing={sorted(expected_ids - actual_ids)}, extra={sorted(actual_ids - expected_ids)}"
        )
    ordered = [first_by_id[request_id] for request_id in sorted(expected_ids)]
    if any(row["split"] != "test" for row in ordered):
        raise RuntimeError(f"{mode} canonical rows contain a non-test record")

    canonical_path = RESULTS / f"kimi_{mode}_test_v0_3_canonical_predictions.jsonl"
    canonical_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in ordered),
        encoding="utf-8",
    )
    provenance = {
        "raw_file": raw_path.name,
        "raw_valid_json_rows": len(raw_rows),
        "unique_request_ids": len(first_by_id),
        "duplicate_request_ids": {key: value for key, value in sorted(counts.items()) if value > 1},
        "selection_rule": "earliest complete JSON row for each held-out request ID",
        "canonical_file": canonical_path.name,
    }
    return ordered, provenance


def report_for(mode: str, rows: list[dict[str, Any]], provenance: dict[str, Any]) -> dict[str, Any]:
    original = json.loads(
        (RESULTS / f"kimi_{mode}_test_v0_3_report.json").read_text(encoding="utf-8")
    )
    report = {
        key: original[key]
        for key in (
            "system", "mode", "provider", "model", "endpoint", "temperature",
            "dataset", "dataset_manifest_sha256", "split", "scope", "access_date",
            "prompt_version",
        )
    }
    report["canonicalization"] = provenance
    report["overall"] = aggregate(rows)
    report["by_language"] = {
        language: aggregate([row for row in rows if row["language"] == language])
        for language in ("zh", "en")
    }
    report["by_category"] = {
        category: aggregate([row for row in rows if row["category"] == category])
        for category in sorted({row["category"] for row in rows})
    }
    report["error_counts"] = dict(Counter(
        row["error"] or "none" for row in rows
    ))
    path = RESULTS / f"kimi_{mode}_test_v0_3_canonical_report.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def main() -> None:
    requests = load_jsonl(DATASET / "requests.jsonl")
    expected_ids = {row["request_id"] for row in requests if row["split"] == "test"}
    if len(expected_ids) != 128:
        raise RuntimeError(f"Expected 128 held-out IDs, found {len(expected_ids)}")

    rows_by_mode: dict[str, list[dict[str, Any]]] = {}
    provenance: dict[str, Any] = {}
    reports: dict[str, dict[str, Any]] = {}
    for mode in MODES:
        rows, mode_provenance = canonical_rows(mode, expected_ids)
        rows_by_mode[mode] = rows
        provenance[mode] = mode_provenance
        reports[mode] = report_for(mode, rows, mode_provenance)

    indexed = {
        mode: {row["request_id"]: row for row in rows}
        for mode, rows in rows_by_mode.items()
    }
    paired: dict[str, Any] = {}
    for metric in METRICS:
        schema_success = sum(row[metric] for row in rows_by_mode["schema"])
        prompt_success = sum(row[metric] for row in rows_by_mode["prompt_only"])
        schema_only = sum(
            indexed["schema"][request_id][metric]
            and not indexed["prompt_only"][request_id][metric]
            for request_id in sorted(expected_ids)
        )
        prompt_only = sum(
            not indexed["schema"][request_id][metric]
            and indexed["prompt_only"][request_id][metric]
            for request_id in sorted(expected_ids)
        )
        paired[metric] = {
            "schema_successes": schema_success,
            "schema_rate": schema_success / 128,
            "schema_wilson_95_ci": wilson_interval(schema_success, 128),
            "prompt_only_successes": prompt_success,
            "prompt_only_rate": prompt_success / 128,
            "prompt_only_wilson_95_ci": wilson_interval(prompt_success, 128),
            "absolute_difference": (schema_success - prompt_success) / 128,
            "discordant_schema_only": schema_only,
            "discordant_prompt_only": prompt_only,
            "exact_mcnemar_two_sided_p": exact_mcnemar(schema_only, prompt_only),
        }

    category_comparison: dict[str, Any] = {}
    categories = sorted({row["category"] for row in rows_by_mode["schema"]})
    for category in categories:
        category_comparison[category] = {}
        for mode in MODES:
            subset = [row for row in rows_by_mode[mode] if row["category"] == category]
            category_comparison[category][mode] = {
                "n": len(subset),
                "schema_valid_rate": sum(row["schema_valid"] for row in subset) / len(subset),
                "ir_decision_exact_match": sum(row["ir_decision_exact"] for row in subset) / len(subset),
                "pipeline_state_accuracy": sum(row["pipeline_state_correct"] for row in subset) / len(subset),
            }

    rates = {"cache_miss_input": 0.95, "cache_hit_input": 0.19, "output": 4.00}
    estimated_cost: dict[str, float] = {}
    for mode in MODES:
        usage = reports[mode]["overall"]["usage"]
        cached = usage["cached_tokens"]
        uncached = max(0, usage["prompt_tokens"] - cached)
        estimated_cost[mode] = (
            uncached * rates["cache_miss_input"]
            + cached * rates["cache_hit_input"]
            + usage["completion_tokens"] * rates["output"]
        ) / 1_000_000

    comparison = {
        "analysis_version": "formal-comparison-v1",
        "canonicalization": provenance,
        "paired_binary_metrics": paired,
        "slot_f1": {
            mode: reports[mode]["overall"]["slot_f1"] for mode in MODES
        },
        "latency_ms": {
            mode: {
                "median": reports[mode]["overall"]["median_latency_ms"],
                "p95": reports[mode]["overall"]["p95_latency_ms"],
            }
            for mode in MODES
        },
        "usage": {mode: reports[mode]["overall"]["usage"] for mode in MODES},
        "estimated_cost_usd": {
            **estimated_cost,
            "total": sum(estimated_cost.values()),
            "rate_assumptions_per_million_tokens": rates,
        },
        "by_category": category_comparison,
        "failure_ids": {
            mode: {
                "schema_invalid": [row["request_id"] for row in rows_by_mode[mode] if not row["schema_valid"]],
                "ir_decision_mismatch": [row["request_id"] for row in rows_by_mode[mode] if not row["ir_decision_exact"]],
            }
            for mode in MODES
        },
    }
    output_path = RESULTS / "kimi_formal_test_v0_3_comparison.json"
    output_path.write_text(
        json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(comparison, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
