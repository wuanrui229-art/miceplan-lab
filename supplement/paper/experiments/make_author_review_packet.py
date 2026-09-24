from __future__ import annotations

import json
import os
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATASET = ROOT / "data" / os.getenv("MICEPLAN_DATASET_DIR", "miceplan_eval_v1_1")
OUTPUT = DATASET / "AUTHOR_REVIEW_PACKET.md"
TEST_QUOTAS = {"simple": 8, "capacity_stress": 4, "compound": 4, "ambiguous": 4, "contradictory": 4, "revision": 4, "protected_object": 4}


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def operation_summary(operation: dict) -> str:
    fields = [operation["type"]]
    if operation["target_ids"]:
        fields.append("targets=" + ",".join(operation["target_ids"]))
    for key in ("count", "width", "height", "x", "y", "region", "booth_type"):
        if operation[key] is not None:
            fields.append(f"{key}={operation[key]}")
    return "; ".join(fields)


def main() -> None:
    manifest = json.loads((DATASET / "manifest.json").read_text(encoding="utf-8"))
    rows = load_jsonl(DATASET / "requests.jsonl")
    development = [row for row in rows if row["split"] == "development"]
    test_by_category: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        if row["split"] == "test":
            test_by_category[row["category"]].append(row)
    selected_test: list[dict] = []
    for category, quota in TEST_QUOTAS.items():
        candidates = sorted(test_by_category[category], key=lambda row: (row["language"], row["request_id"]))
        english = [row for row in candidates if row["language"] == "en"][: quota // 2]
        chinese = [row for row in candidates if row["language"] == "zh"][: quota - len(english)]
        selected_test.extend(english + chinese)
    selected = development + sorted(selected_test, key=lambda row: row["request_id"])
    assert len(development) == 32
    assert len(selected_test) == 32

    lines = [
        f"# {manifest['dataset']} author review packet",
        "",
        "Review status: **not started**. Checking a box is not sufficient; if an item is corrected, update `requests.jsonl`, regenerate the manifest hash, and record the reason.",
        "",
        "This packet contains all 32 development requests and a balanced 32-request test sample.",
        "",
    ]
    for position, row in enumerate(selected, 1):
        ir = row["gold_ir"]
        lines.extend(
            [
                f"## {position}. {row['request_id']} · {row['split']} · {row['language']} · {row['category']}",
                "",
                f"- Hall: `{row['hall_id']}`",
                f"- Request: {row['text']}",
                f"- Expected state: `{row['expected_pipeline_state']}`",
                f"- Requires confirmation: `{str(ir['requires_confirmation']).lower()}`",
                f"- Operations: {(' | '.join(operation_summary(operation) for operation in ir['operations'])) or 'none'}",
                f"- Unresolved references: {(', '.join(ir['unresolved_references'])) or 'none'}",
                f"- Assumptions: {(', '.join(ir['assumptions'])) or 'none'}",
                "- Decision: [ ] accepted  [ ] corrected  [ ] excluded",
                "- Reviewer name/role: ",
                "- Review notes: ",
                "",
            ]
        )
    OUTPUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(selected)} review items to {OUTPUT}")


if __name__ == "__main__":
    main()
