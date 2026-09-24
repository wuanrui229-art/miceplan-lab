from __future__ import annotations

import json
import unittest
from pathlib import Path

from miceplan_lab.formal_run import (
    DATA,
    audit_formal_preconditions,
    build_natural_jobs,
    build_plan,
    build_seeded_jobs,
)
from miceplan_lab.execution import load_jsonl
from miceplan_lab.formal_run_openai import audit_openai_preconditions, build_openai_plan


class FormalRunTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.selection = json.loads((DATA / "formal_selection_v1_2.json").read_text(encoding="utf-8"))
        cls.requests = load_jsonl(DATA / "requests.jsonl")
        cls.seeds = {
            row["seed_id"]: row
            for filename in ("fault_seeds_v1_2.jsonl", "fault_seeds_composite_v1_2.jsonl")
            for row in load_jsonl(DATA / filename)
        }

    def test_exact_irregular_formal_schedules(self) -> None:
        natural = build_natural_jobs(self.selection, self.requests)
        seeded = build_seeded_jobs(self.selection, self.requests, self.seeds)
        self.assertEqual(len(natural), 216)
        self.assertEqual(len(seeded), 210)
        self.assertEqual(sum(job["replicate_id"] == 1 for job in natural), 144)
        self.assertEqual(sum(job["replicate_id"] in {2, 3} for job in natural), 72)
        self.assertEqual(sum(job["replicate_id"] == 1 for job in seeded), 126)
        self.assertEqual(sum(job["replicate_id"] in {2, 3} for job in seeded), 84)

    def test_every_formal_item_is_held_out(self) -> None:
        requests = {row["request_id"]: row for row in self.requests}
        for job in build_natural_jobs(self.selection, self.requests):
            self.assertEqual(requests[job["request_id"]]["split"], "test")
        for job in build_seeded_jobs(self.selection, self.requests, self.seeds):
            self.assertEqual(requests[job["request_id"]]["split"], "test")
            self.assertEqual(self.seeds[job["seed_id"]]["split"], "test")

    def test_frozen_models_and_call_bounds(self) -> None:
        natural = build_plan("natural", "kimi", "test-natural")
        seeded = build_plan("seeded", "deepseek", "test-seeded")
        openai = build_openai_plan("natural", "test-openai-natural")
        self.assertEqual(natural["model_id"], "kimi-k2.7-code-highspeed")
        self.assertEqual(seeded["model_id"], "deepseek-v4-pro")
        self.assertEqual(natural["expected"]["minimum_model_calls"], 432)
        self.assertEqual(natural["expected"]["maximum_model_calls"], 1728)
        self.assertEqual(seeded["expected"]["minimum_model_calls"], 420)
        self.assertEqual(seeded["expected"]["maximum_model_calls"], 1260)
        self.assertEqual(openai["model_id"], "gpt-5.6-sol")
        self.assertEqual(openai["endpoint"], "https://api.openai.com/v1/chat/completions")
        self.assertEqual(openai["decoding"]["max_tokens_parameter"], "max_completion_tokens")
        self.assertEqual(
            openai["decoding"]["extra_request_parameters"],
            {"reasoning_effort": "none", "store": False},
        )
        self.assertEqual(openai["pricing_file"], "PRICING_OPENAI_GPT56_SOL_2026-09-01.json")

    def test_preflight_passes_current_freeze(self) -> None:
        self.assertEqual(audit_formal_preconditions()["status"], "PASS")

    def test_openai_extension_preflight_passes_separate_freeze(self) -> None:
        self.assertEqual(audit_openai_preconditions()["extension_status"], "PASS")


if __name__ == "__main__":
    unittest.main()
