from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import DATASET_VERSION, PROTOCOL_VERSION


ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
TRACKED = (
    "paper/MICEPLAN_LAB_PROTOCOL_V1.md",
    "paper/MICEPLAN_LAB_PROTOCOL_V1_2_SUPPLEMENT.md",
    "paper/MICEPLAN_LAB_PROTOCOL_REVIEW.md",
    "paper/experiments/MICEPLAN_LAB_IMPLEMENTATION_PLAN.md",
    "paper/experiments/miceplan_lab/BENCHMARK_REPAIR_REPORT_2026-07-22.md",
    "paper/experiments/miceplan_lab/SECOND_MODEL_FREEZE_2026-07-21.md",
    "paper/experiments/miceplan_lab/finalize_surface_review.py",
    "paper/experiments/miceplan_lab/freeze_formal_selection.py",
    "paper/experiments/miceplan_lab/formal_run.py",
    "paper/experiments/miceplan_lab/generate_benchmark.py",
    "paper/experiments/miceplan_lab/audit_benchmark.py",
    "paper/experiments/miceplan_lab/contracts.py",
    "paper/experiments/miceplan_lab/execution.py",
    "paper/experiments/miceplan_lab/journal.py",
    "paper/experiments/miceplan_lab/live_adapter.py",
    "paper/experiments/miceplan_lab/oracle.py",
    "paper/experiments/miceplan_lab/policy_runner.py",
    "paper/experiments/miceplan_lab/runtime_gate.py",
    "paper/experiments/miceplan_lab/seeded_runner.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    files = []
    for relative in TRACKED:
        path = ROOT / relative
        if not path.exists():
            raise FileNotFoundError(relative)
        files.append({"path": relative, "sha256": sha256(path)})
    manifest = {
        "protocol_id": "miceplan-lab-validation-recovery-v1.2",
        "protocol_version": PROTOCOL_VERSION,
        "dataset_version": DATASET_VERSION,
        "status": "benchmark-and-protocol-frozen-before-formal-calls",
        "freeze_date": "2026-07-22",
        "files": files,
        "notes": [
            "This freeze follows rejection of v1 by the complete interactive author review.",
            "No held-out or formal model call has used v1.1.",
            "The v1 benchmark and preliminary development runs remain unchanged for provenance.",
            "The repaired v1.1 task pairs passed internal bilingual surface-form QA.",
            "No practitioner or CAD-domain expert validation is claimed.",
        ],
    }
    output = DATASET / "protocol_manifest.json"
    output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"protocol_manifest": str(output), "tracked_files": len(files)}, indent=2))


if __name__ == "__main__":
    main()
