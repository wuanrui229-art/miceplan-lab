from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from miceplan_lab.oracle import (
    apply_ir,
    correct_defer,
    intent_signature_correct,
    validate_candidate,
)


DATASET = Path(__file__).resolve().parents[3] / "data" / "miceplan_lab_v1_1"


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class IndependentOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = load_jsonl(DATASET / "scenes.jsonl")[0]

    def test_clean_source_passes(self):
        result = validate_candidate(self.scene, copy.deepcopy(self.scene))
        self.assertEqual(result.status, "PASS")

    def test_touching_edges_are_not_interior_overlap(self):
        candidate = copy.deepcopy(self.scene)
        first, second = candidate["booths"][2], candidate["booths"][3]
        second["x"] = first["x"] + first["width"]
        second["y"] = first["y"]
        result = validate_candidate(self.scene, candidate)
        self.assertNotIn("OVERLAP", result.rule_ids)

    def test_positive_area_overlap_is_detected(self):
        candidate = copy.deepcopy(self.scene)
        first, second = candidate["booths"][2], candidate["booths"][3]
        second["x"] = first["x"] + first["width"] - 0.25
        second["y"] = first["y"]
        result = validate_candidate(self.scene, candidate)
        self.assertEqual(result.status, "FAIL")
        self.assertIn("OVERLAP", result.rule_ids)

    def test_boundary_violation_is_detected(self):
        candidate = copy.deepcopy(self.scene)
        candidate["booths"][2]["x"] = -0.01
        result = validate_candidate(self.scene, candidate)
        self.assertIn("BOUNDARY", result.rule_ids)

    def test_protected_polygon_collision_is_detected(self):
        candidate = copy.deepcopy(self.scene)
        obstacle = candidate["obstacles"][0]["polygon"][0]
        candidate["booths"][2]["x"] = obstacle[0]
        candidate["booths"][2]["y"] = obstacle[1]
        result = validate_candidate(self.scene, candidate)
        self.assertIn("PROTECTED_POLYGON", result.rule_ids)

    def test_locked_mutation_is_detected(self):
        candidate = copy.deepcopy(self.scene)
        locked = next(booth for booth in candidate["booths"] if booth["status"] == "locked")
        locked["x"] += 0.5
        result = validate_candidate(self.scene, candidate)
        self.assertIn("LOCKED_MUTATION", result.rule_ids)

    def test_missing_target_returns_unknown(self):
        ir = {
            "request_id": "test-missing-target",
            "source_layout_version": "v1",
            "language": "en",
            "operations": [{
                "type": "MOVE_BOOTH", "target_ids": ["absent"], "count": None,
                "width": None, "height": None, "x": 2, "y": 2,
                "region": None, "booth_type": None,
            }],
            "hard_constraints": [], "preferences": [], "assumptions": [],
            "unresolved_references": [], "requires_confirmation": False,
        }
        result = apply_ir(self.scene, ir)
        self.assertEqual(result.status, "UNKNOWN")
        self.assertIn("TARGET", result.rule_ids)

    def test_defer_requires_no_operation_and_an_unresolved_reference(self):
        self.assertTrue(correct_defer({"operations": [], "requires_confirmation": True, "unresolved_references": ["entrance"]}))
        self.assertFalse(correct_defer({"operations": [], "requires_confirmation": True, "unresolved_references": []}))

    def test_valid_witnesses_preserve_declared_intent_signature(self):
        scenes = {row["scene_id"]: row for row in load_jsonl(DATASET / "scenes.jsonl")}
        checked = 0
        for gold in load_jsonl(DATASET / "gold.jsonl"):
            witness = gold["valid_witness_ir"]
            if witness is None:
                continue
            self.assertTrue(
                intent_signature_correct(scenes[gold["scene_id"]], gold, witness),
                gold["semantic_task_id"],
            )
            checked += 1
        self.assertEqual(checked, 66)


if __name__ == "__main__":
    unittest.main()
