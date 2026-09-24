from __future__ import annotations

import argparse
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from .execution import load_jsonl
from .journal import AppendOnlyHashChain
from .oracle import evaluate_candidate
from .policy_runner import POLICIES


ROLE_BY_PROMPT_MARKER = {
    "generation prompt": "BASE",
    "constraint-in-prompt": "CONSTRAINT",
    "rule-evidence repair": "RULE_REPAIR",
    "matched blind-retry": "BLIND_RETRY",
}


def _safe_rate(numerator: int | float, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _mean(values: list[float]) -> float | None:
    return statistics.fmean(values) if values else None


def classify_call(prompt: str) -> str:
    first_line = prompt.splitlines()[0].lower() if prompt else ""
    for marker, role in ROLE_BY_PROMPT_MARKER.items():
        if marker in first_line:
            return role
    raise ValueError(f"Unrecognized prompt template: {first_line!r}")


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


def _candidate_evaluation(
    call_payload: dict[str, Any], scenes: dict[str, dict[str, Any]], gold: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    request = call_payload["request"]
    ir = call_payload["model_call"].get("ir")
    if ir is None:
        return {
            "oracle_status": "UNKNOWN",
            "oracle_rules": ["SCHEMA"],
            "intent_correct": False,
            "safe_task_success": False,
        }
    evaluation = evaluate_candidate(scenes[request["scene_id"]], gold[request["semantic_task_id"]], ir)
    return {
        "oracle_status": evaluation["oracle"]["status"],
        "oracle_rules": evaluation["oracle"]["rule_ids"],
        "intent_correct": evaluation["intent_correct"],
        "safe_task_success": evaluation["safe_task_success"],
    }


def _build_traces(
    calls: list[dict[str, Any]], scenes: dict[str, dict[str, Any]], gold: dict[str, dict[str, Any]]
) -> dict[tuple[str, int, str], list[dict[str, Any]]]:
    traces: dict[tuple[str, int, str], list[dict[str, Any]]] = defaultdict(list)
    for row in calls:
        identity = row["identity"]
        role = classify_call(row["prompt"])
        item = {
            "semantic_attempt": int(identity["semantic_attempt"]),
            "call_id": row["model_call"]["call_id"],
            "evaluation": _candidate_evaluation(row, scenes, gold),
        }
        traces[(identity["request_id"], int(identity["replicate_id"]), role)].append(item)
    for items in traces.values():
        items.sort(key=lambda item: item["semantic_attempt"])
    return traces


def _trace_for_policy(
    traces: dict[tuple[str, int, str], list[dict[str, Any]]],
    request_id: str,
    replicate_id: int,
    policy: str,
) -> list[dict[str, Any]]:
    base = traces.get((request_id, replicate_id, "BASE"), [])
    if policy == "CONSTRAINT_IN_PROMPT":
        return traces.get((request_id, replicate_id, "CONSTRAINT"), [])
    if policy == "VALIDATE_AND_REPAIR":
        return base + traces.get((request_id, replicate_id, "RULE_REPAIR"), [])
    if policy == "VALIDATE_AND_BLIND_RETRY":
        return base + traces.get((request_id, replicate_id, "BLIND_RETRY"), [])
    return base


def _policy_metrics(
    rows: list[dict[str, Any]],
    pricing: dict[str, Any],
    gold: dict[str, dict[str, Any]],
    usage_by_call_id: dict[str, dict[str, int]],
) -> dict[str, Any]:
    n = len(rows)
    calls = [call for row in rows for call in row["model_calls"]]
    usage = _sum_usage(calls, usage_by_call_id)
    defer_cases = sum(
        gold[row["semantic_task_id"]]["admissible_final_outcome"] == "DEFER" for row in rows
    )
    safe_successes = sum(bool(row["offline_evaluation"]["safe_task_success"]) for row in rows)
    correct_defers = sum(bool(row["offline_evaluation"]["correct_defer"]) for row in rows)
    rule_invalid_exposures = sum(
        bool(row["offline_evaluation"].get("rule_invalid_operation_exposed")) for row in rows
    )
    unsupported_exposures = sum(
        bool(row["offline_evaluation"].get("unsupported_candidate_exposed")) for row in rows
    )
    unsafe_exposures = sum(
        bool(row["offline_evaluation"].get("unsafe_candidate_exposed")) for row in rows
    )
    return {
        "n": n,
        "rule_invalid_operation_exposures": rule_invalid_exposures,
        "rule_invalid_operation_exposure_rate": _safe_rate(rule_invalid_exposures, n),
        "unsupported_candidate_exposures": unsupported_exposures,
        "unsupported_candidate_exposure_rate": _safe_rate(unsupported_exposures, n),
        "unsafe_candidate_exposures": unsafe_exposures,
        "unsafe_candidate_exposure_rate": _safe_rate(unsafe_exposures, n),
        "safe_task_successes": safe_successes,
        "safe_task_success_rate": _safe_rate(safe_successes, n),
        "block_rate": _safe_rate(sum(row["final_action"] == "BLOCK" for row in rows), n),
        "defer_rate": _safe_rate(sum(row["final_action"] == "DEFER" for row in rows), n),
        "genuine_defer_cases": defer_cases,
        "correct_defers": correct_defers,
        "correct_defer_rate": _safe_rate(correct_defers, defer_cases),
        "safe_resolution_rate": _safe_rate(safe_successes + correct_defers, n),
        "mean_semantic_calls": _mean([float(len(row["model_calls"])) for row in rows]),
        "mean_model_latency_ms": _mean(
            [sum(float(call["latency_ms"]) for call in row["model_calls"]) for row in rows]
        ),
        "usage": usage,
        "conceptual_policy_cost_usd": compute_cost(usage, pricing),
    }


def _repair_metrics(
    outcomes: list[dict[str, Any]],
    traces: dict[tuple[str, int, str], list[dict[str, Any]]],
    policy: str,
    max_attempts: int = 3,
) -> dict[str, Any]:
    initial_failures = 0
    recovered_at: dict[int, int] = {attempt: 0 for attempt in range(1, max_attempts + 1)}
    entered_at: dict[int, int] = {attempt: 0 for attempt in range(1, max_attempts + 1)}
    repeated = 0
    rule_regressions = 0
    transitions = 0
    for row in outcomes:
        if row["policy"] != policy:
            continue
        trace = _trace_for_policy(traces, row["request_id"], int(row["replicate_id"]), policy)
        if not trace or trace[0]["evaluation"]["oracle_status"] != "FAIL":
            continue
        initial_failures += 1
        first_recovery: int | None = None
        for item in trace[1:]:
            attempt = int(item["semantic_attempt"])
            if attempt <= max_attempts:
                entered_at[attempt] += 1
                if item["evaluation"]["safe_task_success"] and first_recovery is None:
                    first_recovery = attempt
        if first_recovery is not None:
            recovered_at[first_recovery] += 1
        for previous, current in zip(trace, trace[1:]):
            transitions += 1
            previous_rules = set(previous["evaluation"]["oracle_rules"])
            current_rules = set(current["evaluation"]["oracle_rules"])
            if previous_rules & current_rules:
                repeated += 1
            if current["evaluation"]["oracle_status"] == "FAIL" and current_rules - previous_rules:
                rule_regressions += 1
    cumulative = 0
    recovery: dict[str, Any] = {}
    for attempt in range(1, max_attempts + 1):
        cumulative += recovered_at[attempt]
        recovery[str(attempt)] = {
            "entered": entered_at[attempt],
            "newly_recovered": recovered_at[attempt],
            "marginal_recovery_rate": _safe_rate(recovered_at[attempt], entered_at[attempt]),
            "recovery_at_k": _safe_rate(cumulative, initial_failures),
        }
    return {
        "initial_independent_failures": initial_failures,
        "attempts": recovery,
        "candidate_transitions": transitions,
        "repeated_violation_rate": _safe_rate(repeated, transitions),
        "rule_regression_rate": _safe_rate(rule_regressions, transitions),
    }


def analyze(run_directory: Path, data_directory: Path, pricing: dict[str, Any]) -> dict[str, Any]:
    manifest = json.loads((run_directory / "run_manifest.json").read_text(encoding="utf-8"))
    calls = AppendOnlyHashChain(run_directory / "calls.jsonl").payloads
    gates = AppendOnlyHashChain(run_directory / "gate_events.jsonl").payloads
    outcomes = AppendOnlyHashChain(run_directory / "outcomes.jsonl").payloads
    errors = AppendOnlyHashChain(run_directory / "infrastructure_errors.jsonl").payloads
    requests = {row["request_id"]: row for row in load_jsonl(data_directory / "requests.jsonl")}
    scenes = {row["scene_id"]: row for row in load_jsonl(data_directory / "scenes.jsonl")}
    gold = {row["semantic_task_id"]: row for row in load_jsonl(data_directory / "gold.jsonl")}
    traces = _build_traces(calls, scenes, gold)

    heldout_ids = sorted(
        request_id
        for request_id in set(manifest["scheduled_request_ids"])
        | {row["identity"]["request_id"] for row in calls}
        | {row["request_id"] for row in outcomes}
        if requests[request_id]["split"] != "development"
    )
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in outcomes:
        grouped[row["policy"]].append(row)
    usage_by_call_id = {
        row["model_call"]["call_id"]: _usage_for_call(row["model_call"]) for row in calls
    }
    unique_usage = _sum_usage([row["model_call"] for row in calls])
    finish_reasons = [
        row["model_call"].get("raw_response", {}).get("choices", [{}])[0].get("finish_reason")
        for row in calls
    ]
    return {
        "run_id": manifest["run_id"],
        "completion": {
            "scheduled_requests": len(manifest["scheduled_request_ids"]),
            "expected_policy_outcomes": len(manifest["scheduled_request_ids"])
            * len(manifest["replicate_ids"])
            * len(POLICIES),
            "recorded_policy_outcomes": len(outcomes),
            "unique_model_calls": len(calls),
            "gate_events": len(gates),
            "infrastructure_error_records": len(errors),
            "heldout_request_ids_observed": heldout_ids,
        },
        "model_quality": {
            "schema_valid_calls": sum(
                row["model_call"].get("ir") is not None and row["model_call"].get("error") is None
                for row in calls
            ),
            "length_truncations": sum(reason == "length" for reason in finish_reasons),
            "infrastructure_retry_count": sum(
                max(0, int(row["model_call"].get("infrastructure_attempts", 1)) - 1) for row in calls
            ),
        },
        "actual_unique_usage": unique_usage,
        "actual_unique_cost_usd": compute_cost(unique_usage, pricing),
        "policies": {
            policy: _policy_metrics(
                grouped.get(policy, []), pricing, gold, usage_by_call_id
            )
            for policy in POLICIES
        },
        "repair": {
            policy: _repair_metrics(outcomes, traces, policy)
            for policy in ("VALIDATE_AND_REPAIR", "VALIDATE_AND_BLIND_RETRY")
        },
        "pricing": pricing,
    }


def _format_rate(value: float | None) -> str:
    return "n/a" if value is None else f"{100 * value:.1f}%"


def render_markdown(result: dict[str, Any]) -> str:
    completion = result["completion"]
    lines = [
        f"# Development Audit — {result['run_id']}",
        "",
        "## Completion and isolation",
        "",
        f"- Policy outcomes: {completion['recorded_policy_outcomes']}/{completion['expected_policy_outcomes']}",
        f"- Unique model calls: {completion['unique_model_calls']}",
        f"- Infrastructure error records: {completion['infrastructure_error_records']}",
        f"- Held-out request IDs observed: {completion['heldout_request_ids_observed'] or 'none'}",
        f"- Estimated unique API cost: USD {result['actual_unique_cost_usd']:.4f}",
        "",
        "## Primary development metrics",
        "",
        "| Policy | n | RIOER | UER | STS | SRR | Block | Defer | Mean calls | Cost (USD) |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for policy in POLICIES:
        item = result["policies"][policy]
        lines.append(
            f"| {policy} | {item['n']} | {_format_rate(item['rule_invalid_operation_exposure_rate'])} | "
            f"{_format_rate(item['unsafe_candidate_exposure_rate'])} | "
            f"{_format_rate(item['safe_task_success_rate'])} | {_format_rate(item['safe_resolution_rate'])} | "
            f"{_format_rate(item['block_rate'])} | {_format_rate(item['defer_rate'])} | "
            f"{item['mean_semantic_calls'] or 0:.2f} | "
            f"{item['conceptual_policy_cost_usd']:.4f} |"
        )
    lines.extend(["", "## Development repair diagnostics", ""])
    for policy, item in result["repair"].items():
        lines.extend(
            [
                f"### {policy}",
                "",
                f"Initial independently failed cases: {item['initial_independent_failures']}",
                "",
                "| Attempt | Entered | Newly recovered | Marginal recovery | Recovery@k |",
                "| ---: | ---: | ---: | ---: | ---: |",
            ]
        )
        for attempt, values in item["attempts"].items():
            lines.append(
                f"| {attempt} | {values['entered']} | {values['newly_recovered']} | "
                f"{_format_rate(values['marginal_recovery_rate'])} | {_format_rate(values['recovery_at_k'])} |"
            )
        lines.extend(
            [
                "",
                f"Repeated-violation rate: {_format_rate(item['repeated_violation_rate'])}; "
                f"rule-regression rate: {_format_rate(item['rule_regression_rate'])}.",
                "",
            ]
        )
    lines.append(
        "Development metrics are diagnostic only and must not be pooled with or reported as held-out results."
    )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit one completed MICEPlan-Lab development run")
    parser.add_argument("run_directory", type=Path)
    parser.add_argument(
        "--data-directory",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "data" / "miceplan_lab_v1_1",
    )
    parser.add_argument(
        "--pricing",
        type=Path,
        default=Path(__file__).with_name("PRICING_KIMI_K27_2026-07-21.json"),
    )
    args = parser.parse_args()
    pricing = json.loads(args.pricing.read_text(encoding="utf-8"))
    result = analyze(args.run_directory, args.data_directory, pricing)
    (args.run_directory / "development_analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (args.run_directory / "development_analysis.md").write_text(
        render_markdown(result), encoding="utf-8"
    )
    print(json.dumps(result["completion"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
