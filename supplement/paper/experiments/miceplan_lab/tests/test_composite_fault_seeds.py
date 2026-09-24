from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from miceplan_lab.oracle import apply_ir, intent_signature_correct


DATA = Path(__file__).resolve().parents[3] / "data" / "miceplan_lab_v1_1"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class CompositeFaultSeedTests(unittest.TestCase):
    def test_composite_seeds_are_intent_preserving_and_exact(self) -> None:
        scenes = {row["scene_id"]: row for row in load_jsonl(DATA / "scenes.jsonl")}
        gold = {row["semantic_task_id"]: row for row in load_jsonl(DATA / "gold.jsonl")}
        seeds = load_jsonl(DATA / "fault_seeds_composite_v1_2.jsonl")
        self.assertGreater(len(seeds), 0)
        for seed in seeds:
            scene = scenes[seed["scene_id"]]
            item = gold[seed["semantic_task_id"]]
            self.assertTrue(intent_signature_correct(scene, item, seed["ir"]), seed["seed_id"])
            result = apply_ir(scene, seed["ir"])
            self.assertEqual(result.status, "FAIL", seed["seed_id"])
            self.assertEqual(list(result.rule_ids), seed["rule_ids"], seed["seed_id"])
            self.assertEqual(len(result.rule_ids), seed["fault_cardinality"])


if __name__ == "__main__":
    unittest.main()
