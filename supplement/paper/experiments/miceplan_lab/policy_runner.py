from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from .runtime_gate import GateResult, RuntimeGate


POLICIES = (
    "LLM_ONLY",
    "CONSTRAINT_IN_PROMPT",
    "VALIDATE_AND_BLOCK",
    "VALIDATE_AND_REPAIR",
    "VALIDATE_AND_BLIND_RETRY",
)


@dataclass(frozen=True)
class ModelCall:
    call_id: str
    ir: dict[str, Any] | None
    raw_response: Any
    latency_ms: float
    usage: dict[str, int]
    error: str | None = None
    infrastructure_attempts: int = 1
    infrastructure_errors: tuple[str, ...] = ()


class ModelAdapter(Protocol):
    def generate(
        self,
        *,
        request: dict[str, Any],
        visible_scene: dict[str, Any],
        prompt: str,
        semantic_attempt: int,
        previous_ir: dict[str, Any] | None = None,
        feedback: dict[str, Any] | None = None,
    ) -> ModelCall: ...


@dataclass(frozen=True)
class PolicyOutcome:
    policy: str
    final_action: str
    final_ir: dict[str, Any] | None
    gate_events: tuple[dict[str, Any], ...]
    model_calls: tuple[ModelCall, ...]
    semantic_attempts: int


def visible_scene(scene: dict[str, Any], request: dict[str, Any]) -> dict[str, Any]:
    result = dict(scene)
    mask = request["context_mask"]
    if mask["hide_unit"]:
        result.pop("unit", None)
    if mask["hide_scale"]:
        result["scale"] = None
    if mask["hide_disambiguating_labels"]:
        result["booths"] = [{key: value for key, value in booth.items() if key not in {"id", "number"}} for booth in scene["booths"]]
        result["exits"] = [{key: value for key, value in item.items() if key != "id"} for item in scene["exits"]]
    return result


def _feedback_from_gate(gate: GateResult) -> dict[str, Any]:
    return {
        "status": gate.status,
        "issues": [issue.to_dict() for issue in gate.issues],
    }


class FiveConditionRunner:
    def __init__(self, adapter: ModelAdapter, prompt_directory: Path, max_semantic_repairs: int = 3) -> None:
        self.adapter = adapter
        self.prompt_directory = prompt_directory
        self.max_semantic_repairs = max_semantic_repairs
        self.gate = RuntimeGate()

    def _prompt(self, name: str) -> str:
        return (self.prompt_directory / name).read_text(encoding="utf-8")

    def _ungated(self, policy: str, call: ModelCall) -> PolicyOutcome:
        if call.ir is None or call.error is not None:
            action = "BLOCK"
        elif call.ir.get("requires_confirmation") and not call.ir.get("operations"):
            action = "DEFER"
        else:
            action = "EXPOSE"
        return PolicyOutcome(policy, action, call.ir, (), (call,), 0)

    def _gated(
        self,
        *,
        policy: str,
        request: dict[str, Any],
        scene: dict[str, Any],
        initial: ModelCall,
    ) -> PolicyOutcome:
        calls = [initial]
        events: list[dict[str, Any]] = []
        current_ir = initial.ir
        for semantic_attempt in range(self.max_semantic_repairs + 1):
            gate = self.gate.evaluate(scene, request, current_ir)
            events.append({"semantic_attempt": semantic_attempt, "gate": gate.to_dict()})
            if gate.status == "PASS":
                return PolicyOutcome(policy, "EXPOSE", current_ir, tuple(events), tuple(calls), semantic_attempt)
            if gate.status == "UNKNOWN":
                return PolicyOutcome(policy, "DEFER", current_ir, tuple(events), tuple(calls), semantic_attempt)
            if policy == "VALIDATE_AND_BLOCK" or semantic_attempt == self.max_semantic_repairs:
                return PolicyOutcome(policy, "BLOCK", current_ir, tuple(events), tuple(calls), semantic_attempt)

            feedback_mode = "RULE_EVIDENCE" if policy == "VALIDATE_AND_REPAIR" else "GENERIC"
            feedback = _feedback_from_gate(gate) if feedback_mode == "RULE_EVIDENCE" else None
            prompt_name = "repair.txt" if feedback_mode == "RULE_EVIDENCE" else "blind_retry.txt"
            repair_call = self.adapter.generate(
                request=request,
                visible_scene=visible_scene(scene, request),
                prompt=self._prompt(prompt_name),
                semantic_attempt=semantic_attempt + 1,
                previous_ir=current_ir,
                feedback=feedback,
            )
            calls.append(repair_call)
            current_ir = repair_call.ir
        raise AssertionError("bounded policy loop did not terminate")

    def run_request(
        self,
        request: dict[str, Any],
        scene: dict[str, Any],
        *,
        initial_arm_order: tuple[str, str] = ("LLM_ONLY", "CONSTRAINT_IN_PROMPT"),
        repair_policy_order: tuple[str, str] = ("VALIDATE_AND_REPAIR", "VALIDATE_AND_BLIND_RETRY"),
    ) -> dict[str, PolicyOutcome]:
        model_scene = visible_scene(scene, request)
        allowed_initial = {"LLM_ONLY", "CONSTRAINT_IN_PROMPT"}
        if set(initial_arm_order) != allowed_initial or len(initial_arm_order) != 2:
            raise ValueError("initial_arm_order must contain each initial arm exactly once")
        allowed_repairs = {"VALIDATE_AND_REPAIR", "VALIDATE_AND_BLIND_RETRY"}
        if set(repair_policy_order) != allowed_repairs or len(repair_policy_order) != 2:
            raise ValueError("repair_policy_order must contain each repair policy exactly once")

        initial_calls: dict[str, ModelCall] = {}
        for arm in initial_arm_order:
            prompt_name = "base_generation.txt" if arm == "LLM_ONLY" else "constraint_generation.txt"
            initial_calls[arm] = self.adapter.generate(
                request=request,
                visible_scene=model_scene,
                prompt=self._prompt(prompt_name),
                semantic_attempt=0,
            )
        base = initial_calls["LLM_ONLY"]
        constrained = initial_calls["CONSTRAINT_IN_PROMPT"]

        results: dict[str, PolicyOutcome] = {
            "LLM_ONLY": self._ungated("LLM_ONLY", base),
            "CONSTRAINT_IN_PROMPT": self._ungated("CONSTRAINT_IN_PROMPT", constrained),
            "VALIDATE_AND_BLOCK": self._gated(policy="VALIDATE_AND_BLOCK", request=request, scene=scene, initial=base),
        }
        for policy in repair_policy_order:
            results[policy] = self._gated(policy=policy, request=request, scene=scene, initial=base)
        return {policy: results[policy] for policy in POLICIES}
