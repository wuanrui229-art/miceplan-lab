from __future__ import annotations

import copy
import math
from collections import Counter
from dataclasses import dataclass
from typing import Any

from shapely.geometry import Polygon, box

from . import ORACLE_VERSION


EPSILON_AREA = 1e-8


@dataclass(frozen=True)
class OracleResult:
    status: str
    rule_ids: tuple[str, ...]
    object_ids: tuple[str, ...]
    scene_after: dict[str, Any] | None
    details: tuple[str, ...]
    oracle_version: str = ORACLE_VERSION

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "rule_ids": list(self.rule_ids),
            "object_ids": list(self.object_ids),
            "scene_after": self.scene_after,
            "details": list(self.details),
            "oracle_version": self.oracle_version,
        }


def _polygon(points: list[list[float]] | tuple[tuple[float, float], ...]) -> Polygon:
    polygon = Polygon(points)
    if not polygon.is_valid or polygon.area <= EPSILON_AREA:
        raise ValueError("Oracle received an invalid or zero-area polygon")
    return polygon


def _booth_shape(booth: dict[str, Any]) -> Polygon:
    return box(
        float(booth["x"]),
        float(booth["y"]),
        float(booth["x"]) + float(booth["width"]),
        float(booth["y"]) + float(booth["height"]),
    )


def _polygon_object_shape(item: dict[str, Any]) -> Polygon:
    return _polygon(item["polygon"])


def _operation_targets(booths: list[dict[str, Any]], operation: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {booth["id"]: booth for booth in booths}
    return [by_id[target_id] for target_id in operation.get("target_ids", []) if target_id in by_id]


def _unknown(rule_id: str, message: str, object_ids: list[str] | None = None) -> OracleResult:
    return OracleResult(
        status="UNKNOWN",
        rule_ids=(rule_id,),
        object_ids=tuple(object_ids or []),
        scene_after=None,
        details=(message,),
    )


def _next_number(booths: list[dict[str, Any]], seed: int) -> str:
    existing = {booth["number"] for booth in booths}
    value = seed
    while f"LAB{value:03d}" in existing:
        value += 1
    return f"LAB{value:03d}"


def apply_ir(scene: dict[str, Any], ir: dict[str, Any]) -> OracleResult:
    """Apply an IR without importing any runtime-gate or solver implementation."""

    if ir.get("requires_confirmation") and not ir.get("operations"):
        return _unknown("DEFER", "The model explicitly requested clarification.")

    candidate = copy.deepcopy(scene)
    booths: list[dict[str, Any]] = candidate["booths"]
    generated_index = 1

    for operation_index, operation in enumerate(ir.get("operations", [])):
        operation_type = operation.get("type")
        requested_targets = list(operation.get("target_ids", []))
        targets = _operation_targets(booths, operation)

        if operation_type in {"MOVE_BOOTH", "RESIZE_BOOTH", "REMOVE_BOOTH", "SPLIT_BOOTH"}:
            if not requested_targets:
                return _unknown("TARGET", f"{operation_type} requires at least one target.")
            if len(targets) != len(requested_targets):
                missing = sorted(set(requested_targets) - {item["id"] for item in targets})
                return _unknown("TARGET", "At least one target is absent from the source scene.", missing)

        if operation_type == "MOVE_BOOTH":
            if operation.get("x") is None or operation.get("y") is None:
                return _unknown("MISSING_EVIDENCE", "MOVE_BOOTH requires explicit x and y in MICEPlan-Lab.", requested_targets)
            for target in targets:
                target["x"] = float(operation["x"])
                target["y"] = float(operation["y"])

        elif operation_type == "RESIZE_BOOTH":
            if operation.get("width") is None or operation.get("height") is None:
                return _unknown("MISSING_EVIDENCE", "RESIZE_BOOTH requires width and height.", requested_targets)
            for target in targets:
                target["width"] = float(operation["width"])
                target["height"] = float(operation["height"])

        elif operation_type == "REMOVE_BOOTH":
            removed = set(requested_targets)
            booths[:] = [booth for booth in booths if booth["id"] not in removed]

        elif operation_type == "ADD_BOOTH":
            required = (operation.get("count"), operation.get("width"), operation.get("height"), operation.get("x"), operation.get("y"))
            if any(value is None for value in required):
                return _unknown("MISSING_EVIDENCE", "ADD_BOOTH requires count, dimensions, and an explicit anchor.")
            count = int(operation["count"])
            width, height = float(operation["width"]), float(operation["height"])
            columns = max(1, math.ceil(math.sqrt(count)))
            for offset in range(count):
                row, column = divmod(offset, columns)
                booth = {
                    "id": f"oracle-op{operation_index}-booth{generated_index}",
                    "number": _next_number(booths, generated_index),
                    "x": float(operation["x"]) + column * width,
                    "y": float(operation["y"]) + row * height,
                    "width": width,
                    "height": height,
                    "status": "available",
                    "type": operation.get("booth_type") or "standard",
                }
                booths.append(booth)
                generated_index += 1

        elif operation_type == "SPLIT_BOOTH":
            required = (operation.get("count"), operation.get("width"), operation.get("height"), operation.get("x"), operation.get("y"))
            if any(value is None for value in required):
                return _unknown("MISSING_EVIDENCE", "SPLIT_BOOTH requires count, dimensions, and an explicit anchor.", requested_targets)
            removed = set(requested_targets)
            booths[:] = [booth for booth in booths if booth["id"] not in removed]
            count = int(operation["count"])
            width, height = float(operation["width"]), float(operation["height"])
            columns = max(1, math.ceil(math.sqrt(count)))
            for offset in range(count):
                row, column = divmod(offset, columns)
                booth = {
                    "id": f"oracle-op{operation_index}-split{generated_index}",
                    "number": _next_number(booths, generated_index),
                    "x": float(operation["x"]) + column * width,
                    "y": float(operation["y"]) + row * height,
                    "width": width,
                    "height": height,
                    "status": "available",
                    "type": operation.get("booth_type") or "standard",
                }
                booths.append(booth)
                generated_index += 1

        elif operation_type == "RESERVE_AISLE":
            required = (operation.get("x"), operation.get("y"), operation.get("width"), operation.get("height"))
            if any(value is None for value in required):
                return _unknown("MISSING_EVIDENCE", "RESERVE_AISLE requires x, y, width, and height.")
            x, y = float(operation["x"]), float(operation["y"])
            width, height = float(operation["width"]), float(operation["height"])
            candidate["fixed_aisles"].append(
                {
                    "id": f"oracle-op{operation_index}-aisle",
                    "type": "reserved_aisle",
                    "polygon": [[x, y], [x + width, y], [x + width, y + height], [x, y + height]],
                }
            )

        else:
            return _unknown("SCHEMA", f"Unsupported operation type: {operation_type}")

    return validate_candidate(scene, candidate)


def validate_candidate(source: dict[str, Any], candidate: dict[str, Any]) -> OracleResult:
    boundary = _polygon(candidate["boundary"])
    rules: list[str] = []
    objects: list[str] = []
    details: list[str] = []

    booth_shapes = [(booth, _booth_shape(booth)) for booth in candidate["booths"]]
    outside_booths = [booth["id"] for booth, shape in booth_shapes if not boundary.covers(shape)]

    protected_items = candidate.get("obstacles", []) + candidate.get("fixed_aisles", []) + candidate.get("exits", [])
    protected_shapes = [(item, _polygon_object_shape(item)) for item in protected_items]
    outside_protected = [item["id"] for item, shape in protected_shapes if not boundary.covers(shape)]
    if outside_booths or outside_protected:
        rules.append("BOUNDARY")
        objects.extend(outside_booths + outside_protected)
        details.append("At least one booth or protected polygon extends outside the hall boundary.")

    overlap_ids: list[str] = []
    for index, (first, first_shape) in enumerate(booth_shapes):
        for second, second_shape in booth_shapes[index + 1 :]:
            if first_shape.intersection(second_shape).area > EPSILON_AREA:
                overlap_ids.extend([first["id"], second["id"]])
    if overlap_ids:
        rules.append("OVERLAP")
        objects.extend(overlap_ids)
        details.append("At least one pair of booth interiors overlaps.")

    protected_collisions: list[str] = []
    for booth, booth_shape in booth_shapes:
        for item, protected_shape in protected_shapes:
            if booth_shape.intersection(protected_shape).area > EPSILON_AREA:
                protected_collisions.extend([booth["id"], item["id"]])
    if protected_collisions:
        rules.append("PROTECTED_POLYGON")
        objects.extend(protected_collisions)
        details.append("At least one booth intersects an obstacle, aisle, or exit-clearance polygon.")

    ids = [booth["id"] for booth in candidate["booths"]]
    numbers = [booth["number"] for booth in candidate["booths"]]
    duplicates = sorted({value for value in ids if ids.count(value) > 1} | {value for value in numbers if numbers.count(value) > 1})
    if duplicates:
        rules.append("DUPLICATE_IDENTIFIER")
        objects.extend(duplicates)
        details.append("Booth IDs and visible numbers must remain unique.")

    source_by_id = {booth["id"]: booth for booth in source["booths"]}
    candidate_by_id = {booth["id"]: booth for booth in candidate["booths"]}
    changed_locked = [
        object_id
        for object_id, before in source_by_id.items()
        if before.get("status") in {"sold", "locked"} and candidate_by_id.get(object_id) != before
    ]
    if changed_locked:
        rules.append("LOCKED_MUTATION")
        objects.extend(changed_locked)
        details.append("A sold or locked booth was changed or removed.")

    unique_rules = tuple(dict.fromkeys(rules))
    unique_objects = tuple(dict.fromkeys(objects))
    return OracleResult(
        status="FAIL" if unique_rules else "PASS",
        rule_ids=unique_rules,
        object_ids=unique_objects,
        scene_after=candidate,
        details=tuple(details),
    )


def correct_defer(ir: dict[str, Any]) -> bool:
    return bool(ir.get("requires_confirmation")) and not ir.get("operations") and bool(ir.get("unresolved_references"))


def intent_signature_correct(scene: dict[str, Any], gold: dict[str, Any], ir: dict[str, Any]) -> bool:
    """Check declared user intent without treating geometric validity as intent."""

    requirements = gold["intent_requirements"]
    if gold["admissible_final_outcome"] == "DEFER":
        return correct_defer(ir)

    operations = list(ir.get("operations", []))
    operation_types = [operation.get("type") for operation in operations]
    required_types = requirements.get("required_operation_types", [gold["intended_operation_family"]])
    if Counter(operation_types) != Counter(required_types):
        return False

    primary = next((operation for operation in operations if operation.get("type") == gold["intended_operation_family"]), None)
    if primary is None:
        return False
    required_targets = set(requirements.get("required_target_ids", []))
    primary_targets = set(primary.get("target_ids", []))
    if required_targets and primary_targets != required_targets:
        return False
    for operation_type, expected_target_ids in requirements.get("required_targets_by_operation", {}).items():
        matching_operations = [operation for operation in operations if operation.get("type") == operation_type]
        if len(matching_operations) != 1:
            return False
        if set(matching_operations[0].get("target_ids", [])) != set(expected_target_ids):
            return False
    for key in ("count", "width", "height"):
        expected = requirements.get(key)
        if expected is not None and primary.get(key) != expected:
            return False

    required_anchor = requirements.get("required_anchor")
    if required_anchor is not None:
        anchor_type = requirements.get("anchor_operation_type", gold["intended_operation_family"])
        anchor_operation = next((operation for operation in operations if operation.get("type") == anchor_type), None)
        if anchor_operation is None or anchor_operation.get("x") != required_anchor[0] or anchor_operation.get("y") != required_anchor[1]:
            return False

    goal_zone = requirements.get("goal_zone")
    if goal_zone:
        zone_operation_type = requirements.get("goal_zone_operation_type", gold["intended_operation_family"])
        zone_operation = next(
            (operation for operation in operations if operation.get("type") == zone_operation_type),
            None,
        )
        if zone_operation is None:
            return False
        boundary = _polygon(scene["boundary"])
        min_x, min_y, max_x, max_y = boundary.bounds
        centers: list[tuple[float, float]] = []
        if required_targets:
            source_by_id = {booth["id"]: booth for booth in scene["booths"]}
            for target_id in required_targets:
                booth = source_by_id.get(target_id)
                if booth is not None:
                    x = zone_operation.get("x") if zone_operation.get("x") is not None else booth["x"]
                    y = zone_operation.get("y") if zone_operation.get("y") is not None else booth["y"]
                    width = zone_operation.get("width") if zone_operation.get("width") is not None else booth["width"]
                    height = zone_operation.get("height") if zone_operation.get("height") is not None else booth["height"]
                    centers.append((float(x) + float(width) / 2, float(y) + float(height) / 2))
        elif zone_operation.get("x") is not None and zone_operation.get("y") is not None:
            centers.append(
                (
                    float(zone_operation["x"]) + float(zone_operation.get("width") or 0) / 2,
                    float(zone_operation["y"]) + float(zone_operation.get("height") or 0) / 2,
                )
            )
        if not centers:
            return False
        for center_x, center_y in centers:
            if goal_zone == "east" and center_x < min_x + 0.60 * (max_x - min_x):
                return False
            if goal_zone == "west" and center_x > min_x + 0.40 * (max_x - min_x):
                return False
            if goal_zone == "north" and center_y > min_y + 0.40 * (max_y - min_y):
                return False
            if goal_zone == "south" and center_y < min_y + 0.60 * (max_y - min_y):
                return False
    return True


def intent_correct(
    scene: dict[str, Any], gold: dict[str, Any], ir: dict[str, Any], result: OracleResult
) -> bool:
    if result.status != "PASS" or result.scene_after is None:
        return False
    return intent_signature_correct(scene, gold, ir)


def evaluate_candidate(scene: dict[str, Any], gold: dict[str, Any], ir: dict[str, Any]) -> dict[str, Any]:
    result = apply_ir(scene, ir)
    defer = correct_defer(ir)
    signature_correct = intent_signature_correct(scene, gold, ir)
    return {
        "oracle": result.to_dict(),
        "correct_defer": gold["admissible_final_outcome"] == "DEFER" and defer,
        "intent_signature_correct": signature_correct,
        "intent_correct": intent_correct(scene, gold, ir, result),
        "safe_task_success": gold["admissible_final_outcome"] == "VALID_EDIT"
        and intent_correct(scene, gold, ir, result),
    }
