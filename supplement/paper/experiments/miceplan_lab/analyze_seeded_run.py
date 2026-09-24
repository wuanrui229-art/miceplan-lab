from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .execution import load_jsonl
from .journal import AppendOnlyHashChain


REPAIR_POLICIES = (
    "SEEDED_VALIDATE_AND_REPAIR",
    "SEEDED_VALIDATE_AND_BLIND_RETRY",
)
ALL_POLICIES = ("SEEDED_VALIDATE_AND_BLOCK", *REPAIR_POLICIES)


def _rate(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def _usage_for_call(call: dict[str, Any]) -> dict[str, int]:
    usage = dict(call.get("usage", {}))
    if "cache_write_tokens" not in usage:
        raw_usage = call.get("raw_response", {}).get("usage", {})
        details = raw_usage.get("prompt_tokens_details", {})
        usage["cache_write_tokens"] = int(details.get("cache_write_tokens", 0) or 0)
    return usage


def _sum_usage(
    calls: list[dict[str, Any]], usage_by_call_id: dict[str, dict[str, int]] | None = None
) -> dict[str, int]:
    fields = (
        "prompt_tokens",
        "completion_tokens",
        "cached_tokens",
        "cache_write_tokens",
        "total_tokens",
    )
    return {
        field: sum(
            int(
                (usage_by_call_id or {}).get(call.get("call_id"), _usage_for_call(call)).get(field, 0)
                or 0
            )
            for call in calls
        )
        for field in fields
    }


def compute_cost(usage: dict[str, int], pricing: dict[str, Any]) -> float:
    rates = pricing["prices_per_million_tokens"]
    unit = float(pricing["billing_unit_tokens"])
    prompt = int(usage.get("prompt_tokens", 0) or 0)
    cached = min(prompt, int(usage.get("cached_tokens", 0) or 0))
    cache_written = min(
        prompt - cached,
        int(usage.get("cache_write_tokens", 0) or 0),
    )
    uncached = prompt - cached - cache_written
    output = int(usage.get("completion_tokens", 0) or 0)
    return (
        cached * float(rates["cache_hit_input"])
        + cache_written * float(rates.get("cache_write_input", rates["cache_miss_input"]))
        + uncached * float(rates["cache_miss_input"])
        + output * float(rates["output"])
    ) / unit


def _policy_metrics(
    rows: list[dict[str, Any]],
    pricing: dict[str, Any],
    usage_by_call_id: dict[str, dict[str, int]],
) -> dict[str, Any]:
    calls = [call for row in rows for call in row["model_calls"]]
    usage = _sum_usage(calls, usage_by_call_id)
    successes = sum(bool(row["offline_evaluation"]["safe_task_success"]) for row in rows)
    return {
        "n": len(rows),
        "safe_task_successes": successes,
        "safe_task_success_rate": _rate(successes, len(rows)),
        "final_actions": dict(sorted(Counter(row["final_action"] for row in rows).items())),
        "semantic_attempts": dict(
            sorted(Counter(str(row["semantic_attempts"]) for row in rows).items())
        ),
        "mean_model_calls": statistics.fmean(len(row["model_calls"]) for row in rows)
        if rows
        else None,
        "median_total_latency_ms": _median(
            [sum(float(call["latency_ms"]) for call in row["model_calls"]) for row in rows]
        ),
        "usage": usage,
        "conceptual_policy_cost_usd": compute_cost(usage, pricing),
    }


def _recovery_at_k(rows: list[dict[str, Any]], max_attempts: int) -> dict[str, Any]:
    denominator = len(rows)
    values: dict[str, Any] = {}
    previous = 0
    for attempt in range(1, max_attempts + 1):
        cumulative = sum(
            bool(row["offline_evaluation"]["safe_task_success"])
            and int(row["semantic_attempts"]) <= attempt
            for row in rows
        )
        entered = sum(int(row["semantic_attempts"]) >= attempt for row in rows)
        newly_recovered = cumulative - previous
        values[str(attempt)] = {
            "entered": entered,
            "newly_recovered": newly_recovered,
            "marginal_recovery_rate": _rate(newly_recovered, entered),
            "recovery_at_k": _rate(cumulative, denominator),
        }
        previous = cumulative
    return values


def _paired_comparison(outcomes: list[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[tuple[str, str, int], dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in outcomes:
        grouped[(row["seed_id"], row["request_id"], int(row["replicate_id"]))][
            row["policy"]
        ] = row
    pairs = [values for values in grouped.values() if all(policy in values for policy in REPAIR_POLICIES)]
    rule_only = blind_only = both = neither = 0
    attempt_differences: list[int] = []
    for values in pairs:
        rule = values["SEEDED_VALIDATE_AND_REPAIR"]
        blind = values["SEEDED_VALIDATE_AND_BLIND_RETRY"]
        rule_success = bool(rule["offline_evaluation"]["safe_task_success"])
        blind_success = bool(blind["offline_evaluation"]["safe_task_success"])
        if rule_success and blind_success:
            both += 1
        elif rule_success:
            rule_only += 1
        elif blind_success:
            blind_only += 1
        else:
            neither += 1
        attempt_differences.append(int(rule["semantic_attempts"]) - int(blind["semantic_attempts"]))
    return {
        "paired_cases": len(pairs),
        "both_succeeded": both,
        "rule_feedback_only_succeeded": rule_only,
        "blind_retry_only_succeeded": blind_only,
        "neither_succeeded": neither,
        "median_attempt_difference_rule_minus_blind": _median(
            [float(value) for value in attempt_differences]
        ),
    }


def _seed_rules(row: dict[str, Any]) -> list[str]:
    values = row.get("seed_rule_ids")
    if values:
        return list(values)
    return [row["seed_rule_id"]]


def analyze(run_directory: Path, data_directory: Path, pricing: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads((run_directory / "run_manifest.json").read_text(encoding="utf-8"))
    calls = AppendOnlyHashChain(run_directory / "calls.jsonl").payloads
    gates = AppendOnlyHashChain(run_directory / "gate_events.jsonl").payloads
    outcomes = AppendOnlyHashChain(run_directory / "outcomes.jsonl").payloads
    errors = AppendOnlyHashChain(run_directory / "infrastructure_errors.jsonl").payloads
    request_rows = {row["request_id"]: row for row in load_jsonl(data_directory / "requests.jsonl")}
    seed_file = data_directory / manifest.get("fault_seed_file", "fault_seeds_v1_2.jsonl")
    seed_rows = {row["seed_id"]: row for row in load_jsonl(seed_file)}

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in outcomes:
        grouped[row["policy"]].append(row)

    max_attempts = int(manifest["decoding"]["semantic_repair_limit"])
    model_calls = [row["model_call"] for row in calls]
    usage_by_call_id = {call["call_id"]: _usage_for_call(call) for call in model_calls}
    unique_usage = _sum_usage(model_calls)
    expected_jobs = len(manifest["schedule"])
    initial_seed_audit = {
        "all_initial_candidates_fail": all(
            row["initial_offline_evaluation"]["oracle"]["status"] == "FAIL" for row in outcomes
        ),
        "all_initial_candidates_preserve_intent_signature": all(
            bool(row["initial_offline_evaluation"]["intent_signature_correct"]) for row in outcomes
        ),
        "all_initial_rule_sets_match_declared_seed_rule": all(
            row["initial_offline_evaluation"]["oracle"]["rule_ids"] == _seed_rules(row)
            for row in outcomes
        ),
    }
    feedback_audit = {
        "rule_feedback_calls": sum(row["feedback"] is not None for row in calls),
        "blind_retry_calls": sum(row["feedback"] is None for row in calls),
        "rule_feedback_payloads_match_prompt": all(
            ("rule-evidence repair" in row["prompt"].splitlines()[0].lower())
            == (row["feedback"] is not None)
            for row in calls
        ),
    }
    heldout_requests = sorted(
        request_id
        for request_id in {
            *manifest["scheduled_request_ids"],
            *(row["identity"]["request_id"] for row in calls),
            *(row["request_id"] for row in outcomes),
        }
        if request_rows[request_id]["split"] != "development"
    )
    heldout_seeds = sorted(
        seed_id
        for seed_id in {
            *manifest["scheduled_seed_ids"],
            *(row["seed_id"] for row in outcomes),
        }
        if seed_rows[seed_id]["split"] != "development"
    )
    strata: dict[str, Any] = {}
    for rule in sorted({"+".join(_seed_rules(row)) for row in outcomes}):
        strata[rule] = {}
        for policy in REPAIR_POLICIES:
            rows = [
                row for row in grouped[policy] if "+".join(_seed_rules(row)) == rule
            ]
            successes = sum(bool(row["offline_evaluation"]["safe_task_success"]) for row in rows)
            strata[rule][policy] = {
                "n": len(rows),
                "safe_task_successes": successes,
                "safe_task_success_rate": _rate(successes, len(rows)),
            }

    return {
        "run_id": manifest["run_id"],
        "experiment_track": manifest["experiment_track"],
        "completion": {
            "scheduled_jobs": expected_jobs,
            "expected_policy_outcomes": expected_jobs * len(ALL_POLICIES),
            "recorded_policy_outcomes": len(outcomes),
            "unique_model_calls": len(calls),
            "gate_events": len(gates),
            "infrastructure_error_records": len(errors),
            "heldout_request_ids_observed": heldout_requests,
            "heldout_seed_ids_observed": heldout_seeds,
        },
        "initial_seed_audit": initial_seed_audit,
        "feedback_isolation_audit": feedback_audit,
        "actual_unique_usage": unique_usage,
        "actual_unique_cost_usd": compute_cost(unique_usage, pricing),
        "model_quality": {
            "schema_valid_calls": sum(
                row.get("ir") is not None and row.get("error") is None for row in model_calls
            ),
            "length_truncations": sum(
                row.get("raw_response", {}).get("choices", [{}])[0].get("finish_reason") == "length"
                for row in model_calls
            ),
            "infrastructure_retry_count": sum(
                max(0, int(row.get("infrastructure_attempts", 1)) - 1) for row in model_calls
            ),
        },
        "policies": {
            policy: _policy_metrics(grouped.get(policy, []), pricing, usage_by_call_id)
            for policy in ALL_POLICIES
        },
        "recovery": {
            policy: _recovery_at_k(grouped.get(policy, []), max_attempts)
            for policy in REPAIR_POLICIES
        },
        "paired_rule_vs_blind": _paired_comparison(outcomes),
        "rule_strata": strata,
        "pricing": pricing,
    }


def _format_rate(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def render_markdown(result: dict[str, Any]) -> str:
    completion = result["completion"]
    lines = [
        f"# Seeded Recovery Audit — {result['run_id']}",
        "",
        "## Completion and isolation",
        "",
        f"- Policy outcomes: {completion['recorded_policy_outcomes']}/{completion['expected_policy_outcomes']}",
        f"- Unique repair calls: {completion['unique_model_calls']}",
        f"- Infrastructure error records: {completion['infrastructure_error_records']}",
        f"- Held-out request IDs observed: {completion['heldout_request_ids_observed'] or 'none'}",
        f"- Held-out seed IDs observed: {completion['heldout_seed_ids_observed'] or 'none'}",
        f"- Estimated unique API cost: USD {result['actual_unique_cost_usd']:.4f}",
        "",
        "## Seed and feedback audits",
        "",
        f"- Every initial candidate failed independently: {result['initial_seed_audit']['all_initial_candidates_fail']}",
        f"- Every seed preserved the task intent signature: {result['initial_seed_audit']['all_initial_candidates_preserve_intent_signature']}",
        f"- Every initial rule set matched its declared seed rule: {result['initial_seed_audit']['all_initial_rule_sets_match_declared_seed_rule']}",
        f"- Rule/blind prompt isolation passed: {result['feedback_isolation_audit']['rule_feedback_payloads_match_prompt']}",
        "",
        "## Policy results",
        "",
        "| Policy | n | Safe task success | Median total latency | Mean calls | Cost (USD) |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in ALL_POLICIES:
        item = result["policies"][policy]
        latency = item["median_total_latency_ms"]
        lines.append(
            f"| {policy} | {item['n']} | {_format_rate(item['safe_task_success_rate'])} | "
            f"{('n/a' if latency is None else f'{latency / 1000:.2f} s')} | "
            f"{item['mean_model_calls'] or 0:.2f} | {item['conceptual_policy_cost_usd']:.4f} |"
        )
    pair = result["paired_rule_vs_blind"]
    lines.extend(
        [
            "",
            "## Paired rule-feedback versus blind retry",
            "",
            f"- Paired cases: {pair['paired_cases']}",
            f"- Both succeeded: {pair['both_succeeded']}",
            f"- Rule feedback only succeeded: {pair['rule_feedback_only_succeeded']}",
            f"- Blind retry only succeeded: {pair['blind_retry_only_succeeded']}",
            f"- Neither succeeded: {pair['neither_succeeded']}",
            f"- Median attempt difference (rule minus blind): {pair['median_attempt_difference_rule_minus_blind']}",
            "",
            "## Interpretation boundary",
            "",
            "This development pilot estimates conditional recovery from transparent, "
            "intent-preserving injected failures. It does not estimate how often the LLM naturally "
            "creates those failures, and it must not be pooled with held-out results.",
        ]
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit one MICEPlan-Lab seeded recovery run")
    parser.add_argument("run_directory", type=Path)
    parser.add_argument(
        "--data-directory",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "miceplan_lab_v1_1",
    )
    parser.add_argument(
        "--pricing",
        type=Path,
        default=Path(__file__).with_name("PRICING_KIMI_K27_HIGHSPEED_2026-07-21.json"),
    )
    args = parser.parse_args()
    pricing = json.loads(args.pricing.read_text(encoding="utf-8"))
    result = analyze(args.run_directory, args.data_directory, pricing)
    (args.run_directory / "seeded_analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.run_directory / "seeded_analysis.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result["completion"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
