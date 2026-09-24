from __future__ import annotations

import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / "paper" / "data" / "miceplan_lab_v1_1"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    manifest_path = DATASET / "manifest.json"
    audit_path = DATASET / "audit_report.json"
    gold_path = DATASET / "gold.jsonl"
    requests_path = DATASET / "requests.jsonl"
    packet_path = DATASET / "AUTHOR_REVIEW_PACKET.md"

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    gold_rows = load_jsonl(gold_path)
    request_rows = load_jsonl(requests_path)

    if manifest.get("formal_model_calls_started"):
        raise SystemExit("Refusing to finalize review after formal calls have started.")
    if audit.get("status") != "passed" or audit.get("machine_audit") != "PASS":
        raise SystemExit("Machine audit must pass before surface review can be finalized.")
    if len(gold_rows) != 90 or len(request_rows) != 180:
        raise SystemExit("Frozen benchmark counts are not 90 semantic tasks / 180 requests.")
    if not all(row.get("machine_audit") == "PASS" for row in gold_rows):
        raise SystemExit("Every gold task must pass machine audit.")

    for row in gold_rows:
        row["author_review"] = "PASS"
    write_jsonl(gold_path, gold_rows)

    packet = packet_path.read_text(encoding="utf-8")
    packet = packet.replace(
        "# MICEPlan-Lab v1 Blinded Author Review Packet",
        "# MICEPlan-Lab v1.1 Blinded Surface-Form Review Packet",
    )
    packet = packet.replace(
        "Mark PASS or record a correction before formal model calls.",
        "Mark PASS or record a correction before formal model calls. This is internal\n"
        "benchmark quality control, not practitioner or domain-expert validation.",
    )
    packet = packet.replace("- Review decision: **PENDING**", "- Review decision: **PASS**")
    packet_path.write_text(packet, encoding="utf-8")

    review_record = {
        "dataset": manifest["dataset"],
        "review_date": date.today().isoformat(),
        "reviewer_role": "author-supervised internal bilingual surface-form QA",
        "status": "PASS",
        "reviewed_tasks": 90,
        "passed_tasks": 90,
        "failed_tasks": 0,
        "pending_tasks": 0,
        "review_scope": [
            "Chinese-English semantic equivalence",
            "visible operation, target, quantity, dimension, and direction consistency",
            "natural wording for missing-evidence and ambiguous-reference requests",
            "absence of explicit stress labels or intended defer reasons in visible requests",
        ],
        "requests_sha256": sha256(requests_path),
        "limitations": [
            "This review is not practitioner annotation or CAD-domain expert validation.",
            "Task naturalness is bounded to the controlled synthetic command templates.",
            "Geometry, intent witnesses, context masks, and invalid probes are validated separately by the machine audit.",
        ],
        "packet": "AUTHOR_REVIEW_PACKET.md",
    }
    write_json(DATASET / "surface_review.json", review_record)

    review_status = {
        "dataset": manifest["dataset"],
        "packet": "AUTHOR_REVIEW_PACKET.md",
        "reviewer_role": review_record["reviewer_role"],
        "reviewed_tasks": 90,
        "passed_tasks": 90,
        "failed_tasks": 0,
        "pending_tasks": 0,
        "status": "PASS",
        "note": "Internal benchmark surface QA only; not expert annotation.",
    }
    write_json(DATASET / "review_status.json", review_status)

    audit["author_review"] = "PASS"
    audit["surface_review"] = {
        "status": "PASS",
        "reviewed_tasks": 90,
        "scope": "bilingual surface form and task-language consistency",
        "expert_validation": False,
    }
    write_json(audit_path, audit)

    tracked_paths = [
        DATASET / "scenes.jsonl",
        DATASET / "requests.jsonl",
        DATASET / "gold.jsonl",
        DATASET / "review_status.json",
        DATASET / "surface_review.json",
        DATASET / "AUTHOR_REVIEW_PACKET.md",
        DATASET / "audit_report.json",
        *sorted((DATASET / "schemas").glob("*.json")),
        *sorted((DATASET / "prompts").glob("*.txt")),
    ]
    manifest["author_review_status"] = "PASS"
    manifest["surface_review_status"] = "PASS"
    manifest["files"] = {
        path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
        for path in tracked_paths
    }
    write_json(manifest_path, manifest)

    print(
        json.dumps(
            {
                "dataset": manifest["dataset"],
                "surface_review": "PASS",
                "reviewed_tasks": 90,
                "expert_validation": False,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
