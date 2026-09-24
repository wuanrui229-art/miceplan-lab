from __future__ import annotations

import argparse
import copy
import json
import os
import random
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .execution import ExperimentExecutor, file_sha256, load_jsonl, offline_evaluate_outcome
from .journal import JournaledAdapter, RunJournal, sha256_json, utc_now
from .live_adapter import DeepSeekStrictToolAdapter, OpenAICompatibleModelAdapter
from .run_development import load_local_env, model_profile
from .seeded_runner import SEEDED_POLICIES, SeededRecoveryRunner
from .verify_integrity import verify_dataset_manifest, verify_protocol_manifest


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
RUNS = DATA / "runs"
REHEARSALS = DATA / "formal_rehearsals"
SELECTION_PATH = DATA / "formal_selection_v1_2.json"
FORMAL_SEED = 20260722

FORMAL_MODELS = {
    "kimi": {
        "model_id": "kimi-k2.7-code-highspeed",
        "provider": "Moonshot AI / Kimi Open Platform",
        "endpoint_env": "MICEPLAN_LLM_ENDPOINT",
        "endpoint_default": "UNCONFIGURED",
        "api_key_env": "MICEPLAN_LLM_API_KEY",
        "adapter": OpenAICompatibleModelAdapter,
        "output_contract": "provider-enforced response_format JSON Schema",
        "pricing_file": "PRICING_KIMI_K27_HIGHSPEED_2026-07-21.json",
    },
    "deepseek": {
        "model_id": "deepseek-v4-pro",
        "provider": "DeepSeek Open Platform / strict-tool beta",
        "endpoint_env": "MICEPLAN_DEEPSEEK_ENDPOINT",
        "endpoint_default": "https://api.deepseek.com/beta/chat/completions",
        "api_key_env": "MICEPLAN_DEEPSEEK_API_KEY",
        "adapter": DeepSeekStrictToolAdapter,
        "output_contract": "provider-enforced strict function tool JSON Schema (beta)",
        "pricing_file": "PRICING_DEEPSEEK_V4_PRO_2026-07-21.json",
    },
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _stable_schedule(jobs: list[dict[str, Any]], seed: int, *, natural: bool) -> list[dict[str, Any]]:
    result = [dict(job) for job in jobs]
    random.Random(seed).shuffle(result)
    for index, job in enumerate(result):
        selector = int(sha256_json({"seed": seed, **job})[:8], 16)
        if natural:
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
        else:
            job["repair_policy_order"] = (
                ["SEEDED_VALIDATE_AND_REPAIR", "SEEDED_VALIDATE_AND_BLIND_RETRY"]
                if selector % 2 == 0
                else ["SEEDED_VALIDATE_AND_BLIND_RETRY", "SEEDED_VALIDATE_AND_REPAIR"]
            )
        job["schedule_index"] = index
    return result


def build_natural_jobs(selection: dict[str, Any], requests: list[dict[str, Any]]) -> list[dict[str, Any]]:
    natural = selection["natural_incidence"]
    selected = set(natural["request_ids"])
    repeat_tasks = set(natural["repeat_subset_semantic_task_ids"])
    by_id = {row["request_id"]: row for row in requests}
    jobs = [
        {"request_id": request_id, "replicate_id": int(replicate_id)}
        for request_id in sorted(selected)
        for replicate_id in natural["full_replicate_ids"]
    ]
    repeat_requests = sorted(
        request_id for request_id in selected if by_id[request_id]["semantic_task_id"] in repeat_tasks
    )
    jobs.extend(
        {"request_id": request_id, "replicate_id": int(replicate_id)}
        for request_id in repeat_requests
        for replicate_id in natural["repeat_subset_additional_replicate_ids"]
    )
    return _stable_schedule(jobs, FORMAL_SEED, natural=True)


def _seed_index() -> dict[str, dict[str, Any]]:
    return {
        row["seed_id"]: row
        for filename in ("fault_seeds_v1_2.jsonl", "fault_seeds_composite_v1_2.jsonl")
        for row in load_jsonl(DATA / filename)
    }


def build_seeded_jobs(
    selection: dict[str, Any], requests: list[dict[str, Any]], seeds: dict[str, dict[str, Any]]
) -> list[dict[str, Any]]:
    seeded = selection["seeded_conditional_recovery"]
    selected_ids = list(seeded["single_fault_seed_ids"]) + list(seeded["composite_fault_seed_ids"])
    repeat_ids = set(seeded["repeat_subset_seed_ids"])
    requests_by_task: dict[str, list[dict[str, Any]]] = {}
    for request in requests:
        if request["split"] == "test":
            requests_by_task.setdefault(request["semantic_task_id"], []).append(request)
    jobs: list[dict[str, Any]] = []
    for seed_id in selected_ids:
        seed = seeds[seed_id]
        task_requests = sorted(requests_by_task[seed["semantic_task_id"]], key=lambda row: row["request_id"])
        for request in task_requests:
            for replicate_id in seeded["full_replicate_ids"]:
                jobs.append(
                    {"seed_id": seed_id, "request_id": request["request_id"], "replicate_id": int(replicate_id)}
                )
            if seed_id in repeat_ids:
                for replicate_id in seeded["repeat_subset_additional_replicate_ids"]:
                    jobs.append(
                        {"seed_id": seed_id, "request_id": request["request_id"], "replicate_id": int(replicate_id)}
                    )
    return _stable_schedule(jobs, FORMAL_SEED + 1, natural=False)


def audit_formal_preconditions() -> dict[str, Any]:
    failures = verify_dataset_manifest() + verify_protocol_manifest()
    manifest = _read_json(DATA / "manifest.json")
    audit = _read_json(DATA / "audit_report.json")
    review = _read_json(DATA / "surface_review.json")
    protocol = _read_json(DATA / "protocol_manifest.json")
    selection = _read_json(SELECTION_PATH)
    if failures:
        raise RuntimeError("Frozen integrity audit failed: " + "; ".join(failures))
    if audit.get("machine_audit") != "PASS" or audit.get("status") != "passed":
        raise RuntimeError("Machine audit has not passed")
    if review.get("status") != "PASS" or review.get("reviewer_role") != "author-supervised internal bilingual surface-form QA":
        raise RuntimeError("Internal bilingual surface-form QA has not passed")
    if protocol.get("status") != "benchmark-and-protocol-frozen-before-formal-calls":
        raise RuntimeError("Protocol is not frozen")
    if not selection.get("created_before_formal_calls"):
        raise RuntimeError("Formal selection was not declared before formal calls")
    for filename, expected in selection["source_hashes"].items():
        if file_sha256(DATA / filename) != expected:
            raise RuntimeError(f"Formal selection source hash is stale: {filename}")
    if not (ROOT / "paper" / "experiments" / "miceplan_lab" / "SECOND_MODEL_FREEZE_2026-07-21.md").exists():
        raise RuntimeError("Second-model freeze record is missing")

    requests = load_jsonl(DATA / "requests.jsonl")
    request_by_id = {row["request_id"]: row for row in requests}
    natural_ids = selection["natural_incidence"]["request_ids"]
    if len(natural_ids) != 144 or any(request_by_id[value]["split"] != "test" for value in natural_ids):
        raise RuntimeError("Natural formal selection is not exactly 144 held-out requests")
    seeds = _seed_index()
    selected_seed_ids = (
        selection["seeded_conditional_recovery"]["single_fault_seed_ids"]
        + selection["seeded_conditional_recovery"]["composite_fault_seed_ids"]
    )
    if len(selected_seed_ids) != 63 or any(seeds[value]["split"] != "test" for value in selected_seed_ids):
        raise RuntimeError("Seeded formal selection is not exactly 63 held-out seeds")
    return {
        "status": "PASS",
        "machine_audit": "PASS",
        "surface_review": "PASS (internal QA; not expert validation)",
        "protocol_freeze": protocol["freeze_date"],
        "formal_calls_started_before_rehearsal": bool(manifest.get("formal_model_calls_started")),
        "formal_selection_sha256": file_sha256(SELECTION_PATH),
    }


def _provider(provider_key: str) -> dict[str, Any]:
    frozen = dict(FORMAL_MODELS[provider_key])
    frozen["endpoint"] = os.getenv(str(frozen["endpoint_env"]), str(frozen["endpoint_default"]))
    frozen["profile"] = model_profile(str(frozen["model_id"]))
    return frozen


def build_plan(track: str, provider_key: str, run_id: str) -> dict[str, Any]:
    selection = _read_json(SELECTION_PATH)
    requests = load_jsonl(DATA / "requests.jsonl")
    frozen = _provider(provider_key)
    profile = dict(frozen["profile"])
    if track == "natural":
        schedule = build_natural_jobs(selection, requests)
        policy_count = 5
        min_calls, max_calls = 2 * len(schedule), 8 * len(schedule)
        experiment_track = "formal_natural_incidence"
    else:
        schedule = build_seeded_jobs(selection, requests, _seed_index())
        policy_count = 3
        min_calls, max_calls = 2 * len(schedule), 6 * len(schedule)
        experiment_track = "formal_seeded_conditional_recovery"
    plan = {
        "run_id": run_id,
        "evidence_status": "formal held-out",
        "experiment_track": experiment_track,
        "protocol_version": "miceplan-lab-validation-recovery-v1.2",
        "dataset_version": "miceplan-lab-v1.1",
        "selection_version": selection["selection_version"],
        "provider_key": provider_key,
        "provider": frozen["provider"],
        "endpoint": frozen["endpoint"],
        "model_id": frozen["model_id"],
        "access_date": date.today().isoformat(),
        "prompt_hashes": {
            path.name: file_sha256(path) for path in sorted((DATA / "prompts").glob("*.txt"))
        },
        "schema_hash": file_sha256(DATA / "schemas" / "layout-edit-ir.schema.json"),
        "formal_selection_hash": file_sha256(SELECTION_PATH),
        "source_hashes": dict(selection["source_hashes"]),
        "scheduled_request_ids": sorted({job["request_id"] for job in schedule}),
        "scheduled_seed_ids": sorted({job["seed_id"] for job in schedule if "seed_id" in job}),
        "replicate_ids": sorted({int(job["replicate_id"]) for job in schedule}),
        "schedule_seed": FORMAL_SEED if track == "natural" else FORMAL_SEED + 1,
        "schedule": schedule,
        "decoding": {
            **profile,
            "semantic_repair_limit": 3,
            "output_contract": frozen["output_contract"],
        },
        "gold_visible_to_model": False,
        "fault_seed_visible_as_previous_candidate": track == "seeded",
        "expected": {
            "jobs": len(schedule),
            "policy_outcomes": len(schedule) * policy_count,
            "minimum_model_calls": min_calls,
            "maximum_model_calls": max_calls,
        },
        "pricing_file": frozen["pricing_file"],
    }
    if track == "natural" and len(schedule) != 216:
        raise RuntimeError(f"Expected 216 natural jobs, observed {len(schedule)}")
    if track == "seeded" and len(schedule) != 210:
        raise RuntimeError(f"Expected 210 seeded jobs, observed {len(schedule)}")
    return plan


def _write_rehearsal(plans: list[dict[str, Any]], preflight: dict[str, Any]) -> Path:
    REHEARSALS.mkdir(parents=True, exist_ok=True)
    if len(plans) == 4:
        scope = "all-models-all-tracks"
    else:
        scope = "--".join(
            f"{plan['provider_key']}-{plan['experiment_track'].removeprefix('formal_')}"
            for plan in plans
        )
    path = REHEARSALS / f"formal_zero_call_rehearsal_{scope}_{date.today().isoformat()}.json"
    payload = {
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "PASS",
        "preflight": preflight,
        "model_calls_made": 0,
        "held_out_responses_observed": 0,
        "plans": plans,
        "aggregate_expected": {
            "runs": len(plans),
            "jobs": sum(plan["expected"]["jobs"] for plan in plans),
            "policy_outcomes": sum(plan["expected"]["policy_outcomes"] for plan in plans),
            "minimum_model_calls": sum(plan["expected"]["minimum_model_calls"] for plan in plans),
            "maximum_model_calls": sum(plan["expected"]["maximum_model_calls"] for plan in plans),
        },
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _mark_formal_execution_started(run_id: str, track: str, provider_key: str) -> None:
    path = DATA / "manifest.json"
    manifest = _read_json(path)
    manifest["formal_model_calls_started"] = True
    starts = list(manifest.get("formal_run_initializations", []))
    if not any(item.get("run_id") == run_id for item in starts):
        starts.append(
            {
                "run_id": run_id,
                "track": track,
                "provider": provider_key,
                "initialized_at": utc_now(),
            }
        )
    manifest["formal_run_initializations"] = starts
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _adapter_factory(provider_key: str, frozen: dict[str, Any]) -> Callable[[], OpenAICompatibleModelAdapter]:
    api_key = os.environ[str(frozen["api_key_env"])]
    profile = dict(frozen["profile"])
    adapter_class = frozen["adapter"]

    def create() -> OpenAICompatibleModelAdapter:
        return adapter_class(
            endpoint=str(frozen["endpoint"]),
            api_key=api_key,
            model=str(frozen["model_id"]),
            temperature=profile["temperature"],
            max_output_tokens=int(profile["max_output_tokens"]),
            max_tokens_parameter=str(profile["max_tokens_parameter"]),
            extra_request_parameters=dict(profile["extra_request_parameters"]),
        )

    return create


def _seeded_outcome_key(run_id: str, seed_id: str, request_id: str, replicate_id: int, policy: str) -> str:
    return sha256_json(
        {
            "run_id": run_id,
            "seed_id": seed_id,
            "request_id": request_id,
            "replicate_id": replicate_id,
            "policy": policy,
        }
    )


def _run_seeded(plan: dict[str, Any], journal: RunJournal, adapter_factory: Callable[[], Any]) -> dict[str, int]:
    seeds = _seed_index()
    requests = {row["request_id"]: row for row in load_jsonl(DATA / "requests.jsonl")}
    scenes = {row["scene_id"]: row for row in load_jsonl(DATA / "scenes.jsonl")}
    gold = {row["semantic_task_id"]: row for row in load_jsonl(DATA / "gold.jsonl")}
    for position, job in enumerate(plan["schedule"], start=1):
        seed = seeds[job["seed_id"]]
        request = requests[job["request_id"]]
        replicate_id = int(job["replicate_id"])
        keys = {
            policy: _seeded_outcome_key(plan["run_id"], seed["seed_id"], request["request_id"], replicate_id, policy)
            for policy in SEEDED_POLICIES
        }
        if all(journal.has_outcome(value) for value in keys.values()):
            continue
        scene = scenes[request["scene_id"]]
        initial_ir = copy.deepcopy(seed["ir"])
        initial_ir["request_id"] = request["request_id"]
        initial_ir["language"] = request["language"]
        adapter = JournaledAdapter(adapter_factory(), journal, replicate_id)
        outcomes = SeededRecoveryRunner(adapter, DATA / "prompts", max_semantic_repairs=3).run(
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
                    "seed_rule_ids": seed.get("rule_ids", [seed.get("rule_id")]),
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
        print(f"[{position}/{len(plan['schedule'])}] {seed['seed_id']} / {request['request_id']} completed", flush=True)
    return journal.verify()


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or execute frozen MICEPlan-Lab formal runs")
    parser.add_argument("--track", choices=("natural", "seeded", "all"), default="all")
    parser.add_argument("--provider", choices=("kimi", "deepseek", "all"), default="all")
    parser.add_argument("--run-id", help="Required only to override a single formal run identifier")
    parser.add_argument("--execute", action="store_true", help="Actually send held-out provider requests")
    args = parser.parse_args()

    load_local_env(ROOT / "paper" / "system" / ".env")
    preflight = audit_formal_preconditions()
    tracks = ("natural", "seeded") if args.track == "all" else (args.track,)
    providers = ("kimi", "deepseek") if args.provider == "all" else (args.provider,)
    plans = []
    for provider_key in providers:
        for track in tracks:
            run_id = args.run_id or f"formal-{track}-{provider_key}-v1-2"
            plans.append(build_plan(track, provider_key, run_id))

    if not args.execute:
        path = _write_rehearsal(plans, preflight)
        aggregate = {
            "runs": len(plans),
            "jobs": sum(plan["expected"]["jobs"] for plan in plans),
            "policy_outcomes": sum(plan["expected"]["policy_outcomes"] for plan in plans),
            "minimum_model_calls": sum(plan["expected"]["minimum_model_calls"] for plan in plans),
            "maximum_model_calls": sum(plan["expected"]["maximum_model_calls"] for plan in plans),
        }
        print(json.dumps({"status": "PASS", "model_calls_made": 0, "rehearsal": str(path), "aggregate": aggregate}, indent=2))
        return

    if len(plans) != 1 or args.track == "all" or args.provider == "all":
        raise RuntimeError("Formal execution requires exactly one --track and one --provider")
    plan = plans[0]
    provider_key = args.provider
    frozen = _provider(provider_key)
    missing = []
    if str(frozen["endpoint"]) == "UNCONFIGURED":
        missing.append(str(frozen["endpoint_env"]))
    if not os.getenv(str(frozen["api_key_env"])):
        missing.append(str(frozen["api_key_env"]))
    if missing:
        raise RuntimeError("Missing frozen provider configuration: " + ", ".join(missing))
    journal = RunJournal(RUNS / plan["run_id"], plan)
    _mark_formal_execution_started(plan["run_id"], args.track, provider_key)
    factory = _adapter_factory(provider_key, frozen)
    if args.track == "natural":
        counts = ExperimentExecutor(
            data_directory=DATA,
            journal=journal,
            adapter_factory=factory,
            max_semantic_repairs=3,
            progress_callback=lambda position, total, request_id, replicate_id: print(
                f"[{position}/{total}] {request_id} replicate={replicate_id} completed", flush=True
            ),
        ).run()
    else:
        counts = _run_seeded(plan, journal, factory)
    print(json.dumps({"run_id": plan["run_id"], "status": "complete-or-safely-resumed", "journal": counts}, indent=2))


if __name__ == "__main__":
    main()
