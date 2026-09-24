from __future__ import annotations

import argparse
import os
from datetime import date
from pathlib import Path

from .credentials import resolve_api_key
from .execution import ExperimentExecutor, build_run_manifest, load_jsonl
from .journal import RunJournal
from .live_adapter import DeepSeekStrictToolAdapter, OpenAICompatibleModelAdapter
from .openai_adapter import OpenAISolAdapter


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
DEFAULT_RUNS = DATA / "runs"


def load_local_env(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def model_profile(model: str) -> dict[str, object]:
    """Return provider-compatible, manifest-ready decoding controls."""

    if model.startswith("kimi-k2.7-code"):
        return {
            "temperature": 1.0,
            "max_output_tokens": 32768,
            "max_tokens_parameter": "max_tokens",
            "extra_request_parameters": {},
        }
    if model == "kimi-k3":
        return {
            "temperature": None,
            "max_output_tokens": 4096,
            "max_tokens_parameter": "max_completion_tokens",
            "extra_request_parameters": {"reasoning_effort": "low"},
        }
    if model in {"kimi-k2.6", "kimi-k2.5"}:
        return {
            "temperature": None,
            "max_output_tokens": 2048,
            "max_tokens_parameter": "max_tokens",
            "extra_request_parameters": {"thinking": {"type": "disabled"}},
        }
    if model.startswith("deepseek-v4"):
        return {
            "temperature": None,
            "max_output_tokens": 32768,
            "max_tokens_parameter": "max_tokens",
            "extra_request_parameters": {"thinking": {"type": "disabled"}},
        }
    if model == "gpt-5.6-sol":
        return {
            "temperature": None,
            "max_output_tokens": 32768,
            "max_tokens_parameter": "max_completion_tokens",
            "extra_request_parameters": {"reasoning_effort": "none", "store": False},
        }
    return {
        "temperature": float(os.getenv("MICEPLAN_LLM_TEMPERATURE", "0")),
        "max_output_tokens": 2048,
        "max_tokens_parameter": "max_tokens",
        "extra_request_parameters": {},
    }


def select_development_requests(
    all_requests: list[dict[str, object]], request_ids: list[str] | None, limit: int
) -> list[dict[str, object]]:
    development = {
        str(row["request_id"]): row for row in all_requests if row["split"] == "development"
    }
    if request_ids:
        missing = [request_id for request_id in request_ids if request_id not in development]
        if missing:
            raise ValueError(f"Unknown or non-development request IDs: {', '.join(missing)}")
        if len(request_ids) != len(set(request_ids)):
            raise ValueError("Duplicate request IDs are not allowed")
        return [development[request_id] for request_id in request_ids]
    return [development[key] for key in sorted(development)[:limit]]


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a development-only MICEPlan-Lab provider pilot")
    parser.add_argument("--provider", choices=("kimi", "deepseek", "openai"), default="kimi")
    parser.add_argument("--execute", action="store_true", help="Actually send provider requests")
    parser.add_argument("--limit", type=int, default=36)
    parser.add_argument("--replicates", type=int, default=1)
    parser.add_argument("--seed", type=int, default=20260720)
    parser.add_argument("--run-id", default=f"kimi-development-{date.today().isoformat()}")
    parser.add_argument("--model", help="Override MICEPLAN_LLM_MODEL for this development run")
    parser.add_argument("--request-ids", help="Comma-separated frozen development request IDs")
    parser.add_argument("--max-semantic-repairs", type=int, default=3)
    args = parser.parse_args()

    load_local_env(ROOT / "paper" / "system" / ".env")
    requested_ids = [value.strip() for value in (args.request_ids or "").split(",") if value.strip()]
    requests = select_development_requests(load_jsonl(DATA / "requests.jsonl"), requested_ids or None, args.limit)
    keychain_service = None
    if args.provider == "deepseek":
        endpoint = os.getenv(
            "MICEPLAN_DEEPSEEK_ENDPOINT",
            "https://api.deepseek.com/beta/chat/completions",
        )
        api_key_name = "MICEPLAN_DEEPSEEK_API_KEY"
        model_id = args.model or os.getenv("MICEPLAN_DEEPSEEK_MODEL", "deepseek-v4-pro")
        provider_name = "DeepSeek Open Platform / strict-tool beta"
        output_contract = "provider-enforced strict function tool JSON Schema (beta)"
        adapter_class = DeepSeekStrictToolAdapter
    elif args.provider == "openai":
        endpoint = os.getenv(
            "MICEPLAN_OPENAI_ENDPOINT",
            "https://api.openai.com/v1/chat/completions",
        )
        api_key_name = "MICEPLAN_OPENAI_API_KEY"
        keychain_service = "MICEPLAN_OPENAI_API_KEY"
        model_id = args.model or os.getenv("MICEPLAN_OPENAI_MODEL", "gpt-5.6-sol")
        provider_name = "OpenAI API"
        output_contract = "provider-enforced response_format strict JSON Schema"
        adapter_class = OpenAISolAdapter
    else:
        endpoint = os.getenv("MICEPLAN_LLM_ENDPOINT", "UNCONFIGURED")
        api_key_name = "MICEPLAN_LLM_API_KEY"
        model_id = args.model or os.getenv("MICEPLAN_LLM_MODEL", "UNCONFIGURED")
        provider_name = "Moonshot AI / Kimi Open Platform"
        output_contract = "provider-enforced response_format JSON Schema"
        adapter_class = OpenAICompatibleModelAdapter
    missing = []
    if endpoint == "UNCONFIGURED":
        missing.append("MICEPLAN_LLM_ENDPOINT")
    if model_id == "UNCONFIGURED":
        missing.append("MICEPLAN_LLM_MODEL")
    profile = model_profile(model_id)
    manifest = build_run_manifest(
        run_id=args.run_id,
        data_directory=DATA,
        model_id=model_id,
        provider=provider_name,
        endpoint=endpoint,
        access_date=date.today().isoformat(),
        request_ids=[row["request_id"] for row in requests],
        replicate_ids=list(range(1, args.replicates + 1)),
        seed=args.seed,
        decoding={
            **profile,
            "semantic_repair_limit": args.max_semantic_repairs,
            "output_contract": output_contract,
        },
    )
    planned = len(requests) * args.replicates
    print(f"Development jobs: {planned}; five policy outcomes per job; held-out requests: 0")
    if not args.execute:
        print("Dry run only. Add --execute to send API requests; no files or provider calls were made.")
        return
    if missing:
        raise RuntimeError(f"Missing LLM configuration: {', '.join(missing)}")
    api_key = resolve_api_key(api_key_name, keychain_service=keychain_service)

    run_directory = DEFAULT_RUNS / args.run_id
    journal = RunJournal(run_directory, manifest)

    def adapter_factory() -> OpenAICompatibleModelAdapter:
        return adapter_class(
            endpoint=endpoint,
            api_key=api_key,
            model=model_id,
            temperature=profile["temperature"],
            max_output_tokens=int(profile["max_output_tokens"]),
            max_tokens_parameter=str(profile["max_tokens_parameter"]),
            extra_request_parameters=dict(profile["extra_request_parameters"]),
        )

    counts = ExperimentExecutor(
        data_directory=DATA,
        journal=journal,
        adapter_factory=adapter_factory,
        max_semantic_repairs=args.max_semantic_repairs,
        progress_callback=lambda position, total, request_id, replicate_id: print(
            f"[{position}/{total}] {request_id} replicate={replicate_id} completed", flush=True
        ),
    ).run()
    print(f"Development run complete or safely resumed: {counts}")


if __name__ == "__main__":
    main()
