from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "paper" / "data" / "miceplan_lab_v1_1" / "runs"
FORMAL_RUNS = (
    "formal-natural-kimi-v1-2",
    "formal-natural-deepseek-v1-2",
    "formal-natural-openai-v1-2-extension",
    "formal-seeded-kimi-v1-2",
    "formal-seeded-deepseek-v1-2",
    "formal-seeded-openai-v1-2-extension",
)
JOURNALS = (
    "calls.jsonl",
    "gate_events.jsonl",
    "outcomes.jsonl",
    "infrastructure_errors.jsonl",
)


def canonical_json(value) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def digest(value) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def verify(path: Path) -> int:
    previous = "GENESIS"
    count = 0
    with path.open(encoding="utf-8") as handle:
        for expected_sequence, line in enumerate(handle):
            if not line.strip():
                continue
            envelope = json.loads(line)
            core = {
                "sequence": expected_sequence,
                "previous_sha256": previous,
                "payload": envelope.get("payload"),
            }
            if envelope.get("sequence") != expected_sequence:
                raise AssertionError(f"{path}: non-contiguous sequence")
            if envelope.get("previous_sha256") != previous:
                raise AssertionError(f"{path}: broken previous hash")
            expected_hash = digest(core)
            if envelope.get("record_sha256") != expected_hash:
                raise AssertionError(f"{path}: record hash mismatch")
            previous = expected_hash
            count += 1
    return count


def main() -> None:
    checked = 0
    records = 0
    for run_name in FORMAL_RUNS:
        run = RUNS / run_name
        if not run.is_dir():
            raise FileNotFoundError(run)
        for journal_name in JOURNALS:
            path = run / journal_name
            if not path.exists():
                continue
            count = verify(path)
            checked += 1
            records += count
            print(f"PASS  {run_name}/{journal_name}: {count} records")
    print(f"PASS: verified {checked} journals containing {records} records.")


if __name__ == "__main__":
    main()

