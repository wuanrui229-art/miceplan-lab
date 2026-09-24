from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from typing import Any

from miceplan_lab.policy_runner import ModelCall
from miceplan_lab.seeded_runner import SeededRecoveryRunner


DATA = Path(__file__).resolve().parents[3] / "data" / "miceplan_lab_v1_1"
PROMPTS = DATA / "prompts"


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class RepairAdapter:
    def __init__(self, valid_ir: dict[str, Any], failed_ir: dict[str, Any]) -> None:
        self.valid_ir = valid_ir
        self.failed_ir = failed_ir
        self.calls: list[dict[str, Any]] = []

    def generate(self, **kwargs: Any) -> ModelCall:
        self.calls.append(kwargs)
        ir = copy.deepcopy(self.valid_ir if kwargs["feedback"] is not None else self.failed_ir)
        ir["request_id"] = kwargs["request"]["request_id"]
        ir["language"] = kwargs["request"]["language"]
        return ModelCall(
            call_id=f"seeded-{len(self.calls)}",
            ir=ir,
            raw_response={"scripted": True},
            latency_ms=1.0,
            usage={"prompt_tokens": 1, "completion_tokens": 1, "cached_tokens": 0, "total_tokens": 2},
        )


class SeededRunnerTests(unittest.TestCase):
    def test_rule_feedback_recovers_while_matched_blind_retry_exhausts(self) -> None:
        seeds = load_jsonl(DATA / "fault_seeds_v1_2.jsonl")
        seed = next(row for row in seeds if row["split"] == "development")
        gold = next(row for row in load_jsonl(DATA / "gold.jsonl") if row["semantic_task_id"] == seed["semantic_task_id"])
        request = next(
            row for row in load_jsonl(DATA / "requests.jsonl")
            if row["semantic_task_id"] == seed["semantic_task_id"] and row["language"] == "en"
        )
        scene = next(row for row in load_jsonl(DATA / "scenes.jsonl") if row["scene_id"] == seed["scene_id"])
        initial = copy.deepcopy(seed["ir"])
        initial["request_id"] = request["request_id"]
        initial["language"] = request["language"]
        adapter = RepairAdapter(gold["valid_witness_ir"], initial)
        outcomes = SeededRecoveryRunner(adapter, PROMPTS, max_semantic_repairs=3).run(
            request=request, scene=scene, initial_ir=initial
        )
        self.assertEqual(outcomes["SEEDED_VALIDATE_AND_BLOCK"].final_action, "BLOCK")
        self.assertEqual(outcomes["SEEDED_VALIDATE_AND_REPAIR"].final_action, "EXPOSE")
        self.assertEqual(outcomes["SEEDED_VALIDATE_AND_REPAIR"].semantic_attempts, 1)
        self.assertEqual(outcomes["SEEDED_VALIDATE_AND_BLIND_RETRY"].final_action, "BLOCK")
        self.assertEqual(outcomes["SEEDED_VALIDATE_AND_BLIND_RETRY"].semantic_attempts, 3)
        self.assertEqual(len(outcomes["SEEDED_VALIDATE_AND_BLOCK"].model_calls), 0)
        self.assertEqual(len(outcomes["SEEDED_VALIDATE_AND_REPAIR"].model_calls), 1)
        self.assertEqual(len(outcomes["SEEDED_VALIDATE_AND_BLIND_RETRY"].model_calls), 3)


if __name__ == "__main__":
    unittest.main()
