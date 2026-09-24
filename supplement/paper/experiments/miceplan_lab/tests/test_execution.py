from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any

from miceplan_lab.execution import (
    ExperimentExecutor,
    build_run_manifest,
    load_jsonl,
    offline_evaluate_outcome,
)
from miceplan_lab.analyze_development import classify_call, compute_cost
from miceplan_lab.journal import AppendOnlyHashChain, JournalIntegrityError, RunJournal
from miceplan_lab.live_adapter import (
    DEEPSEEK_NULL_SENTINEL,
    DeepSeekStrictToolAdapter,
    OpenAICompatibleModelAdapter,
    decode_deepseek_null_sentinels,
    deepseek_strict_schema,
)
from miceplan_lab.openai_adapter import OpenAISolAdapter, normalise_openai_usage
from miceplan_lab.contracts import IR_SCHEMA
from miceplan_lab.policy_runner import ModelCall, PolicyOutcome
from miceplan_lab.run_development import model_profile, select_development_requests
from miceplan_lab.summarize_run import summarize


DATASET = Path(__file__).resolve().parents[3] / "data" / "miceplan_lab_v1_1"


class SyntheticInterruption(RuntimeError):
    pass


class SmokeAdapter:
    def __init__(self, gold_by_task: dict[str, dict[str, Any]], shared: dict[str, Any]) -> None:
        self.gold_by_task = gold_by_task
        self.shared = shared

    @staticmethod
    def _defer_ir(request: dict[str, Any], scene: dict[str, Any]) -> dict[str, Any]:
        return {
            "request_id": request["request_id"],
            "source_layout_version": scene["version"],
            "language": request["language"],
            "operations": [],
            "hard_constraints": [],
            "preferences": [],
            "assumptions": [],
            "unresolved_references": ["masked_or_ambiguous_evidence"],
            "requires_confirmation": True,
        }

    @staticmethod
    def _for_request(ir: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
        result = copy.deepcopy(ir)
        result["request_id"] = request["request_id"]
        result["language"] = request["language"]
        return result

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
        self.shared["attempted"] += 1
        if self.shared["interrupt_at"] == self.shared["attempted"] and not self.shared["interrupted"]:
            self.shared["interrupted"] = True
            raise SyntheticInterruption("simulated process interruption before a response was stored")

        gold = self.gold_by_task[request["semantic_task_id"]]
        valid = gold["valid_witness_ir"]
        if valid is None:
            good_ir = self._defer_ir(request, visible_scene)
        else:
            good_ir = self._for_request(valid, request)
        invalid_probe = gold["invalid_probe_ir"]
        bad_ir = self._for_request(invalid_probe["ir"], request) if invalid_probe is not None else good_ir

        first_line = prompt.splitlines()[0]
        if "constraint-in-prompt" in first_line or feedback is not None:
            ir = good_ir
        elif "matched blind-retry" in first_line:
            ir = previous_ir or bad_ir
        else:
            ir = bad_ir
        self.shared["successful"] += 1
        return ModelCall(
            call_id=f"smoke-{self.shared['successful']}",
            ir=ir,
            raw_response={"synthetic_smoke_only": True},
            latency_ms=2.0,
            usage={"prompt_tokens": 20, "completion_tokens": 10, "cached_tokens": 0, "total_tokens": 30},
        )


class ExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.requests = sorted(
            (row for row in load_jsonl(DATASET / "requests.jsonl") if row["split"] == "development"),
            key=lambda row: row["request_id"],
        )
        cls.gold_by_task = {
            row["semantic_task_id"]: row for row in load_jsonl(DATASET / "gold.jsonl")
        }

    def manifest(self, request_ids: list[str]) -> dict[str, Any]:
        return build_run_manifest(
            run_id="twelve-request-resume-smoke",
            data_directory=DATASET,
            model_id="scripted-smoke-model",
            provider="local-scripted-test",
            endpoint="none",
            access_date="2026-07-20",
            request_ids=request_ids,
            replicate_ids=[1],
            seed=20260720,
            decoding={"temperature": 0, "semantic_repair_limit": 3},
        )

    def test_interrupted_twelve_request_smoke_resumes_without_duplicate_semantic_calls(self) -> None:
        selected = self.requests[:12]
        manifest = self.manifest([row["request_id"] for row in selected])
        shared = {"attempted": 0, "successful": 0, "interrupt_at": 8, "interrupted": False}
        with tempfile.TemporaryDirectory() as temporary:
            run_directory = Path(temporary) / "run"
            first_journal = RunJournal(run_directory, manifest)
            first = ExperimentExecutor(
                data_directory=DATASET,
                journal=first_journal,
                adapter_factory=lambda: SmokeAdapter(self.gold_by_task, shared),
            )
            with self.assertRaises(SyntheticInterruption):
                first.run()
            stored_before_resume = len(first_journal.calls.payloads)
            self.assertEqual(stored_before_resume, shared["successful"])
            self.assertGreater(stored_before_resume, 0)

            resumed_journal = RunJournal(run_directory, manifest)
            resumed = ExperimentExecutor(
                data_directory=DATASET,
                journal=resumed_journal,
                adapter_factory=lambda: SmokeAdapter(self.gold_by_task, shared),
            )
            counts = resumed.run()
            self.assertEqual(counts["outcomes"], 12 * 5)
            self.assertEqual(len({row["call_key"] for row in resumed_journal.calls.payloads}), counts["calls"])
            self.assertEqual(shared["successful"], counts["calls"])
            self.assertEqual(len(resumed_journal.errors.payloads), 1)

            reloaded = RunJournal(run_directory, manifest)
            self.assertEqual(reloaded.verify(), counts)
            report = summarize(reloaded.outcomes.payloads)
            self.assertEqual(report["row_count"], 60)
            self.assertEqual(set(report["policies"]), {
                "LLM_ONLY", "CONSTRAINT_IN_PROMPT", "VALIDATE_AND_BLOCK",
                "VALIDATE_AND_REPAIR", "VALIDATE_AND_BLIND_RETRY",
            })

    def test_hash_chain_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "events.jsonl"
            chain = AppendOnlyHashChain(path)
            chain.append({"value": 1})
            text = path.read_text(encoding="utf-8").replace('"value":1', '"value":2')
            path.write_text(text, encoding="utf-8")
            with self.assertRaises(JournalIntegrityError):
                AppendOnlyHashChain(path)

    def test_live_payload_contains_no_gold_and_blind_retry_contains_no_feedback(self) -> None:
        request = self.requests[0]
        scene = next(row for row in load_jsonl(DATASET / "scenes.jsonl") if row["scene_id"] == request["scene_id"])
        adapter = OpenAICompatibleModelAdapter("https://example.invalid", "not-logged", "test-model")
        payload = adapter._payload(
            request=request,
            visible_scene=scene,
            prompt="blind",
            semantic_attempt=1,
            previous_ir={"candidate": True},
            feedback=None,
        )
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn("gold", serialized)
        user_payload = json.loads(payload["messages"][1]["content"])
        self.assertNotIn("runtime_feedback", user_payload)
        self.assertEqual(payload["response_format"]["type"], "json_schema")

    def test_openai_sol_profile_and_payload_freeze_nonreasoning_strict_json(self) -> None:
        profile = model_profile("gpt-5.6-sol")
        self.assertIsNone(profile["temperature"])
        self.assertEqual(profile["max_output_tokens"], 32768)
        self.assertEqual(profile["max_tokens_parameter"], "max_completion_tokens")
        self.assertEqual(
            profile["extra_request_parameters"],
            {"reasoning_effort": "none", "store": False},
        )
        adapter = OpenAISolAdapter(
            "https://api.openai.com/v1/chat/completions",
            "not-logged",
            "gpt-5.6-sol",
            temperature=profile["temperature"],
            max_output_tokens=int(profile["max_output_tokens"]),
            max_tokens_parameter=str(profile["max_tokens_parameter"]),
            extra_request_parameters=dict(profile["extra_request_parameters"]),
        )
        request = self.requests[0]
        scene = next(
            row for row in load_jsonl(DATASET / "scenes.jsonl")
            if row["scene_id"] == request["scene_id"]
        )
        payload = adapter._payload(
            request=request,
            visible_scene=scene,
            prompt="strict OpenAI test",
            semantic_attempt=0,
            previous_ir=None,
            feedback=None,
        )
        self.assertNotIn("temperature", payload)
        self.assertNotIn("max_tokens", payload)
        self.assertEqual(payload["max_completion_tokens"], 32768)
        self.assertEqual(payload["reasoning_effort"], "none")
        self.assertFalse(payload["store"])
        self.assertTrue(payload["response_format"]["json_schema"]["strict"])

    def test_openai_refusal_and_cached_usage_are_normalised(self) -> None:
        adapter = OpenAISolAdapter(
            "https://api.openai.com/v1/chat/completions",
            "not-logged",
            "gpt-5.6-sol",
        )
        parsed, error = adapter._parse_candidate(
            {"choices": [{"finish_reason": "stop", "message": {"content": None, "refusal": "no"}}]}
        )
        self.assertIsNone(parsed)
        self.assertEqual(error, "provider_refusal")
        self.assertEqual(
            normalise_openai_usage(
                {
                    "prompt_tokens": 100,
                    "completion_tokens": 20,
                    "total_tokens": 120,
                    "prompt_tokens_details": {
                        "cached_tokens": 25,
                        "cache_write_tokens": 70,
                    },
                }
            ),
            {
                "prompt_tokens": 100,
                "completion_tokens": 20,
                "cached_tokens": 25,
                "cache_write_tokens": 70,
                "total_tokens": 120,
            },
        )

    def test_deepseek_strict_schema_uses_supported_subset(self) -> None:
        converted = deepseek_strict_schema(IR_SCHEMA)

        def visit(value: Any) -> None:
            if isinstance(value, list):
                for item in value:
                    visit(item)
                return
            if not isinstance(value, dict):
                return
            for unsupported in (
                "$id", "$schema", "title", "minLength", "maxLength", "minItems", "maxItems"
            ):
                self.assertNotIn(unsupported, value)
            if value.get("type") == "object":
                self.assertFalse(value.get("additionalProperties", True))
                self.assertEqual(set(value["properties"]), set(value["required"]))
            for item in value.values():
                visit(item)

        visit(converted)
        width = converted["properties"]["operations"]["items"]["properties"]["width"]
        self.assertIn("anyOf", width)
        self.assertIn(
            {"type": "string", "enum": [DEEPSEEK_NULL_SENTINEL]},
            width["anyOf"],
        )
        self.assertTrue(all("type" in branch for branch in width["anyOf"]))

    def test_deepseek_null_sentinel_decoder_is_field_scoped(self) -> None:
        candidate = {
            "operations": [{"count": DEEPSEEK_NULL_SENTINEL, "booth_type": "standard"}],
            "assumptions": [DEEPSEEK_NULL_SENTINEL],
        }
        decoded = decode_deepseek_null_sentinels(candidate)
        self.assertIsNone(decoded["operations"][0]["count"])
        self.assertEqual(decoded["operations"][0]["booth_type"], "standard")
        self.assertEqual(decoded["assumptions"], [DEEPSEEK_NULL_SENTINEL])

    def test_deepseek_payload_and_tool_response_preserve_frozen_ir_contract(self) -> None:
        request = next(
            row for row in self.requests
            if self.gold_by_task[row["semantic_task_id"]]["valid_witness_ir"] is not None
        )
        scene = next(
            row for row in load_jsonl(DATASET / "scenes.jsonl")
            if row["scene_id"] == request["scene_id"]
        )
        adapter = DeepSeekStrictToolAdapter(
            "https://api.deepseek.com/beta/chat/completions",
            "not-logged",
            "deepseek-v4-pro",
        )
        payload = adapter._payload(
            request=request,
            visible_scene=scene,
            prompt="strict test",
            semantic_attempt=0,
            previous_ir=None,
            feedback=None,
        )
        serialized = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn("gold", serialized)
        self.assertNotIn("response_format", payload)
        self.assertTrue(payload["tools"][0]["function"]["strict"])
        self.assertEqual(payload["tool_choice"]["function"]["name"], adapter.tool_name)

        candidate = SmokeAdapter._for_request(
            self.gold_by_task[request["semantic_task_id"]]["valid_witness_ir"], request
        )
        body = {
            "choices": [{
                "message": {
                    "tool_calls": [{
                        "function": {
                            "name": adapter.tool_name,
                            "arguments": json.dumps(candidate),
                        }
                    }]
                }
            }]
        }
        parsed, error = adapter._parse_candidate(body)
        self.assertIsNone(error)
        self.assertEqual(parsed, candidate)

    def test_kimi_profiles_use_provider_compatible_controls(self) -> None:
        self.assertEqual(model_profile("kimi-k2.7-code")["temperature"], 1.0)
        self.assertEqual(model_profile("kimi-k2.7-code-highspeed")["max_output_tokens"], 32768)
        self.assertEqual(model_profile("kimi-k2.6")["extra_request_parameters"], {"thinking": {"type": "disabled"}})
        self.assertEqual(model_profile("kimi-k3")["extra_request_parameters"], {"reasoning_effort": "low"})
        self.assertEqual(model_profile("deepseek-v4-pro")["max_output_tokens"], 32768)
        self.assertEqual(
            model_profile("deepseek-v4-pro")["extra_request_parameters"],
            {"thinking": {"type": "disabled"}},
        )

    def test_explicit_selection_rejects_heldout_and_preserves_order(self) -> None:
        all_requests = load_jsonl(DATASET / "requests.jsonl")
        selected = select_development_requests(all_requests, ["task-0021-zh", "task-0001-en"], 99)
        self.assertEqual([row["request_id"] for row in selected], ["task-0021-zh", "task-0001-en"])
        heldout = next(row["request_id"] for row in all_requests if row["split"] == "test")
        with self.assertRaises(ValueError):
            select_development_requests(all_requests, [heldout], 99)

    def test_pricing_and_prompt_role_helpers(self) -> None:
        pricing = {
            "billing_unit_tokens": 1_000_000,
            "prices_per_million_tokens": {
                "cache_hit_input": 0.19,
                "cache_miss_input": 0.95,
                "output": 4.0,
            },
        }
        usage = {
            "prompt_tokens": 1_000_000,
            "cached_tokens": 250_000,
            "completion_tokens": 100_000,
        }
        self.assertAlmostEqual(compute_cost(usage, pricing), 1.16)
        pricing["prices_per_million_tokens"]["cache_write_input"] = 1.1875
        usage["cache_write_tokens"] = 500_000
        self.assertAlmostEqual(compute_cost(usage, pricing), 1.27875)
        self.assertEqual(
            classify_call("MICEPlan-Lab rule-evidence repair prompt v0.1-development"),
            "RULE_REPAIR",
        )
        with self.assertRaises(ValueError):
            classify_call("unknown prompt")

    def test_correct_defer_is_safe_resolution_not_invalid_exposure(self) -> None:
        request = next(
            row for row in self.requests if self.gold_by_task[row["semantic_task_id"]]["admissible_final_outcome"] == "DEFER"
        )
        scene = next(row for row in load_jsonl(DATASET / "scenes.jsonl") if row["scene_id"] == request["scene_id"])
        ir = SmokeAdapter._defer_ir(request, scene)
        outcome = PolicyOutcome("LLM_ONLY", "DEFER", ir, (), (), 0)
        evaluation = offline_evaluate_outcome(scene, self.gold_by_task[request["semantic_task_id"]], outcome)
        self.assertTrue(evaluation["correct_defer"])
        self.assertTrue(evaluation["safe_resolution"])
        self.assertFalse(evaluation["rule_invalid_operation_exposed"])
        self.assertFalse(evaluation["unsafe_candidate_exposed"])


if __name__ == "__main__":
    unittest.main()
