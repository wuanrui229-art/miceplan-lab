from __future__ import annotations

import json
import unittest
from collections import Counter
from pathlib import Path


DATASET = Path(__file__).resolve().parents[3] / "data" / "miceplan_lab_v1_1"


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class FrozenBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = load_jsonl(DATASET / "scenes.jsonl")
        cls.requests = load_jsonl(DATASET / "requests.jsonl")
        cls.gold = load_jsonl(DATASET / "gold.jsonl")
        cls.audit = json.loads((DATASET / "audit_report.json").read_text(encoding="utf-8"))

    def test_frozen_counts(self):
        self.assertEqual((len(self.scenes), len(self.gold), len(self.requests)), (8, 90, 180))
        self.assertEqual(Counter(row["split"] for row in self.scenes), Counter({"development": 2, "test": 6}))
        self.assertEqual(Counter(row["split"] for row in self.requests), Counter({"development": 36, "test": 144}))

    def test_every_task_has_bilingual_pair(self):
        by_task: dict[str, set[str]] = {}
        for row in self.requests:
            by_task.setdefault(row["semantic_task_id"], set()).add(row["language"])
        self.assertEqual(len(by_task), 90)
        self.assertTrue(all(languages == {"zh", "en"} for languages in by_task.values()))

    def test_machine_audit_and_internal_surface_review_passed(self):
        self.assertEqual(self.audit["status"], "passed")
        self.assertTrue(all(row["machine_audit"] == "PASS" for row in self.gold))
        self.assertTrue(all(row["author_review"] == "PASS" for row in self.gold))
        self.assertEqual(self.audit["surface_review"]["expert_validation"], False)

    def test_unknown_tasks_have_no_hidden_solution(self):
        unknown = [row for row in self.gold if row["target_stress_class"] in {"AMBIGUOUS_TARGET", "MISSING_EVIDENCE"}]
        self.assertEqual(len(unknown), 24)
        self.assertTrue(all(row["admissible_final_outcome"] == "DEFER" for row in unknown))
        self.assertTrue(all(row["valid_witness_ir"] is None and row["invalid_probe_ir"] is None for row in unknown))

    def test_deterministic_stress_tasks_have_probes(self):
        deterministic = [row for row in self.gold if row["target_stress_class"] in {"BOUNDARY", "OVERLAP", "PROTECTED_POLYGON", "LOCKED_MUTATION"}]
        self.assertEqual(len(deterministic), 42)
        self.assertTrue(all(row["invalid_probe_ir"] is not None for row in deterministic))


if __name__ == "__main__":
    unittest.main()
