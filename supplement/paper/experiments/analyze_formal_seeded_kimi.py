from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from miceplan_lab import analyze_seeded_run


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
RUN = Path(
    os.environ.get(
        "MICEPLAN_SEEDED_RUN",
        str(DATA / "runs" / "formal-seeded-kimi-v1-2"),
    )
)
PRICING = Path(
    os.environ.get(
        "MICEPLAN_SEEDED_PRICING",
        str(
            ROOT
            / "paper"
            / "experiments"
            / "miceplan_lab"
            / "PRICING_KIMI_K27_HIGHSPEED_2026-07-21.json"
        ),
    )
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    manifest = json.loads((RUN / "run_manifest.json").read_text(encoding="utf-8"))
    source_hashes = manifest["source_hashes"]
    seed_paths = (
        DATA / "fault_seeds_v1_2.jsonl",
        DATA / "fault_seeds_composite_v1_2.jsonl",
    )
    for path in seed_paths:
        expected = source_hashes[path.name]
        observed = sha256(path)
        if observed != expected:
            raise RuntimeError(f"Frozen seed hash mismatch: {path.name}")

    original_load_jsonl = analyze_seeded_run.load_jsonl

    def load_jsonl_with_composites(path: Path) -> list[dict]:
        rows = original_load_jsonl(path)
        if path.name != "fault_seeds_v1_2.jsonl":
            return rows
        composite_rows = original_load_jsonl(path.with_name("fault_seeds_composite_v1_2.jsonl"))
        identifiers = [row["seed_id"] for row in (*rows, *composite_rows)]
        if len(identifiers) != len(set(identifiers)):
            raise RuntimeError("Duplicate seed IDs across frozen seed files")
        return [*rows, *composite_rows]

    analyze_seeded_run.load_jsonl = load_jsonl_with_composites
    pricing = json.loads(PRICING.read_text(encoding="utf-8"))
    result = analyze_seeded_run.analyze(RUN, DATA, pricing)

    scheduled = set(manifest["scheduled_seed_ids"])
    observed = set(result["completion"]["heldout_seed_ids_observed"])
    if observed != scheduled:
        raise RuntimeError("Analyzed seed IDs do not exactly match the frozen schedule")

    (RUN / "seeded_analysis.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    markdown = analyze_seeded_run.render_markdown(result).replace(
        "This development pilot estimates conditional recovery from transparent, "
        "intent-preserving injected failures. It does not estimate how often the LLM naturally "
        "creates those failures, and it must not be pooled with held-out results.",
        "This formal held-out seeded-recovery experiment estimates conditional recovery from "
        "transparent, intent-preserving injected failures. It does not estimate how often the "
        "LLM naturally creates those failures and should be analyzed separately from Track N.",
    )
    (RUN / "seeded_analysis.md").write_text(markdown, encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
