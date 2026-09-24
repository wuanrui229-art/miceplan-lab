from __future__ import annotations

import json
import unittest
from pathlib import Path

from miceplan.geometry import GeometryValidator
from miceplan.models import HallLayout
from miceplan_lab.oracle import apply_ir


DATASET = Path(__file__).resolve().parents[3] / "data" / "miceplan_lab_v1_1"
RULE_MAP = {
    "BOUNDARY": "within_boundary",
    "OVERLAP": "no_overlap",
    "PROTECTED_POLYGON": "avoid_protected_polygons",
    "LOCKED_MUTATION": "preserve_sold_and_locked",
}


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def to_runtime_layout(scene: dict, version: str) -> HallLayout:
    return HallLayout.from_dict(
        {
            "hall_id": scene["scene_id"],
            "version": version,
            "unit": scene["unit"],
            "boundary": scene["boundary"],
            "booths": scene["booths"],
            "obstacles": scene["obstacles"],
            "fixed_aisles": scene["fixed_aisles"],
            "exits": scene["exits"],
        }
    )


class RuntimeDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = {row["scene_id"]: row for row in load_jsonl(DATASET / "scenes.jsonl")}
        cls.gold = load_jsonl(DATASET / "gold.jsonl")

    def test_runtime_and_oracle_detect_each_deterministic_rule(self):
        checked: set[str] = set()
        validator = GeometryValidator()
        for gold in self.gold:
            stress = gold["target_stress_class"]
            if stress not in RULE_MAP or stress in checked:
                continue
            scene = self.scenes[gold["scene_id"]]
            oracle = apply_ir(scene, gold["invalid_probe_ir"]["ir"])
            self.assertEqual(oracle.status, "FAIL")
            self.assertIsNotNone(oracle.scene_after)
            source = to_runtime_layout(scene, "v1")
            candidate = to_runtime_layout(oracle.scene_after, "candidate")
            runtime = validator.validate(source, candidate)
            runtime_check = next(check for check in runtime.checks if check.rule == RULE_MAP[stress])
            self.assertFalse(runtime_check.passed, stress)
            checked.add(stress)
        self.assertEqual(checked, set(RULE_MAP))


if __name__ == "__main__":
    unittest.main()
