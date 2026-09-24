from __future__ import annotations

import json
import os
import statistics
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT / "system"
DATASET = ROOT / "data" / os.getenv("MICEPLAN_DATASET_DIR", "miceplan_eval_v1_1")
OUTPUT = ROOT / "experiments" / "results"
sys.path.insert(0, str(SYSTEM_ROOT))

from miceplan.config import load_local_env
from miceplan.geometry import GeometryValidator
from miceplan.models import HallLayout, LayoutEditIR, ModelError
from miceplan.parser import (
    OpenAICompatiblePromptOnlyParser,
    OpenAICompatibleStructuredParser,
    PROMPT_VERSION,
)
from miceplan.solver import DeterministicLayoutSolver, SolveError


PILOT_IDS = (
    "eval-001-en", "eval-002-en", "eval-003-zh", "eval-004-en", "eval-005-en",
    "eval-006-zh", "eval-007-en", "eval-042-en", "eval-043-zh", "eval-044-en",
    "eval-045-zh", "eval-046-zh", "eval-047-zh", "eval-081-zh", "eval-083-en",
    "eval-084-zh", "eval-085-zh", "eval-088-en", "eval-121-en", "eval-126-zh",
)


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def operation_slots(ir: LayoutEditIR) -> set[str]:
    slots: set[str] = set()
    for index, operation in enumerate(ir.operations):
        data = operation.to_dict()
        slots.add(f"op:{index}:type={data['type']}")
        for target in data["target_ids"]:
            slots.add(f"op:{index}:target_id={target}")
        for key in ("count", "width", "height", "x", "y", "region", "booth_type"):
            if data[key] is not None:
                slots.add(f"op:{index}:{key}={data[key]}")
    for reference in ir.unresolved_references:
        slots.add(f"unresolved={reference}")
    return slots


def operations_equal(first: LayoutEditIR, second: LayoutEditIR) -> bool:
    return [item.to_dict() for item in first.operations] == [item.to_dict() for item in second.operations]


def quick_area_infeasible(layout: HallLayout, ir: LayoutEditIR) -> bool:
    requested_area = sum(
        (operation.count or 0) * (operation.width or 0) * (operation.height or 0)
        for operation in ir.operations if operation.type.value == "ADD_BOOTH"
    )
    polygon_area = abs(sum(
        layout.boundary[index][0] * layout.boundary[(index + 1) % len(layout.boundary)][1]
        - layout.boundary[(index + 1) % len(layout.boundary)][0] * layout.boundary[index][1]
        for index in range(len(layout.boundary))
    )) / 2
    return requested_area > polygon_area


def compile_state(layout: HallLayout, ir: LayoutEditIR) -> str:
    if ir.requires_confirmation:
        return "needs_confirmation"
    if quick_area_infeasible(layout, ir):
        return "infeasible"
    try:
        candidate = DeterministicLayoutSolver().solve(layout, ir)
        report = GeometryValidator().validate(layout, candidate, ir)
        return "awaiting_approval" if report.valid else "blocked"
    except SolveError:
        return "infeasible"


def aggregate(rows: list[dict[str, Any]]) -> dict[str, Any]:
    tp = sum(row["slot_tp"] for row in rows)
    fp = sum(row["slot_fp"] for row in rows)
    fn = sum(row["slot_fn"] for row in rows)
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    per_label_f1: list[float] = []
    for label in (True, False):
        label_tp = sum(row["gold_confirmation"] == label and row["pred_confirmation"] == label for row in rows)
        label_fp = sum(row["gold_confirmation"] != label and row["pred_confirmation"] == label for row in rows)
        label_fn = sum(row["gold_confirmation"] == label and row["pred_confirmation"] != label for row in rows)
        label_precision = label_tp / (label_tp + label_fp) if label_tp + label_fp else 0.0
        label_recall = label_tp / (label_tp + label_fn) if label_tp + label_fn else 0.0
        per_label_f1.append(
            2 * label_precision * label_recall / (label_precision + label_recall)
            if label_precision + label_recall else 0.0
        )
    latencies = [row["latency_ms"] for row in rows]
    usage_fields = ("prompt_tokens", "completion_tokens", "total_tokens", "cached_tokens")
    return {
        "n": len(rows),
        "schema_valid_rate": sum(row["schema_valid"] for row in rows) / len(rows),
        "operation_exact_match": sum(row["operation_exact"] for row in rows) / len(rows),
        "ir_decision_exact_match": sum(row["ir_decision_exact"] for row in rows) / len(rows),
        "slot_precision": precision,
        "slot_recall": recall,
        "slot_f1": f1,
        "confirmation_accuracy": sum(row["confirmation_correct"] for row in rows) / len(rows),
        "confirmation_macro_f1": sum(per_label_f1) / len(per_label_f1),
        "pipeline_state_accuracy": sum(row["pipeline_state_correct"] for row in rows) / len(rows),
        "hallucinated_reference_rate": sum(row["hallucinated_reference"] for row in rows) / len(rows),
        "median_latency_ms": statistics.median(latencies),
        "p95_latency_ms": sorted(latencies)[max(0, int(len(latencies) * 0.95) - 1)],
        "usage": {key: sum(int(row["usage"].get(key, 0) or 0) for row in rows) for key in usage_fields},
    }


def main() -> None:
    load_local_env()
    required = ("MICEPLAN_LLM_ENDPOINT", "MICEPLAN_LLM_API_KEY", "MICEPLAN_LLM_MODEL")
    missing = [key for key in required if not os.getenv(key)]
    if missing:
        raise RuntimeError(f"Missing LLM configuration: {', '.join(missing)}")

    mode = os.getenv("MICEPLAN_EVAL_MODE", "schema").strip().lower()
    parser_types = {
        "schema": OpenAICompatibleStructuredParser,
        "prompt_only": OpenAICompatiblePromptOnlyParser,
    }
    if mode not in parser_types:
        raise RuntimeError(f"Unsupported MICEPLAN_EVAL_MODE: {mode}")
    parser = parser_types[mode](
        endpoint=os.environ["MICEPLAN_LLM_ENDPOINT"],
        api_key=os.environ["MICEPLAN_LLM_API_KEY"],
        model=os.environ["MICEPLAN_LLM_MODEL"],
        temperature=float(os.getenv("MICEPLAN_LLM_TEMPERATURE", "0")),
    )
    halls = {row["hall_id"]: HallLayout.from_dict(row) for row in load_jsonl(DATASET / "halls.jsonl")}
    request_rows = load_jsonl(DATASET / "requests.jsonl")
    all_requests = {row["request_id"]: row for row in request_rows}
    scope = os.getenv("MICEPLAN_EVAL_SCOPE", "pilot").strip().lower()
    if scope == "pilot":
        selected = [all_requests[request_id] for request_id in PILOT_IDS]
        expected_split = "development"
    elif scope == "test":
        selected = sorted(
            (row for row in request_rows if row["split"] == "test"),
            key=lambda row: row["request_id"],
        )
        expected_split = "test"
    else:
        raise RuntimeError(f"Unsupported MICEPLAN_EVAL_SCOPE: {scope}")
    if any(row["split"] != expected_split for row in selected):
        raise RuntimeError(f"{scope} selection contains a record outside {expected_split}")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    run_tag = PROMPT_VERSION.rsplit("-", 1)[-1].replace(".", "_")
    predictions_path = OUTPUT / f"kimi_{mode}_{scope}_{run_tag}_predictions.jsonl"
    report_path = OUTPUT / f"kimi_{mode}_{scope}_{run_tag}_report.json"
    infrastructure_log_path = OUTPUT / f"kimi_{mode}_{scope}_{run_tag}_infrastructure_errors.jsonl"
    dataset_manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    resume = os.getenv("MICEPLAN_EVAL_RESUME", "1") == "1"
    result_rows = load_jsonl(predictions_path) if resume and predictions_path.exists() else []
    completed_ids = {row["request_id"] for row in result_rows}
    file_mode = "a" if result_rows else "w"

    with predictions_path.open(file_mode, encoding="utf-8") as handle:
        for index, row in enumerate(selected, start=1):
            if row["request_id"] in completed_ids:
                print(f"[{index:03d}/{len(selected)}] {row['request_id']} resumed", flush=True)
                continue
            layout = halls[row["hall_id"]]
            gold = LayoutEditIR.from_dict(row["gold_ir"])
            started = time.perf_counter_ns()
            body: dict[str, Any] | None = None
            predicted: LayoutEditIR | None = None
            error: str | None = None
            attempt_errors: list[str] = []
            attempts = 0
            transient = False
            for attempts in range(1, 4):
                try:
                    body = parser.request_completion(row["text"], layout)
                    predicted = parser.parse_completion(body)
                    break
                except (ModelError, ValueError) as exc:
                    error = str(exc)
                    attempt_errors.append(error)
                    transient = any(marker in error for marker in (
                        "HTTP 429", "HTTP 500", "HTTP 502", "HTTP 503", "HTTP 504",
                        "timed out", "Temporary failure", "Connection reset",
                        "nodename nor servname provided", "Name or service not known",
                        "Temporary failure in name resolution", "<urlopen error",
                    ))
                    if not transient or attempts == 3:
                        break
                    time.sleep(2 ** (attempts - 1))
            latency_ms = (time.perf_counter_ns() - started) / 1_000_000

            # Infrastructure failures are not model predictions. Record them outside
            # the prediction file and stop immediately so resume cannot turn a DNS or
            # provider outage into 128 false model errors.
            if predicted is None and transient:
                infrastructure_failure = {
                    "request_id": row["request_id"],
                    "mode": mode,
                    "scope": scope,
                    "attempts": attempts,
                    "attempt_errors": attempt_errors,
                    "latency_ms": latency_ms,
                }
                with infrastructure_log_path.open("a", encoding="utf-8") as error_handle:
                    error_handle.write(json.dumps(
                        infrastructure_failure, ensure_ascii=False, sort_keys=True
                    ) + "\n")
                raise RuntimeError(
                    "Evaluation stopped after a transient infrastructure failure; "
                    f"details recorded in {infrastructure_log_path.name}"
                )

            gold_slots = operation_slots(gold)
            predicted_slots = operation_slots(predicted) if predicted else set()
            known_ids = {booth.id for booth in layout.booths}
            predicted_targets = {
                target for operation in predicted.operations for target in operation.target_ids
            } if predicted else set()
            predicted_state = compile_state(layout, predicted) if predicted else None
            operation_exact = operations_equal(gold, predicted) if predicted else False
            confirmation_correct = (
                gold.requires_confirmation == predicted.requires_confirmation if predicted else False
            )
            usage = body.get("usage", {}) if body else {}
            result = {
                "request_id": row["request_id"],
                "input_text": row["text"],
                "gold_ir": row["gold_ir"],
                "split": row["split"],
                "language": row["language"],
                "category": row["category"],
                "schema_valid": predicted is not None,
                "operation_exact": operation_exact,
                "confirmation_correct": confirmation_correct,
                "ir_decision_exact": bool(
                    predicted and operation_exact and confirmation_correct
                    and set(gold.unresolved_references) == set(predicted.unresolved_references)
                ),
                "slot_tp": len(gold_slots & predicted_slots),
                "slot_fp": len(predicted_slots - gold_slots),
                "slot_fn": len(gold_slots - predicted_slots),
                "gold_confirmation": gold.requires_confirmation,
                "pred_confirmation": predicted.requires_confirmation if predicted else None,
                "gold_pipeline_state": row["expected_pipeline_state"],
                "pred_pipeline_state": predicted_state,
                "pipeline_state_correct": predicted_state == row["expected_pipeline_state"],
                "hallucinated_reference": bool(predicted_targets - known_ids),
                "latency_ms": latency_ms,
                "usage": usage,
                "attempts": attempts,
                "attempt_errors": attempt_errors,
                "prediction": predicted.to_dict() if predicted else None,
                "error": error,
                "raw_response": body,
            }
            result_rows.append(result)
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            print(
                f"[{index:02d}/{len(selected)}] {row['request_id']} "
                f"schema={predicted is not None} op_exact={operation_exact} "
                f"confirm={confirmation_correct} latency_ms={latency_ms:.0f}",
                flush=True,
            )

    report = {
        "system": type(parser).__name__,
        "mode": mode,
        "provider": "Moonshot AI / Kimi Open Platform",
        "model": parser.model,
        "endpoint": parser.endpoint,
        "temperature": parser.temperature,
        "dataset": dataset_manifest["dataset"],
        "dataset_manifest_sha256": dataset_manifest["files"]["requests.jsonl"]["sha256"],
        "split": expected_split,
        "scope": scope,
        "request_ids": [row["request_id"] for row in selected],
        "access_date": "2026-07-16",
        "prompt_version": PROMPT_VERSION,
        "overall": aggregate(result_rows),
        "by_language": {
            language: aggregate([item for item in result_rows if item["language"] == language])
            for language in ("zh", "en")
        },
        "by_category": {
            category: aggregate([item for item in result_rows if item["category"] == category])
            for category in sorted({item["category"] for item in result_rows})
        },
        "confirmation_confusion": dict(Counter(
            f"gold_{item['gold_confirmation']}_pred_{item['pred_confirmation']}" for item in result_rows
        )),
        "limitations": [
            "The evaluation scope and request IDs are recorded explicitly.",
            "Gold IR is template-derived and human review remains pending.",
            "One decoding run is insufficient for a stability claim.",
            "Prompt-only output receives strict local validation but no repair.",
        ],
    }
    if len(result_rows) != len(selected):
        raise RuntimeError(f"Expected {len(selected)} records, found {len(result_rows)}")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report["overall"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
