from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path
from typing import Any

from .journal import AppendOnlyHashChain


def diagnose(run_directory: Path) -> dict[str, Any]:
    manifest = json.loads((run_directory / "run_manifest.json").read_text(encoding="utf-8"))
    calls = AppendOnlyHashChain(run_directory / "calls.jsonl").payloads
    errors = AppendOnlyHashChain(run_directory / "infrastructure_errors.jsonl").payloads
    initial = [row for row in calls if row["identity"]["semantic_attempt"] == 0]
    expected_initial = len(manifest["scheduled_request_ids"]) * len(manifest["replicate_ids"]) * 2
    latencies = [float(row["model_call"]["latency_ms"]) for row in initial]
    tokens = [int(row["model_call"]["usage"].get("total_tokens", 0) or 0) for row in initial]
    schema_valid = [row["model_call"].get("ir") is not None and row["model_call"].get("error") is None for row in initial]
    truncated = []
    for row in initial:
        response = row["model_call"].get("raw_response") or {}
        choice = (response.get("choices") or [{}])[0]
        truncated.append(choice.get("finish_reason") == "length")
    completed = len(initial) == expected_initial and not errors
    pass_gate = completed and all(schema_valid) and not any(truncated)
    return {
        "run_directory": str(run_directory),
        "model_id": manifest["model_id"],
        "request_ids": manifest["scheduled_request_ids"],
        "expected_initial_calls": expected_initial,
        "recorded_initial_calls": len(initial),
        "infrastructure_error_records": len(errors),
        "schema_valid_rate": sum(schema_valid) / expected_initial if expected_initial else 0,
        "truncation_rate": sum(truncated) / expected_initial if expected_initial else 0,
        "median_latency_ms": statistics.median(latencies) if latencies else None,
        "median_total_tokens": statistics.median(tokens) if tokens else None,
        "selection_gate_pass": pass_gate,
    }


def compare(run_directories: list[Path]) -> dict[str, Any]:
    models = [diagnose(path) for path in run_directories]
    passing = [row for row in models if row["selection_gate_pass"]]
    preferred = None
    if passing:
        preferred = min(
            passing,
            key=lambda row: (
                row["median_total_tokens"] if row["median_total_tokens"] is not None else float("inf"),
                row["median_latency_ms"] if row["median_latency_ms"] is not None else float("inf"),
            ),
        )["model_id"]
    return {
        "selection_rule": (
            "Require all expected initial calls, zero infrastructure errors, 100% schema-valid output, "
            "and zero length truncation; among passing models prefer lower median tokens then latency."
        ),
        "models": models,
        "provisional_preferred_model": preferred,
        "formal_model_frozen": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare frozen MICEPlan-Lab development model-selection runs")
    parser.add_argument("run_directories", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = compare(args.run_directories)
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
