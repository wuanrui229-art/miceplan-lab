from __future__ import annotations

import json
import unittest
from pathlib import Path
from typing import Any

from miceplan_lab.policy_runner import FiveConditionRunner, ModelCall
from miceplan_lab.runtime_gate import RuntimeGate


DATASET = Path(__file__).resolve().parents[3] / "data" / "miceplan_lab_v1_1"
PROMPTS = DATASET / "prompts"


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


class ScriptedAdapter:
    def __init__(self, initial_invalid: dict[str, Any], valid_repair: dict[str, Any]) -> None:
        self.initial_invalid = initial_invalid
        self.valid_repair = valid_repair
        self.calls: list[dict[str, Any]] = []

    def generate(
        self,
        *,
        request: dict[str, Any],
        visible_scene: dict[str, Any],
        prompt: str,
        semantic_attempt: int,
        previous_ir: dict[str, Any] | None = None,
        feedback: dict[str, Any] | None = None,
    ) -> ModelCall:
        self.calls.append(
            {
                "request_id": request["request_id"],
                "semantic_attempt": semantic_attempt,
                "feedback": feedback,
                "prompt": prompt.splitlines()[0],
                "visible_scene": visible_scene,
                "previous_ir": previous_ir,
            }
        )
        if semantic_attempt == 0 and "constraint-in-prompt" in prompt:
            ir = self.valid_repair
        elif semantic_attempt == 0:
            ir = self.initial_invalid
        elif feedback is not None:
            ir = self.valid_repair
        else:
            ir = self.initial_invalid
        return ModelCall(
            call_id=f"fake-{len(self.calls)}",
            ir=ir,
            raw_response={"fake": True},
            latency_ms=1.0,
            usage={"prompt_tokens": 10, "completion_tokens": 5, "cached_tokens": 0, "total_tokens": 15},
        )


class FiveConditionRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scenes = {row["scene_id"]: row for row in load_jsonl(DATASET / "scenes.jsonl")}
        cls.requests = load_jsonl(DATASET / "requests.jsonl")
        cls.gold = load_jsonl(DATASET / "gold.jsonl")
        cls.requests_by_task: dict[str, list[dict]] = {}
        for row in cls.requests:
            cls.requests_by_task.setdefault(row["semantic_task_id"], []).append(row)

    def test_all_witnesses_pass_runtime_gate_and_all_probes_fail(self):
        gate = RuntimeGate()
        witness_count = 0
        probe_count = 0
        for gold in self.gold:
            request = self.requests_by_task[gold["semantic_task_id"]][0]
            scene = self.scenes[gold["scene_id"]]
            if gold["valid_witness_ir"] is not None:
                result = gate.evaluate(scene, request, gold["valid_witness_ir"])
                self.assertEqual(result.status, "PASS", (gold["semantic_task_id"], result.to_dict()))
                witness_count += 1
            if gold["invalid_probe_ir"] is not None:
                result = gate.evaluate(scene, request, gold["invalid_probe_ir"]["ir"])
                self.assertEqual(result.status, "FAIL", (gold["semantic_task_id"], result.to_dict()))
                probe_count += 1
        self.assertEqual((witness_count, probe_count), (66, 42))

    def test_rule_feedback_isolated_from_blind_retry(self):
        gold = next(row for row in self.gold if row["target_stress_class"] == "OVERLAP")
        request = next(row for row in self.requests_by_task[gold["semantic_task_id"]] if row["language"] == "en")
        scene = self.scenes[gold["scene_id"]]
        adapter = ScriptedAdapter(gold["invalid_probe_ir"]["ir"], gold["valid_witness_ir"])
        outcomes = FiveConditionRunner(adapter, PROMPTS, max_semantic_repairs=3).run_request(request, scene)

        self.assertEqual(outcomes["LLM_ONLY"].final_action, "EXPOSE")
        self.assertEqual(outcomes["CONSTRAINT_IN_PROMPT"].final_action, "EXPOSE")
        self.assertEqual(outcomes["VALIDATE_AND_BLOCK"].final_action, "BLOCK")
        self.assertEqual(outcomes["VALIDATE_AND_REPAIR"].final_action, "EXPOSE")
        self.assertEqual(outcomes["VALIDATE_AND_REPAIR"].semantic_attempts, 1)
        self.assertEqual(outcomes["VALIDATE_AND_BLIND_RETRY"].final_action, "BLOCK")
        self.assertEqual(outcomes["VALIDATE_AND_BLIND_RETRY"].semantic_attempts, 3)

        base = outcomes["LLM_ONLY"].model_calls[0]
        self.assertIs(outcomes["VALIDATE_AND_BLOCK"].model_calls[0], base)
        self.assertIs(outcomes["VALIDATE_AND_REPAIR"].model_calls[0], base)
        self.assertIs(outcomes["VALIDATE_AND_BLIND_RETRY"].model_calls[0], base)
        rule_calls = [call for call in adapter.calls if call["semantic_attempt"] > 0 and call["feedback"] is not None]
        blind_calls = [call for call in adapter.calls if call["semantic_attempt"] > 0 and call["feedback"] is None]
        self.assertEqual(len(rule_calls), 1)
        self.assertEqual(len(blind_calls), 3)
        self.assertTrue(rule_calls[0]["feedback"]["issues"])

    def test_ungated_explicit_clarification_is_defer_not_exposure(self):
        runner = FiveConditionRunner(
            ScriptedAdapter({}, {}), PROMPTS, max_semantic_repairs=0
        )
        defer_ir = {
            "request_id": "defer-test",
            "source_layout_version": "v1",
            "language": "en",
            "operations": [],
            "hard_constraints": [],
            "preferences": [],
            "assumptions": [],
            "unresolved_references": ["unspecified entrance"],
            "requires_confirmation": True,
        }
        call = ModelCall(
            call_id="defer-call",
            ir=defer_ir,
            raw_response={"fake": True},
            latency_ms=1.0,
            usage={"prompt_tokens": 1, "completion_tokens": 1, "cached_tokens": 0, "total_tokens": 2},
        )
        self.assertEqual(runner._ungated("LLM_ONLY", call).final_action, "DEFER")


if __name__ == "__main__":
    unittest.main()
