from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import random
from datetime import date
from pathlib import Path
from typing import Any

from .execution import file_sha256, load_jsonl, offline_evaluate_outcome
from .journal import JournaledAdapter, RunJournal, sha256_json, utc_now
from .live_adapter import OpenAICompatibleModelAdapter
from .run_development import load_local_env, model_profile
from .seeded_runner import SEEDED_POLICIES, SeededRecoveryRunner


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
RUNS = DATA / "runs"


def select_seeds(seed_file: Path, seed_ids: list[str] | None, limit: int) -> list[dict[str, Any]]:
    rows = [row for row in load_jsonl(seed_file) if row["split"] == "development"]
    by_id = {row["seed_id"]: row for row in rows}
    if seed_ids:
        missing = [seed_id for seed_id in seed_ids if seed_id not in by_id]
        if missing:
            raise ValueError(f"Unknown or non-development seed IDs: {', '.join(missing)}")
        return [by_id[seed_id] for seed_id in seed_ids]
    return sorted(rows, key=lambda row: row["seed_id"])[:limit]


def build_jobs(
    seeds: list[dict[str, Any]], requests: list[dict[str, Any]], replicate_ids: list[int], schedule_seed: int
) -> list[dict[str, Any]]:
    by_task: dict[str, list[dict[str, Any]]] = {}
    for request in requests:
        if request["split"] == "development":
            by_task.setdefault(request["semantic_task_id"], []).append(request)
    jobs = [
        {
            "seed_id": seed["seed_id"],
            "request_id": request["request_id"],
            "replicate_id": replicate_id,
        }
        for seed in seeds
        for request in sorted(by_task[seed["semantic_task_id"]], key=lambda row: row["request_id"])
        for replicate_id in replicate_ids
    ]
    random.Random(schedule_seed).shuffle(jobs)
    for index, job in enumerate(jobs):
        selector = int(sha256_json({"schedule_seed": schedule_seed, **job})[:8], 16)
        job["repair_policy_order"] = (
            ["SEEDED_VALIDATE_AND_REPAIR", "SEEDED_VALIDATE_AND_BLIND_RETRY"]
            if selector % 2 == 0
            else ["SEEDED_VALIDATE_AND_BLIND_RETRY", "SEEDED_VALIDATE_AND_REPAIR"]
        )
        job["schedule_index"] = index
    return jobs


def _outcome_key(run_id: str, seed_id: str, request_id: str, replicate_id: int, policy: str) -> str:
    return sha256_json(
        {
            "run_id": run_id,
            "seed_id": seed_id,
            "request_id": request_id,
            "replicate_id": replicate_id,
            "policy": policy,
        }
    )


def _clone_seed_ir(seed: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    value = copy.deepcopy(seed["ir"])
    value["request_id"] = request["request_id"]
    value["language"] = request["language"]
    return value


def build_manifest(
    *,
    run_id: str,
    seeds: list[dict[str, Any]],
    jobs: list[dict[str, Any]],
    replicate_ids: list[int],
    schedule_seed: int,
    model_id: str,
    endpoint: str,
    profile: dict[str, object],
    max_semantic_repairs: int,
    seed_file: Path,
) -> dict[str, Any]:
    prompt_directory = DATA / "prompts"
    return {
        "run_id": run_id,
        "protocol_version": "1.2-development-candidate",
        "dataset_version": "miceplan-lab-v1.1+intent-preserving-fault-seeds-v1.2",
        "experiment_track": "seeded_conditional_recovery",
        "provider": "Moonshot AI / Kimi Open Platform",
        "endpoint": endpoint,
        "model_id": model_id,
        "access_date": date.today().isoformat(),
        "prompt_hashes": {
            path.name: file_sha256(path) for path in sorted(prompt_directory.glob("*.txt"))
        },
        "schema_hash": file_sha256(DATA / "schemas" / "layout-edit-ir.schema.json"),
        "fault_seed_file": seed_file.name,
        "fault_seed_file_hash": file_sha256(seed_file),
        "scheduled_seed_ids": [row["seed_id"] for row in seeds],
        "scheduled_request_ids": sorted({job["request_id"] for job in jobs}),
        "replicate_ids": replicate_ids,
        "schedule_seed": schedule_seed,
        "schedule": jobs,
        "decoding": {**profile, "semantic_repair_limit": max_semantic_repairs},
        "gold_visible_to_model": False,
        "fault_seed_visible_as_previous_candidate": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run development-only intent-preserving seeded recovery")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--seed-ids", help="Comma-separated development fault-seed IDs")
    parser.add_argument(
        "--seed-file",
        type=Path,
        default=DATA / "fault_seeds_v1_2.jsonl",
        help="Intent-preserving seed JSONL; only development rows are eligible here",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--schedule-seed", type=int, default=20260721)
    parser.add_argument("--run-id", default=f"seeded-development-{date.today().isoformat()}")
    parser.add_argument("--model", default="kimi-k2.7-code-highspeed")
    parser.add_argument("--max-semantic-repairs", type=int, default=3)
    args = parser.parse_args()

    load_local_env(ROOT / "paper" / "system" / ".env")
    requested = [value.strip() for value in (args.seed_ids or "").split(",") if value.strip()]
    seed_file = args.seed_file.resolve()
    if not seed_file.is_file():
        raise FileNotFoundError(seed_file)
    seeds = select_seeds(seed_file, requested or None, args.limit)
    requests = load_jsonl(DATA / "requests.jsonl")
    replicate_ids = list(range(1, args.replicates + 1))
    jobs = build_jobs(seeds, requests, replicate_ids, args.schedule_seed)
    profile = model_profile(args.model)
    manifest = build_manifest(
        run_id=args.run_id,
        seeds=seeds,
        jobs=jobs,
        replicate_ids=replicate_ids,
        schedule_seed=args.schedule_seed,
        model_id=args.model,
        endpoint=os.getenv("MICEPLAN_LLM_ENDPOINT", "UNCONFIGURED"),
        profile=profile,
        max_semantic_repairs=args.max_semantic_repairs,
        seed_file=seed_file,
    )
    print(
        f"Seeded development jobs: {len(jobs)}; seeds: {len(seeds)}; "
        "three policies per job; held-out requests: 0"
    )
    if not args.execute:
        print("Dry run only. Add --execute to send repair calls; no provider call was made.")
        return
    missing = [
        key for key in ("MICEPLAN_LLM_ENDPOINT", "MICEPLAN_LLM_API_KEY") if not os.getenv(key)
    ]
    if missing:
        raise RuntimeError(f"Missing LLM configuration: {', '.join(missing)}")

    seed_by_id = {row["seed_id"]: row for row in seeds}
    request_by_id = {row["request_id"]: row for row in requests}
    scenes = {row["scene_id"]: row for row in load_jsonl(DATA / "scenes.jsonl")}
    gold = {row["semantic_task_id"]: row for row in load_jsonl(DATA / "gold.jsonl")}
    journal = RunJournal(RUNS / args.run_id, manifest)

    def adapter_factory() -> OpenAICompatibleModelAdapter:
        return OpenAICompatibleModelAdapter(
            endpoint=os.environ["MICEPLAN_LLM_ENDPOINT"],
            api_key=os.environ["MICEPLAN_LLM_API_KEY"],
            model=args.model,
            temperature=profile["temperature"],
            max_output_tokens=int(profile["max_output_tokens"]),
            max_tokens_parameter=str(profile["max_tokens_parameter"]),
            extra_request_parameters=dict(profile["extra_request_parameters"]),
        )

    for position, job in enumerate(jobs, start=1):
        seed = seed_by_id[job["seed_id"]]
        request = request_by_id[job["request_id"]]
        replicate_id = int(job["replicate_id"])
        keys = {
            policy: _outcome_key(args.run_id, seed["seed_id"], request["request_id"], replicate_id, policy)
            for policy in SEEDED_POLICIES
        }
        if all(journal.has_outcome(value) for value in keys.values()):
            continue
        scene = scenes[request["scene_id"]]
        initial_ir = _clone_seed_ir(seed, request)
        adapter = JournaledAdapter(adapter_factory(), journal, replicate_id)
        outcomes = SeededRecoveryRunner(
            adapter, DATA / "prompts", max_semantic_repairs=args.max_semantic_repairs
        ).run(
            request=request,
            scene=scene,
            initial_ir=initial_ir,
            repair_policy_order=tuple(job["repair_policy_order"]),
        )
        initial_evaluation = offline_evaluate_outcome(
            scene,
            gold[request["semantic_task_id"]],
            type("InitialSeedOutcome", (), {"final_ir": initial_ir, "final_action": "EXPOSE"})(),
        )
        for policy in SEEDED_POLICIES:
            if journal.has_outcome(keys[policy]):
                continue
            outcome = outcomes[policy]
            evaluation = offline_evaluate_outcome(scene, gold[request["semantic_task_id"]], outcome)
            for event_index, event in enumerate(outcome.gate_events):
                journal.append_gate_event(
                    {
                        "event_key": sha256_json({"outcome_key": keys[policy], "event_index": event_index}),
                        "outcome_key": keys[policy],
                        "seed_id": seed["seed_id"],
                        "request_id": request["request_id"],
                        "replicate_id": replicate_id,
                        "policy": policy,
                        "event_index": event_index,
                        "event": event,
                    }
                )
            journal.append_outcome(
                {
                    "outcome_key": keys[policy],
                    "recorded_at": utc_now(),
                    "seed_id": seed["seed_id"],
                    "seed_rule_id": seed.get("rule_id"),
                    "seed_rule_ids": seed["rule_ids"] if "rule_ids" in seed else [seed["rule_id"]],
                    "fault_cardinality": int(seed.get("fault_cardinality", 1)),
                    "request_id": request["request_id"],
                    "semantic_task_id": request["semantic_task_id"],
                    "scene_id": request["scene_id"],
                    "language": request["language"],
                    "operation_family": request["operation_family"],
                    "complexity": request["complexity"],
                    "replicate_id": replicate_id,
                    "policy": policy,
                    "initial_ir": initial_ir,
                    "initial_offline_evaluation": initial_evaluation,
                    "final_action": outcome.final_action,
                    "final_ir": outcome.final_ir,
                    "semantic_attempts": outcome.semantic_attempts,
                    "model_calls": [
                        {
                            "call_id": call.call_id,
                            "latency_ms": call.latency_ms,
                            "usage": call.usage,
                            "error": call.error,
                            "infrastructure_attempts": call.infrastructure_attempts,
                        }
                        for call in outcome.model_calls
                    ],
                    "offline_evaluation": evaluation,
                }
            )
        print(
            f"[{position}/{len(jobs)}] {seed['seed_id']} / {request['request_id']} completed",
            flush=True,
        )
    print(f"Seeded development run complete or safely resumed: {journal.verify()}")


if __name__ == "__main__":
    main()
