from __future__ import annotations

import argparse
import json
import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .credentials import resolve_api_key
from .execution import ExperimentExecutor, file_sha256
from .formal_run import (
    DATA,
    ROOT,
    RUNS,
    _mark_formal_execution_started,
    _run_seeded,
    audit_formal_preconditions,
    build_plan,
)
from .journal import RunJournal
from .openai_adapter import OpenAISolAdapter
from .run_development import model_profile
from .verify_integrity import sha256


OPENAI_MODEL_ID = "gpt-5.6-sol"
OPENAI_ENDPOINT = "https://api.openai.com/v1/chat/completions"
OPENAI_KEY_ENV = "MICEPLAN_OPENAI_API_KEY"
OPENAI_KEYCHAIN_SERVICE = "MICEPLAN_OPENAI_API_KEY"
EXTENSION_MANIFEST = DATA / "openai_extension_protocol_manifest_2026-09-01.json"
REHEARSALS = DATA / "formal_rehearsals"


def verify_openai_extension_manifest() -> list[str]:
    if not EXTENSION_MANIFEST.exists():
        return [f"{EXTENSION_MANIFEST.name}: missing"]
    manifest = json.loads(EXTENSION_MANIFEST.read_text(encoding="utf-8"))
    failures: list[str] = []
    if manifest.get("status") != "reviewer-extension-frozen-before-openai-held-out-calls":
        failures.append("OpenAI extension protocol is not frozen")
    for item in manifest.get("files", []):
        path = ROOT / item["path"]
        if not path.exists():
            failures.append(f"{item['path']}: missing")
        elif sha256(path) != item["sha256"]:
            failures.append(f"{item['path']}: hash mismatch")
    return failures


def audit_openai_preconditions() -> dict[str, Any]:
    preflight = audit_formal_preconditions()
    failures = verify_openai_extension_manifest()
    if failures:
        raise RuntimeError("OpenAI extension integrity audit failed: " + "; ".join(failures))
    freeze_record = ROOT / "paper" / "experiments" / "miceplan_lab" / "THIRD_MODEL_FREEZE_2026-09-01.md"
    if not freeze_record.exists():
        raise RuntimeError("Third-model freeze record is missing")
    return {
        **preflight,
        "extension_status": "PASS",
        "extension_manifest_sha256": file_sha256(EXTENSION_MANIFEST),
        "openai_held_out_calls_before_rehearsal": False,
    }


def build_openai_plan(track: str, run_id: str) -> dict[str, Any]:
    plan = build_plan(track, "kimi", run_id)
    profile = model_profile(OPENAI_MODEL_ID)
    plan.update(
        {
            "protocol_version": "miceplan-lab-validation-recovery-v1.2-openai-extension-2026-09-01",
            "provider_key": "openai",
            "provider": "OpenAI API",
            "endpoint": os.getenv("MICEPLAN_OPENAI_ENDPOINT", OPENAI_ENDPOINT),
            "model_id": OPENAI_MODEL_ID,
            "access_date": date.today().isoformat(),
            "decoding": {
                **profile,
                "semantic_repair_limit": 3,
                "output_contract": "provider-enforced response_format strict JSON Schema",
            },
            "pricing_file": "PRICING_OPENAI_GPT56_SOL_2026-09-01.json",
            "extension_manifest_hash": file_sha256(EXTENSION_MANIFEST),
        }
    )
    return plan


def _write_openai_rehearsal(plans: list[dict[str, Any]], preflight: dict[str, Any]) -> Path:
    REHEARSALS.mkdir(parents=True, exist_ok=True)
    track_scope = "all-tracks" if len(plans) == 2 else plans[0]["experiment_track"].removeprefix("formal_")
    path = REHEARSALS / f"formal_zero_call_rehearsal_openai-{track_scope}_{date.today().isoformat()}.json"
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


def _adapter_factory() -> Callable[[], OpenAISolAdapter]:
    api_key = resolve_api_key(OPENAI_KEY_ENV, keychain_service=OPENAI_KEYCHAIN_SERVICE)
    profile = model_profile(OPENAI_MODEL_ID)

    def create() -> OpenAISolAdapter:
        return OpenAISolAdapter(
            endpoint=os.getenv("MICEPLAN_OPENAI_ENDPOINT", OPENAI_ENDPOINT),
            api_key=api_key,
            model=OPENAI_MODEL_ID,
            temperature=profile["temperature"],
            max_output_tokens=int(profile["max_output_tokens"]),
            max_tokens_parameter=str(profile["max_tokens_parameter"]),
            extra_request_parameters=dict(profile["extra_request_parameters"]),
        )

    return create


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare or execute the frozen GPT-5.6 Sol extension")
    parser.add_argument("--track", choices=("natural", "seeded", "all"), default="all")
    parser.add_argument("--run-id", help="Override a single OpenAI formal run identifier")
    parser.add_argument("--execute", action="store_true", help="Actually send held-out OpenAI requests")
    args = parser.parse_args()

    preflight = audit_openai_preconditions()
    tracks = ("natural", "seeded") if args.track == "all" else (args.track,)
    plans = [
        build_openai_plan(track, args.run_id or f"formal-{track}-openai-v1-2-extension")
        for track in tracks
    ]
    if not args.execute:
        path = _write_openai_rehearsal(plans, preflight)
        aggregate = {
            "runs": len(plans),
            "jobs": sum(plan["expected"]["jobs"] for plan in plans),
            "policy_outcomes": sum(plan["expected"]["policy_outcomes"] for plan in plans),
            "minimum_model_calls": sum(plan["expected"]["minimum_model_calls"] for plan in plans),
            "maximum_model_calls": sum(plan["expected"]["maximum_model_calls"] for plan in plans),
        }
        print(json.dumps({"status": "PASS", "model_calls_made": 0, "rehearsal": str(path), "aggregate": aggregate}, indent=2))
        return

    if args.track == "all" or len(plans) != 1:
        raise RuntimeError("OpenAI formal execution requires exactly one --track")
    plan = plans[0]
    factory = _adapter_factory()
    journal = RunJournal(RUNS / plan["run_id"], plan)
    _mark_formal_execution_started(plan["run_id"], args.track, "openai")
    if args.track == "natural":
        counts = ExperimentExecutor(
            data_directory=DATA,
            journal=journal,
            adapter_factory=factory,
            max_semantic_repairs=3,
            progress_callback=lambda position, total, request_id, replicate_id: print(
                f"[{position}/{total}] {request_id} replicate={replicate_id} completed",
                flush=True,
            ),
        ).run()
    else:
        counts = _run_seeded(plan, journal, factory)
    print(json.dumps({"run_id": plan["run_id"], "status": "complete-or-safely-resumed", "journal": counts}, indent=2))


if __name__ == "__main__":
    main()
