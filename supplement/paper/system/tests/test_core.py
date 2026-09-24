from __future__ import annotations

import json
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from miceplan.api import build_service, dispatch
from miceplan.geometry import GeometryValidator
from miceplan.models import Booth, HallLayout, LayoutEditIR, ModelError
from miceplan.parser import (
    DeterministicBaselineParser,
    OpenAICompatiblePromptOnlyParser,
    OpenAICompatibleStructuredParser,
)
from miceplan.models import Operation, OperationType
from miceplan.solver import DeterministicLayoutSolver


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "demo_hall_v1.json"


def load_layout() -> HallLayout:
    return HallLayout.from_dict(json.loads(DATA_PATH.read_text(encoding="utf-8")))


class ParserTests(unittest.TestCase):
    def setUp(self):
        self.layout = load_layout()
        self.parser = DeterministicBaselineParser()

    def test_chinese_split_request_becomes_bounded_ir(self):
        ir = self.parser.parse("将北侧 A101 和 A103 拆分为 8 个标准展位，但不要移动已售展位", self.layout)
        self.assertFalse(ir.requires_confirmation)
        self.assertEqual(ir.operations[0].type.value, "SPLIT_BOOTH")
        self.assertEqual(ir.operations[0].target_ids, ("b-a101", "b-a103"))
        self.assertEqual(ir.operations[0].count, 8)
        self.assertEqual((ir.operations[0].width, ir.operations[0].height), (3.0, 3.0))
        self.assertIn("preserve_sold_and_locked", ir.hard_constraints)

    def test_unknown_reference_is_not_guessed(self):
        ir = self.parser.parse("Split A999 into 4 standard booths", self.layout)
        self.assertTrue(ir.requires_confirmation)
        self.assertIn("A999", ir.unresolved_references)

    def test_protected_target_is_blocked_before_solving(self):
        ir = self.parser.parse("Move sold booth A105 to the west", self.layout)
        self.assertTrue(ir.requires_confirmation)
        self.assertIn("protected:A105", ir.unresolved_references)

    def test_strict_ir_rejects_unknown_fields(self):
        payload = {
            "request_id": "req-test",
            "source_layout_version": "v1",
            "language": "en",
            "operations": [],
            "hard_constraints": [],
            "preferences": [],
            "assumptions": [],
            "unresolved_references": [],
            "requires_confirmation": True,
            "invented_field": "not allowed",
        }
        with self.assertRaises(ModelError):
            LayoutEditIR.from_dict(payload)

    def test_strict_ir_rejects_noncanonical_region(self):
        payload = self.parser.parse("Move A101 to the west", self.layout).to_dict()
        payload["operations"][0]["region"] = "west side"
        with self.assertRaises(ModelError):
            LayoutEditIR.from_dict(payload)


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.source = load_layout()
        self.validator = GeometryValidator()

    def test_overlap_is_detected_independently(self):
        booths = list(self.source.booths)
        booths.append(Booth(id="bad", number="BAD1", x=3, y=3, width=3, height=3))
        candidate = replace(self.source, version="candidate", booths=tuple(booths))
        report = self.validator.validate(self.source, candidate)
        overlap = next(check for check in report.checks if check.rule == "no_overlap")
        self.assertFalse(report.valid)
        self.assertFalse(overlap.passed)
        self.assertIn("bad", overlap.object_ids)

    def test_sold_booth_change_is_detected_independently(self):
        booths = tuple(replace(booth, x=booth.x + 1) if booth.id == "b-a105" else booth for booth in self.source.booths)
        candidate = replace(self.source, version="candidate", booths=booths)
        report = self.validator.validate(self.source, candidate)
        protected = next(check for check in report.checks if check.rule == "preserve_sold_and_locked")
        self.assertFalse(protected.passed)
        self.assertIn("b-a105", protected.object_ids)


class SolverOperationTests(unittest.TestCase):
    def setUp(self):
        self.layout = load_layout()
        self.solver = DeterministicLayoutSolver()
        self.validator = GeometryValidator()

    def run_operation(self, operation: Operation) -> HallLayout:
        ir = LayoutEditIR(
            request_id=f"req-{operation.type.value.lower()}",
            source_layout_version="v1",
            language="en",
            operations=(operation,),
            hard_constraints=("within_boundary", "no_overlap", "avoid_protected_polygons"),
        )
        candidate = self.solver.solve(self.layout, ir)
        self.assertTrue(self.validator.validate(self.layout, candidate, ir).valid)
        return candidate

    def test_add_move_resize_remove_and_reserve_aisle(self):
        added = self.run_operation(Operation(OperationType.ADD_BOOTH, count=2, width=3, height=3, region="south", booth_type="standard"))
        self.assertEqual(len(added.booths), 7)

        moved = self.run_operation(Operation(OperationType.MOVE_BOOTH, target_ids=("b-a101",), x=40, y=20))
        self.assertEqual(next(booth for booth in moved.booths if booth.id == "b-a101").x, 40)

        resized = self.run_operation(Operation(OperationType.RESIZE_BOOTH, target_ids=("b-a101",), width=6, height=6))
        self.assertEqual(next(booth for booth in resized.booths if booth.id == "b-a101").width, 6)

        removed = self.run_operation(Operation(OperationType.REMOVE_BOOTH, target_ids=("b-a101",)))
        self.assertNotIn("b-a101", {booth.id for booth in removed.booths})

        aisle = self.run_operation(Operation(OperationType.RESERVE_AISLE, x=40, y=30, width=3, height=6))
        self.assertTrue(any(area.id.startswith("req-reserve_aisle-aisle") for area in aisle.fixed_aisles))


class ServiceTests(unittest.TestCase):
    def test_preview_approve_creates_immutable_child_version(self):
        with patch.dict("os.environ", {"MICEPLAN_PARSER": "baseline"}):
            service = build_service(DATA_PATH)
        proposal = service.preview("demo", "v1", "将 A101 和 A103 拆分为 8 个标准展位，并保留已售展位")
        self.assertEqual(proposal.state, "awaiting_approval")
        self.assertTrue(proposal.validation and proposal.validation.valid)
        self.assertEqual(len([entry for entry in proposal.diff if entry.change == "removed"]), 2)
        self.assertEqual(len([entry for entry in proposal.diff if entry.change == "added"]), 8)
        approved = service.approve(proposal.id)
        self.assertEqual(approved.state, "approved")
        self.assertEqual(approved.created_version, "v2")
        versions = service.list_versions("demo")
        self.assertEqual([item["version"] for item in versions], ["v1", "v2"])
        self.assertEqual(versions[1]["parent_version"], "v1")
        self.assertEqual(len(versions[0]["booths"]), 5)
        self.assertEqual(len(versions[1]["booths"]), 11)

    def test_rejection_preserves_version_history(self):
        with patch.dict("os.environ", {"MICEPLAN_PARSER": "baseline"}):
            service = build_service(DATA_PATH)
        proposal = service.preview("demo", "v1", "将 A101 和 A103 拆分为 8 个标准展位")
        service.reject(proposal.id)
        self.assertEqual([item["version"] for item in service.list_versions("demo")], ["v1"])


class ApiContractTests(unittest.TestCase):
    def test_preview_and_approval_endpoint_contract(self):
        with patch.dict("os.environ", {"MICEPLAN_PARSER": "baseline"}):
            service = build_service(DATA_PATH)
        status, preview = dispatch(service, "POST", "/projects/demo/preview", {"source_version": "v1", "request": "Split A101 and A103 into 8 standard booths and preserve sold booths"})
        self.assertEqual(status, 200)
        self.assertEqual(preview["state"], "awaiting_approval")
        status, approved = dispatch(service, "POST", f"/proposals/{preview['id']}/approve", {})
        self.assertEqual(status, 200)
        self.assertEqual(approved["created_version"], "v2")
        status, response = dispatch(service, "GET", "/projects/demo/versions")
        self.assertEqual(status, 200)
        versions = response["versions"]
        self.assertEqual(len(versions), 2)


class StructuredModelAdapterTests(unittest.TestCase):
    def test_adapter_sends_strict_json_schema_and_validates_response(self):
        captured: dict = {}
        layout = load_layout()
        response_ir = {
            "request_id": "req-mock",
            "source_layout_version": "v1",
            "language": "en",
            "operations": [{
                "type": "REMOVE_BOOTH", "target_ids": ["b-a101"], "count": None,
                "width": None, "height": None, "x": None, "y": None,
                "region": None, "booth_type": None
            }],
            "hard_constraints": ["preserve_sold_and_locked"],
            "preferences": [], "assumptions": [], "unresolved_references": [],
            "requires_confirmation": False
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps({"choices": [{"message": {"content": json.dumps(response_ir)}}]}).encode("utf-8")

        def fake_urlopen(request, timeout):
            captured.update(json.loads(request.data.decode("utf-8")))
            return FakeResponse()

        parser = OpenAICompatibleStructuredParser(
            endpoint="https://example.invalid/chat/completions",
            api_key="test-key",
            model="test-model",
        )
        with patch("urllib.request.urlopen", side_effect=fake_urlopen):
            ir = parser.parse("Remove A101", layout)
        self.assertEqual(ir.operations[0].type.value, "REMOVE_BOOTH")
        self.assertEqual(captured["response_format"]["type"], "json_schema")
        self.assertTrue(captured["response_format"]["json_schema"]["strict"])

    def test_prompt_only_adapter_carries_contract_without_response_format(self):
        parser = OpenAICompatiblePromptOnlyParser(
            endpoint="https://example.invalid/chat/completions",
            api_key="test-key",
            model="test-model",
        )
        payload = parser._payload("Remove A101", load_layout())
        self.assertNotIn("response_format", payload)
        user_context = json.loads(payload["messages"][1]["content"])
        self.assertEqual(user_context["output_contract"]["type"], "object")
        self.assertIn("Return exactly one JSON object", user_context["output_instruction"])


if __name__ == "__main__":
    unittest.main()
