from __future__ import annotations

import hashlib
import json
import random
from pathlib import Path
from typing import Any, Callable

from . import DATASET_VERSION, PROTOCOL_VERSION
from .journal import JournaledAdapter, RunJournal, sha256_json, utc_now
from .oracle import evaluate_candidate
from .policy_runner import POLICIES, FiveConditionRunner, ModelAdapter, PolicyOutcome


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_schedule(request_ids: list[str], replicate_ids: list[int], seed: int) -> list[dict[str, Any]]:
    jobs = [
        {"request_id": request_id, "replicate_id": replicate_id}
        for replicate_id in replicate_ids
        for request_id in request_ids
    ]
    random.Random(seed).shuffle(jobs)
    for index, job in enumerate(jobs):
        selector = int(sha256_json({"seed": seed, **job})[:8], 16)
        job["initial_arm_order"] = (
            ["LLM_ONLY", "CONSTRAINT_IN_PROMPT"]
            if selector % 2 == 0
            else ["CONSTRAINT_IN_PROMPT", "LLM_ONLY"]
        )
        job["repair_policy_order"] = (
            ["VALIDATE_AND_REPAIR", "VALIDATE_AND_BLIND_RETRY"]
            if (selector // 2) % 2 == 0
            else ["VALIDATE_AND_BLIND_RETRY", "VALIDATE_AND_REPAIR"]
        )
        job["schedule_index"] = index
    return jobs


def build_run_manifest(
    *,
    run_id: str,
    data_directory: Path,
    model_id: str,
    provider: str,
    endpoint: str,
    access_date: str,
    request_ids: list[str],
    replicate_ids: list[int],
    seed: int,
    decoding: dict[str, Any],
) -> dict[str, Any]:
    prompts = data_directory / "prompts"
    prompt_hashes = {path.name: file_sha256(path) for path in sorted(prompts.glob("*.txt"))}
    schema_path = data_directory / "schemas" / "layout-edit-ir.schema.json"
    return {
        "run_id": run_id,
        "protocol_version": PROTOCOL_VERSION,
        "dataset_version": DATASET_VERSION,
        "model_id": model_id,
        "provider": provider,
        "endpoint": endpoint,
        "access_date": access_date,
        "prompt_hashes": prompt_hashes,
        "schema_hash": file_sha256(schema_path),
        "scheduled_request_ids": request_ids,
        "replicate_ids": replicate_ids,
        "schedule_seed": seed,
        "schedule": build_schedule(request_ids, replicate_ids, seed),
        "decoding": decoding,
        "gold_visible_to_model": False,
    }


def _empty_evaluation() -> dict[str, Any]:
    return {
        "oracle": {
            "status": "UNKNOWN",
            "rule_ids": ["SCHEMA"],
            "object_ids": [],
            "scene_after": None,
            "details": ["No schema-valid candidate was available for offline evaluation."],
            "oracle_version": "miceplan-lab-shapely-oracle-v1.0",
        },
        "correct_defer": False,
        "intent_correct": False,
        "safe_task_success": False,
    }


def offline_evaluate_outcome(
    scene: dict[str, Any], gold: dict[str, Any], outcome: PolicyOutcome
) -> dict[str, Any]:
    evaluation = evaluate_candidate(scene, gold, outcome.final_ir) if outcome.final_ir is not None else _empty_evaluation()
    exposed = outcome.final_action == "EXPOSE"
    oracle_status = evaluation["oracle"]["status"]
    evaluation["exposed"] = exposed
    evaluation["rule_invalid_operation_exposed"] = exposed and oracle_status == "FAIL"
    evaluation["unsupported_candidate_exposed"] = exposed and oracle_status == "UNKNOWN"
    evaluation["unsafe_candidate_exposed"] = exposed and not (
        oracle_status == "PASS" and bool(evaluation["intent_correct"])
    )
    # Backward-compatible field name; protocol v1.1 now defines it as a rule-invalid
    # operation-bearing exposure rather than conflating FAIL and UNKNOWN.
    evaluation["invalid_operation_exposed"] = evaluation["rule_invalid_operation_exposed"]
    evaluation["safe_task_success"] = exposed and bool(evaluation["safe_task_success"])
    evaluation["correct_defer"] = outcome.final_action == "DEFER" and bool(evaluation["correct_defer"])
    evaluation["safe_resolution"] = bool(evaluation["safe_task_success"] or evaluation["correct_defer"])
    return evaluation


def _outcome_key(run_id: str, request_id: str, replicate_id: int, policy: str) -> str:
    return sha256_json(
        {"run_id": run_id, "request_id": request_id, "replicate_id": replicate_id, "policy": policy}
    )


class ExperimentExecutor:
    def __init__(
        self,
        *,
        data_directory: Path,
        journal: RunJournal,
        adapter_factory: Callable[[], ModelAdapter],
        max_semantic_repairs: int = 3,
        progress_callback: Callable[[int, int, str, int], None] | None = None,
    ) -> None:
        self.data_directory = data_directory
        self.journal = journal
        self.adapter_factory = adapter_factory
        self.max_semantic_repairs = max_semantic_repairs
        self.progress_callback = progress_callback
        self.scenes = {row["scene_id"]: row for row in load_jsonl(data_directory / "scenes.jsonl")}
        self.requests = {row["request_id"]: row for row in load_jsonl(data_directory / "requests.jsonl")}
        self.gold = {row["semantic_task_id"]: row for row in load_jsonl(data_directory / "gold.jsonl")}

    def _write_outcome(
        self,
        *,
        request: dict[str, Any],
        replicate_id: int,
        policy: str,
        outcome: PolicyOutcome,
        evaluation: dict[str, Any],
    ) -> None:
        key = _outcome_key(self.journal.manifest["run_id"], request["request_id"], replicate_id, policy)
        for event_index, event in enumerate(outcome.gate_events):
            event_key = sha256_json({"outcome_key": key, "event_index": event_index})
            self.journal.append_gate_event(
                {
                    "event_key": event_key,
                    "outcome_key": key,
                    "request_id": request["request_id"],
                    "replicate_id": replicate_id,
                    "policy": policy,
                    "event_index": event_index,
                    "event": event,
                }
            )
        call_summaries = [
            {
                "call_id": call.call_id,
                "latency_ms": call.latency_ms,
                "usage": call.usage,
                "error": call.error,
                "infrastructure_attempts": call.infrastructure_attempts,
            }
            for call in outcome.model_calls
        ]
        self.journal.append_outcome(
            {
                "outcome_key": key,
                "recorded_at": utc_now(),
                "request_id": request["request_id"],
                "semantic_task_id": request["semantic_task_id"],
                "scene_id": request["scene_id"],
                "language": request["language"],
                "operation_family": request["operation_family"],
                "complexity": request["complexity"],
                "replicate_id": replicate_id,
                "policy": policy,
                "final_action": outcome.final_action,
                "final_ir": outcome.final_ir,
                "semantic_attempts": outcome.semantic_attempts,
                "model_calls": call_summaries,
                "offline_evaluation": evaluation,
            }
        )

    def run(self) -> dict[str, int]:
        schedule = self.journal.manifest["schedule"]
        for position, job in enumerate(schedule, start=1):
            request = self.requests[job["request_id"]]
            replicate_id = int(job["replicate_id"])
            expected_keys = {
                policy: _outcome_key(
                    self.journal.manifest["run_id"], request["request_id"], replicate_id, policy
                )
                for policy in POLICIES
            }
            if all(self.journal.has_outcome(key) for key in expected_keys.values()):
                continue
            scene = self.scenes[request["scene_id"]]
            gold = self.gold[request["semantic_task_id"]]
            adapter = JournaledAdapter(self.adapter_factory(), self.journal, replicate_id)
            outcomes = FiveConditionRunner(
                adapter,
                self.data_directory / "prompts",
                max_semantic_repairs=self.max_semantic_repairs,
            ).run_request(
                request,
                scene,
                initial_arm_order=tuple(job["initial_arm_order"]),
                repair_policy_order=tuple(job["repair_policy_order"]),
            )
            for policy in POLICIES:
                if self.journal.has_outcome(expected_keys[policy]):
                    continue
                outcome = outcomes[policy]
                evaluation = offline_evaluate_outcome(scene, gold, outcome)
                self._write_outcome(
                    request=request,
                    replicate_id=replicate_id,
                    policy=policy,
                    outcome=outcome,
                    evaluation=evaluation,
                )
            if self.progress_callback is not None:
                self.progress_callback(position, len(schedule), request["request_id"], replicate_id)
        return self.journal.verify()
