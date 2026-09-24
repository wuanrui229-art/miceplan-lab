from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .execution import file_sha256, load_jsonl


ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "paper" / "data" / "miceplan_lab_v1_1"
OUTPUT = DATA / "formal_selection_v1_2.json"
SELECTION_VERSION = "miceplan-lab-formal-selection-v1.2"


def _stable_rank(value: str) -> str:
    return hashlib.sha256(f"20260721:{value}".encode("utf-8")).hexdigest()


def _balanced_one_per_task(
    rows: list[dict[str, Any]], label_key: str
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[row["semantic_task_id"]].append(row)
    label_counts: dict[str, int] = defaultdict(int)
    selected: list[dict[str, Any]] = []
    for task_id in sorted(grouped, key=_stable_rank):
        candidates = grouped[task_id]
        chosen = min(
            candidates,
            key=lambda row: (
                label_counts[str(row[label_key])],
                _stable_rank(row["seed_id"]),
            ),
        )
        selected.append(chosen)
        label_counts[str(chosen[label_key])] += 1
    return sorted(selected, key=lambda row: row["seed_id"])


def _one_task_per_operation_complexity(tasks: list[dict[str, Any]]) -> list[str]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in tasks:
        family = row.get("operation_family", row.get("intended_operation_family"))
        grouped[(str(family), row["complexity"])].append(row)
    selected = [
        min(rows, key=lambda row: _stable_rank(row["semantic_task_id"]))["semantic_task_id"]
        for _, rows in sorted(grouped.items())
    ]
    return sorted(selected)


def _one_seed_per_operation_complexity(rows: list[dict[str, Any]]) -> list[str]:
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[(row["operation_family"], row["complexity"])].append(row)
    return sorted(
        min(values, key=lambda row: _stable_rank(row["seed_id"]))["seed_id"]
        for _, values in sorted(grouped.items())
    )


def build_selection() -> dict[str, Any]:
    requests = load_jsonl(DATA / "requests.jsonl")
    gold = load_jsonl(DATA / "gold.jsonl")
    single = load_jsonl(DATA / "fault_seeds_v1_2.jsonl")
    composite = load_jsonl(DATA / "fault_seeds_composite_v1_2.jsonl")

    test_requests = [row for row in requests if row["split"] == "test"]
    test_task_ids = {row["semantic_task_id"] for row in test_requests}
    test_gold = [row for row in gold if row["semantic_task_id"] in test_task_ids]
    test_single = [row for row in single if row["split"] == "test"]
    test_composite = [
        {**row, "rule_set": "+".join(row["rule_ids"])}
        for row in composite
        if row["split"] == "test" and row["fault_cardinality"] == 2
    ]

    selected_single = _balanced_one_per_task(test_single, "rule_id")
    selected_composite = _balanced_one_per_task(test_composite, "rule_set")
    selected_all = selected_single + selected_composite
    return {
        "selection_version": SELECTION_VERSION,
        "created_before_formal_calls": True,
        "selection_seed": 20260721,
        "source_hashes": {
            "requests.jsonl": file_sha256(DATA / "requests.jsonl"),
            "gold.jsonl": file_sha256(DATA / "gold.jsonl"),
            "fault_seeds_v1_2.jsonl": file_sha256(DATA / "fault_seeds_v1_2.jsonl"),
            "fault_seeds_composite_v1_2.jsonl": file_sha256(
                DATA / "fault_seeds_composite_v1_2.jsonl"
            ),
        },
        "natural_incidence": {
            "semantic_task_ids": sorted({row["semantic_task_id"] for row in test_requests}),
            "request_ids": sorted(row["request_id"] for row in test_requests),
            "full_replicate_ids": [1],
            "repeat_subset_semantic_task_ids": _one_task_per_operation_complexity(test_gold),
            "repeat_subset_additional_replicate_ids": [2, 3],
        },
        "seeded_conditional_recovery": {
            "single_fault_seed_ids": [row["seed_id"] for row in selected_single],
            "composite_fault_seed_ids": [row["seed_id"] for row in selected_composite],
            "selected_seed_count": len(selected_all),
            "bilingual_jobs_per_full_replicate": 2 * len(selected_all),
            "full_replicate_ids": [1],
            "repeat_subset_seed_ids": sorted(
                _one_seed_per_operation_complexity(selected_single)
                + _one_seed_per_operation_complexity(selected_composite)
            ),
            "repeat_subset_additional_replicate_ids": [2, 3],
            "selection_rule": (
                "One available single fault per eligible held-out semantic task and one available "
                "two-rule composite fault per eligible held-out semantic task; greedy balancing "
                "by rule or rule set with SHA-256 tie-breaking. Protocol v1.2 admits the additional "
                "intent-preserving C3 seeds enabled by the repaired benchmark. Three-rule seeds are "
                "excluded from the primary formal sample and reserved for sensitivity analysis."
            ),
        },
    }


def audit(selection: dict[str, Any]) -> None:
    natural = selection["natural_incidence"]
    seeded = selection["seeded_conditional_recovery"]
    if len(natural["semantic_task_ids"]) != 72 or len(natural["request_ids"]) != 144:
        raise AssertionError("Natural held-out selection must contain 72 tasks / 144 requests")
    if len(natural["repeat_subset_semantic_task_ids"]) != 18:
        raise AssertionError("Natural repeat subset must contain one task per operation-complexity cell")
    if seeded["selected_seed_count"] != 63:
        raise AssertionError("Seeded formal selection must contain 36 single + 27 composite seeds")
    if seeded["bilingual_jobs_per_full_replicate"] != 126:
        raise AssertionError("Seeded formal selection must contain 126 bilingual jobs per full replicate")
    if len(seeded["repeat_subset_seed_ids"]) != 21:
        raise AssertionError("Seeded repeats must cover each available operation-complexity cell per track")


def main() -> None:
    selection = build_selection()
    audit(selection)
    OUTPUT.write_text(
        json.dumps(selection, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "natural_tasks": len(selection["natural_incidence"]["semantic_task_ids"]),
                "natural_requests": len(selection["natural_incidence"]["request_ids"]),
                "natural_repeat_tasks": len(
                    selection["natural_incidence"]["repeat_subset_semantic_task_ids"]
                ),
                "seeded_seeds": selection["seeded_conditional_recovery"]["selected_seed_count"],
                "seeded_bilingual_jobs": selection["seeded_conditional_recovery"][
                    "bilingual_jobs_per_full_replicate"
                ],
                "seeded_repeat_seeds": len(
                    selection["seeded_conditional_recovery"]["repeat_subset_seed_ids"]
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
