from __future__ import annotations

from pathlib import Path
from typing import Any

from .policy_runner import ModelAdapter, PolicyOutcome, visible_scene
from .runtime_gate import GateResult, RuntimeGate


SEEDED_POLICIES = (
    "SEEDED_VALIDATE_AND_BLOCK",
    "SEEDED_VALIDATE_AND_REPAIR",
    "SEEDED_VALIDATE_AND_BLIND_RETRY",
)


def _feedback(gate: GateResult) -> dict[str, Any]:
    return {"status": gate.status, "issues": [issue.to_dict() for issue in gate.issues]}


class SeededRecoveryRunner:
    """Run matched policies from one deterministic, intent-preserving failed IR."""

    def __init__(self, adapter: ModelAdapter, prompt_directory: Path, max_semantic_repairs: int = 3) -> None:
        self.adapter = adapter
        self.prompt_directory = prompt_directory
        self.max_semantic_repairs = max_semantic_repairs
        self.gate = RuntimeGate()

    def _prompt(self, name: str) -> str:
        return (self.prompt_directory / name).read_text(encoding="utf-8")

    def _run_policy(
        self,
        *,
        policy: str,
        request: dict[str, Any],
        scene: dict[str, Any],
        initial_ir: dict[str, Any],
    ) -> PolicyOutcome:
        calls = []
        events: list[dict[str, Any]] = []
        current_ir = initial_ir
        for semantic_attempt in range(self.max_semantic_repairs + 1):
            gate = self.gate.evaluate(scene, request, current_ir)
            events.append({"semantic_attempt": semantic_attempt, "gate": gate.to_dict()})
            if semantic_attempt == 0 and gate.status != "FAIL":
                raise ValueError("A seeded-recovery initial candidate must enter through FAIL")
            if gate.status == "PASS":
                return PolicyOutcome(policy, "EXPOSE", current_ir, tuple(events), tuple(calls), semantic_attempt)
            if gate.status == "UNKNOWN":
                return PolicyOutcome(policy, "DEFER", current_ir, tuple(events), tuple(calls), semantic_attempt)
            if policy == "SEEDED_VALIDATE_AND_BLOCK" or semantic_attempt == self.max_semantic_repairs:
                return PolicyOutcome(policy, "BLOCK", current_ir, tuple(events), tuple(calls), semantic_attempt)

            rule_feedback = policy == "SEEDED_VALIDATE_AND_REPAIR"
            repair_call = self.adapter.generate(
                request=request,
                visible_scene=visible_scene(scene, request),
                prompt=self._prompt("repair.txt" if rule_feedback else "blind_retry.txt"),
                semantic_attempt=semantic_attempt + 1,
                previous_ir=current_ir,
                feedback=_feedback(gate) if rule_feedback else None,
            )
            calls.append(repair_call)
            current_ir = repair_call.ir
        raise AssertionError("bounded seeded-recovery loop did not terminate")

    def run(
        self,
        *,
        request: dict[str, Any],
        scene: dict[str, Any],
        initial_ir: dict[str, Any],
        repair_policy_order: tuple[str, str] = (
            "SEEDED_VALIDATE_AND_REPAIR",
            "SEEDED_VALIDATE_AND_BLIND_RETRY",
        ),
    ) -> dict[str, PolicyOutcome]:
        allowed = {"SEEDED_VALIDATE_AND_REPAIR", "SEEDED_VALIDATE_AND_BLIND_RETRY"}
        if set(repair_policy_order) != allowed or len(repair_policy_order) != 2:
            raise ValueError("repair_policy_order must contain both seeded repair policies")
        results = {
            "SEEDED_VALIDATE_AND_BLOCK": self._run_policy(
                policy="SEEDED_VALIDATE_AND_BLOCK",
                request=request,
                scene=scene,
                initial_ir=initial_ir,
            )
        }
        for policy in repair_policy_order:
            results[policy] = self._run_policy(
                policy=policy,
                request=request,
                scene=scene,
                initial_ir=initial_ir,
            )
        return {policy: results[policy] for policy in SEEDED_POLICIES}
