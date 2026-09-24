from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any


DATA = Path(__file__).resolve().parents[3] / "data" / "miceplan_lab_v1_1"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class FormalSelectionTests(unittest.TestCase):
    def test_selection_counts_and_heldout_isolation(self) -> None:
        selection = json.loads((DATA / "formal_selection_v1_2.json").read_text(encoding="utf-8"))
        requests = {row["request_id"]: row for row in load_jsonl(DATA / "requests.jsonl")}
        seeds = {
            row["seed_id"]: row
            for path in ("fault_seeds_v1_2.jsonl", "fault_seeds_composite_v1_2.jsonl")
            for row in load_jsonl(DATA / path)
        }
        natural = selection["natural_incidence"]
        seeded = selection["seeded_conditional_recovery"]
        self.assertEqual(len(natural["semantic_task_ids"]), 72)
        self.assertEqual(len(natural["request_ids"]), 144)
        self.assertEqual(len(natural["repeat_subset_semantic_task_ids"]), 18)
        self.assertTrue(all(requests[value]["split"] == "test" for value in natural["request_ids"]))
        chosen = seeded["single_fault_seed_ids"] + seeded["composite_fault_seed_ids"]
        self.assertEqual(len(chosen), 63)
        self.assertEqual(len(set(chosen)), 63)
        self.assertEqual(seeded["bilingual_jobs_per_full_replicate"], 126)
        self.assertEqual(len(seeded["repeat_subset_seed_ids"]), 21)
        self.assertTrue(all(seeds[value]["split"] == "test" for value in chosen))
        self.assertTrue(set(seeded["repeat_subset_seed_ids"]).issubset(chosen))


if __name__ == "__main__":
    unittest.main()
