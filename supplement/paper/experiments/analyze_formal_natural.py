from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from miceplan_lab import analyze_development


def render_formal_markdown(result: dict) -> str:
    markdown = analyze_development.render_markdown(result)
    markdown = markdown.replace(
        f"# Development Audit — {result['run_id']}",
        f"# Formal Held-Out Natural-Incidence Audit — {result['run_id']}",
    )
    markdown = markdown.replace("## Primary development metrics", "## Formal policy metrics")
    markdown = markdown.replace("## Development repair diagnostics", "## Natural-failure repair diagnostics")
    markdown = markdown.replace(
        "Development metrics are diagnostic only and must not be pooled with or reported as held-out results.",
        "These are formal held-out natural-incidence results. Conditional seeded-recovery "
        "results remain a separate Track S estimand and must not be pooled into this table.",
    )
    return markdown


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit a completed formal natural-incidence run")
    parser.add_argument("run_directory", type=Path)
    parser.add_argument("--pricing", type=Path, required=True)
    parser.add_argument(
        "--data-directory",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "miceplan_lab_v1_1",
    )
    args = parser.parse_args()
    pricing = json.loads(args.pricing.read_text(encoding="utf-8"))
    manifest = json.loads(
        (args.run_directory / "run_manifest.json").read_text(encoding="utf-8")
    )
    prompt_hashes = manifest["prompt_hashes"]
    role_by_hash = {
        prompt_hashes["base_generation.txt"]: "BASE",
        prompt_hashes["constraint_generation.txt"]: "CONSTRAINT",
        prompt_hashes["repair.txt"]: "RULE_REPAIR",
        prompt_hashes["blind_retry.txt"]: "BLIND_RETRY",
    }

    def classify_frozen_prompt(prompt: str) -> str:
        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        if digest not in role_by_hash:
            raise RuntimeError(f"Unrecognized prompt hash in formal run: {digest}")
        return role_by_hash[digest]

    # The frozen development renderer checks the generic substring "generation prompt"
    # before "constraint-in-prompt", so a constraint prompt is otherwise misclassified as
    # BASE. Exact frozen hashes are unambiguous and do not change any metric definition.
    analyze_development.classify_call = classify_frozen_prompt
    result = analyze_development.analyze(args.run_directory, args.data_directory, pricing)
    result["completion"]["unique_scheduled_request_ids"] = result["completion"].pop(
        "scheduled_requests"
    )
    result["completion"]["scheduled_jobs"] = int(manifest["expected"]["jobs"])
    result["completion"]["expected_policy_outcomes"] = int(
        manifest["expected"]["policy_outcomes"]
    )
    if result["completion"]["recorded_policy_outcomes"] != int(
        manifest["expected"]["policy_outcomes"]
    ):
        raise RuntimeError("Recorded policy outcomes do not match the frozen run manifest")
    (args.run_directory / "natural_analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (args.run_directory / "natural_analysis.md").write_text(
        render_formal_markdown(result),
        encoding="utf-8",
    )
    print(json.dumps(result["completion"], ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
