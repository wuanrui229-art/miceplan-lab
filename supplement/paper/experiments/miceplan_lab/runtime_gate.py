from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Any

from miceplan.geometry import GeometryValidator
from miceplan.models import Booth, HallLayout, LayoutEditIR, ModelError, OperationType, PolygonObject


RULE_MAP = {
    "within_boundary": "BOUNDARY",
    "protected_polygons_within_boundary": "BOUNDARY",
    "no_overlap": "OVERLAP",
    "avoid_protected_polygons": "PROTECTED_POLYGON",
    "preserve_sold_and_locked": "LOCKED_MUTATION",
    "unique_identifiers": "DUPLICATE_IDENTIFIER",
    "operation_satisfaction": "OPERATION_SATISFACTION",
}


@dataclass(frozen=True)
class GateIssue:
    rule_id: str
    message_code: str
    object_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "message_code": self.message_code,
            "object_ids": list(self.object_ids),
        }


@dataclass(frozen=True)
class GateResult:
    status: str
    stage: str
    issues: tuple[GateIssue, ...]
    candidate: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "stage": self.stage,
            "issues": [issue.to_dict() for issue in self.issues],
            "candidate": self.candidate,
        }


def _unknown(rule_id: str, code: str, objects: list[str] | None = None, stage: str = "PRECONDITION") -> GateResult:
    return GateResult("UNKNOWN", stage, (GateIssue(rule_id, code, tuple(objects or [])),), None)


def _to_layout(scene: dict[str, Any]) -> HallLayout:
    return HallLayout.from_dict(
        {
            "hall_id": scene["scene_id"],
            "version": scene["version"],
            "unit": scene["unit"],
            "boundary": scene["boundary"],
            "booths": scene["booths"],
            "obstacles": scene["obstacles"],
            "fixed_aisles": scene["fixed_aisles"],
            "exits": scene["exits"],
        }
    )


def _next_number(booths: list[Booth], seed: int) -> str:
    existing = {booth.number for booth in booths}
    value = seed
    while f"LAB{value:03d}" in existing:
        value += 1
    return f"LAB{value:03d}"


def _compile_unchecked(source: HallLayout, ir: LayoutEditIR) -> HallLayout:
    booths = list(source.booths)
    fixed_aisles = list(source.fixed_aisles)
    generated_index = 1
    for operation_index, operation in enumerate(ir.operations):
        by_id = {booth.id: booth for booth in booths}
        targets = [by_id[target_id] for target_id in operation.target_ids if target_id in by_id]
        if len(targets) != len(operation.target_ids):
            raise LookupError("target_not_found")

        if operation.type == OperationType.MOVE_BOOTH:
            if not targets:
                raise LookupError("target_missing")
            if operation.x is None or operation.y is None:
                raise ValueError("position_missing")
            booths = [replace(booth, x=operation.x, y=operation.y) if booth.id in operation.target_ids else booth for booth in booths]

        elif operation.type == OperationType.RESIZE_BOOTH:
            if not targets:
                raise LookupError("target_missing")
            if operation.width is None or operation.height is None:
                raise ValueError("dimensions_missing")
            booths = [replace(booth, width=operation.width, height=operation.height) if booth.id in operation.target_ids else booth for booth in booths]

        elif operation.type == OperationType.REMOVE_BOOTH:
            if not targets:
                raise LookupError("target_missing")
            booths = [booth for booth in booths if booth.id not in operation.target_ids]

        elif operation.type in {OperationType.ADD_BOOTH, OperationType.SPLIT_BOOTH}:
            if operation.type == OperationType.SPLIT_BOOTH and not targets:
                raise LookupError("target_missing")
            if None in {operation.count, operation.width, operation.height, operation.x, operation.y}:
                raise ValueError("placement_evidence_missing")
            if operation.type == OperationType.SPLIT_BOOTH:
                booths = [booth for booth in booths if booth.id not in operation.target_ids]
            count = int(operation.count)
            columns = max(1, math.ceil(math.sqrt(count)))
            for offset in range(count):
                row, column = divmod(offset, columns)
                booth = Booth(
                    id=f"{ir.request_id}-op{operation_index}-booth{generated_index}",
                    number=_next_number(booths, generated_index),
                    x=float(operation.x) + column * float(operation.width),
                    y=float(operation.y) + row * float(operation.height),
                    width=float(operation.width),
                    height=float(operation.height),
                    status="available",
                    type=operation.booth_type or "standard",
                    source_version=source.version,
                )
                booths.append(booth)
                generated_index += 1

        elif operation.type == OperationType.RESERVE_AISLE:
            if None in {operation.x, operation.y, operation.width, operation.height}:
                raise ValueError("aisle_evidence_missing")
            x, y = float(operation.x), float(operation.y)
            width, height = float(operation.width), float(operation.height)
            fixed_aisles.append(
                PolygonObject(
                    id=f"{ir.request_id}-aisle-{operation_index}",
                    polygon=((x, y), (x + width, y), (x + width, y + height), (x, y + height)),
                    type="reserved_aisle",
                )
            )
        else:
            raise ValueError("unsupported_operation")

    return HallLayout(
        hall_id=source.hall_id,
        version=f"candidate-{ir.request_id}",
        unit=source.unit,
        boundary=source.boundary,
        booths=tuple(booths),
        obstacles=source.obstacles,
        exits=source.exits,
        fixed_aisles=tuple(fixed_aisles),
        parent_version=source.version,
        request_id=ir.request_id,
    )


class RuntimeGate:
    """Runtime policy gate. This class deliberately does not import the gold oracle."""

    def __init__(self) -> None:
        self.validator = GeometryValidator()

    def evaluate(self, scene: dict[str, Any], request: dict[str, Any], ir_payload: dict[str, Any] | None) -> GateResult:
        if ir_payload is None:
            return _unknown("SCHEMA", "missing_ir", stage="SCHEMA")
        try:
            ir = LayoutEditIR.from_dict(ir_payload)
        except (ModelError, TypeError, ValueError):
            return _unknown("SCHEMA", "invalid_ir", stage="SCHEMA")

        if ir.requires_confirmation and not ir.operations:
            objects = list(ir.unresolved_references)
            return _unknown("DEFER", "model_requested_clarification", objects)
        if not ir.operations:
            return _unknown("OPERATION", "empty_operations_without_defer")

        mask = request["context_mask"]
        if mask["hide_disambiguating_labels"]:
            return _unknown("TARGET", "target_evidence_masked")
        if mask["hide_scale"] or mask["hide_unit"]:
            return _unknown("MISSING_EVIDENCE", "scale_or_unit_masked")

        source = _to_layout(scene)
        try:
            candidate = _compile_unchecked(source, ir)
        except LookupError as exc:
            return _unknown("TARGET", str(exc))
        except ValueError as exc:
            return _unknown("MISSING_EVIDENCE", str(exc))

        report = self.validator.validate(source, candidate, ir)
        failed = [check for check in report.checks if not check.passed]
        if not failed:
            return GateResult("PASS", "GEOMETRY", (), candidate.to_dict())
        issues = tuple(
            GateIssue(
                rule_id=RULE_MAP.get(check.rule, check.rule.upper()),
                message_code=check.rule,
                object_ids=check.object_ids,
            )
            for check in failed
        )
        return GateResult("FAIL", "GEOMETRY", issues, candidate.to_dict())

