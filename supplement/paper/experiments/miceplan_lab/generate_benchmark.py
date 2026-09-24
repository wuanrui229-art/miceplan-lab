from __future__ import annotations

import copy
import hashlib
import json
import math
import random
from collections import Counter
from pathlib import Path
from typing import Any

from shapely.geometry import Polygon, box

from . import DATASET_VERSION, GENERATOR_VERSION, ORACLE_VERSION, PROTOCOL_VERSION
from .contracts import COMPLEXITIES, OPERATION_FAMILIES, UNKNOWN_STRESS_CLASSES, write_schemas
from .oracle import apply_ir, intent_correct, validate_candidate


SEED = 20260720
ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "miceplan_lab_v1_1"

HARD_CONSTRAINTS = [
    "within_boundary",
    "no_overlap",
    "avoid_protected_polygons",
    "preserve_sold_and_locked",
    "unique_identifiers",
]

TEST_STRESS_BY_OPERATION: dict[str, list[str]] = {
    "ADD_BOOTH": [
        "MISSING_EVIDENCE", "FEASIBLE_CONTROL", "BOUNDARY", "MISSING_EVIDENCE",
        "FEASIBLE_CONTROL", "OVERLAP", "PROTECTED_POLYGON", "MISSING_EVIDENCE",
        "BOUNDARY", "OVERLAP", "PROTECTED_POLYGON", "MISSING_EVIDENCE",
    ],
    "MOVE_BOOTH": [
        "MISSING_EVIDENCE", "BOUNDARY", "PROTECTED_POLYGON", "AMBIGUOUS_TARGET",
        "FEASIBLE_CONTROL", "OVERLAP", "LOCKED_MUTATION", "MISSING_EVIDENCE",
        "FEASIBLE_CONTROL", "BOUNDARY", "OVERLAP", "PROTECTED_POLYGON",
    ],
    "RESIZE_BOOTH": [
        "MISSING_EVIDENCE", "BOUNDARY", "LOCKED_MUTATION", "AMBIGUOUS_TARGET",
        "FEASIBLE_CONTROL", "OVERLAP", "LOCKED_MUTATION", "MISSING_EVIDENCE",
        "FEASIBLE_CONTROL", "BOUNDARY", "OVERLAP", "LOCKED_MUTATION",
    ],
    "REMOVE_BOOTH": [
        "FEASIBLE_CONTROL", "LOCKED_MUTATION", "AMBIGUOUS_TARGET", "FEASIBLE_CONTROL",
        "FEASIBLE_CONTROL", "LOCKED_MUTATION", "AMBIGUOUS_TARGET", "FEASIBLE_CONTROL",
        "FEASIBLE_CONTROL", "LOCKED_MUTATION", "AMBIGUOUS_TARGET", "FEASIBLE_CONTROL",
    ],
    "SPLIT_BOOTH": [
        "FEASIBLE_CONTROL", "BOUNDARY", "LOCKED_MUTATION", "AMBIGUOUS_TARGET",
        "FEASIBLE_CONTROL", "OVERLAP", "LOCKED_MUTATION", "MISSING_EVIDENCE",
        "FEASIBLE_CONTROL", "OVERLAP", "OVERLAP", "PROTECTED_POLYGON",
    ],
    "RESERVE_AISLE": [
        "FEASIBLE_CONTROL", "BOUNDARY", "PROTECTED_POLYGON", "AMBIGUOUS_TARGET",
        "FEASIBLE_CONTROL", "BOUNDARY", "PROTECTED_POLYGON", "AMBIGUOUS_TARGET",
        "FEASIBLE_CONTROL", "PROTECTED_POLYGON", "PROTECTED_POLYGON", "AMBIGUOUS_TARGET",
    ],
}

DEV_STRESS_BY_CELL: dict[tuple[str, str], str] = {
    (operation, "C1"): "FEASIBLE_CONTROL" for operation in OPERATION_FAMILIES
}
DEV_STRESS_BY_CELL.update(
    {
        ("ADD_BOOTH", "C2"): "OVERLAP",
        ("MOVE_BOOTH", "C2"): "BOUNDARY",
        ("RESIZE_BOOTH", "C2"): "LOCKED_MUTATION",
        ("REMOVE_BOOTH", "C2"): "LOCKED_MUTATION",
        ("SPLIT_BOOTH", "C2"): "OVERLAP",
        ("RESERVE_AISLE", "C2"): "PROTECTED_POLYGON",
        ("ADD_BOOTH", "C3"): "MISSING_EVIDENCE",
        ("MOVE_BOOTH", "C3"): "AMBIGUOUS_TARGET",
        ("RESIZE_BOOTH", "C3"): "MISSING_EVIDENCE",
        ("REMOVE_BOOTH", "C3"): "AMBIGUOUS_TARGET",
        ("SPLIT_BOOTH", "C3"): "MISSING_EVIDENCE",
        ("RESERVE_AISLE", "C3"): "AMBIGUOUS_TARGET",
    }
)


def rectangle(x: float, y: float, width: float, height: float) -> list[list[float]]:
    return [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]


def operation(
    operation_type: str,
    *,
    target_ids: list[str] | None = None,
    count: int | None = None,
    width: float | None = None,
    height: float | None = None,
    x: float | None = None,
    y: float | None = None,
    region: str | None = None,
    booth_type: str | None = None,
) -> dict[str, Any]:
    return {
        "type": operation_type,
        "target_ids": target_ids or [],
        "count": count,
        "width": width,
        "height": height,
        "x": x,
        "y": y,
        "region": region,
        "booth_type": booth_type,
    }


def make_ir(request_id: str, operations: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "source_layout_version": "v1",
        "language": "en",
        "operations": operations,
        "hard_constraints": list(HARD_CONSTRAINTS),
        "preferences": [],
        "assumptions": [],
        "unresolved_references": [],
        "requires_confirmation": False,
    }


def _boundary_for(index: int) -> list[list[float]]:
    boundaries = [
        [[0, 0], [40, 0], [40, 30], [0, 30]],
        [[0, 0], [44, 0], [44, 18], [30, 18], [30, 32], [0, 32]],
        [[0, 0], [42, 0], [42, 30], [0, 30]],
        [[0, 0], [48, 0], [48, 34], [0, 34]],
        [[0, 0], [46, 0], [46, 19], [31, 19], [31, 33], [0, 33]],
        [[0, 0], [46, 0], [46, 33], [15, 33], [15, 19], [0, 19]],
        [[0, 0], [50, 0], [50, 34], [33, 34], [33, 24], [18, 24], [18, 34], [0, 34]],
        [[0, 0], [54, 0], [54, 36], [0, 36]],
    ]
    return boundaries[index]


def _protected_objects(boundary_points: list[list[float]], index: int) -> tuple[list[dict], list[dict], list[dict]]:
    boundary = Polygon(boundary_points)
    min_x, min_y, max_x, max_y = boundary.bounds
    fixed_aisles = [
        {"id": f"scene-{index + 1}-aisle-main", "type": "fixed_aisle", "polygon": rectangle(5, 13, min(24, max_x - 10), 3)}
    ]
    exits = [
        {"id": f"scene-{index + 1}-exit-west", "type": "exit_clearance", "polygon": rectangle(min_x, 9, 3, 4)},
        {"id": f"scene-{index + 1}-exit-east", "type": "exit_clearance", "polygon": rectangle(max_x - 3, 3, 3, 4)},
    ]
    obstacle_candidates = [
        rectangle(20 + index % 3, 6, 2, 2),
        rectangle(26, 19, 2, 2),
        rectangle(10, 19, 2, 2),
    ]
    obstacles: list[dict] = []
    for obstacle_index, points in enumerate(obstacle_candidates):
        polygon = Polygon(points)
        if boundary.covers(polygon):
            obstacles.append({"id": f"scene-{index + 1}-column-{obstacle_index + 1}", "type": "column", "polygon": points})
        if len(obstacles) == 2:
            break
    return obstacles, fixed_aisles, exits


def _place_source_booths(scene_stub: dict[str, Any], index: int) -> list[dict[str, Any]]:
    boundary = Polygon(scene_stub["boundary"])
    protected = [Polygon(item["polygon"]) for item in scene_stub["obstacles"] + scene_stub["fixed_aisles"] + scene_stub["exits"]]
    positions = [(x, y) for y in (2, 7, 18, 23, 28) for x in (3, 9, 15, 21, 27, 33, 39, 45)]
    booths: list[dict[str, Any]] = []
    prefix = chr(ord("A") + index)
    for x, y in positions:
        shape = box(x, y, x + 4, y + 3)
        if not boundary.covers(shape):
            continue
        if any(shape.intersection(area).area > 1e-8 for area in protected):
            continue
        if any(shape.intersection(box(item["x"], item["y"], item["x"] + item["width"], item["y"] + item["height"])).area > 1e-8 for item in booths):
            continue
        booth_index = len(booths)
        status = "sold" if booth_index == 0 else "locked" if booth_index == 1 else "reserved" if booth_index == 7 else "available"
        booths.append(
            {
                "id": f"scene-{index + 1}-booth-{booth_index + 1:02d}",
                "number": f"{prefix}{101 + booth_index}",
                "x": float(x),
                "y": float(y),
                "width": 4.0,
                "height": 3.0,
                "status": status,
                "type": "standard",
            }
        )
        if len(booths) == 12:
            break
    if len(booths) < 10:
        raise RuntimeError(f"Scene {index + 1} has only {len(booths)} valid booth positions")
    return booths


def make_scenes() -> list[dict[str, Any]]:
    scenes: list[dict[str, Any]] = []
    for index in range(8):
        boundary = _boundary_for(index)
        obstacles, fixed_aisles, exits = _protected_objects(boundary, index)
        scene: dict[str, Any] = {
            "scene_id": f"{'dev' if index < 2 else 'test'}-scene-{index + 1:02d}",
            "split": "development" if index < 2 else "test",
            "version": "v1",
            "unit": "m",
            "boundary": boundary,
            "booths": [],
            "obstacles": obstacles,
            "fixed_aisles": fixed_aisles,
            "exits": exits,
            "complexity_features": {},
        }
        scene["booths"] = _place_source_booths(scene, index)
        scene["complexity_features"] = {
            "boundary_vertices": len(boundary),
            "booth_count": len(scene["booths"]),
            "protected_polygon_count": len(obstacles) + len(fixed_aisles) + len(exits),
        }
        result = validate_candidate(scene, copy.deepcopy(scene))
        if result.status != "PASS":
            raise RuntimeError(f"Source scene failed oracle audit: {scene['scene_id']} {result.rule_ids}")
        scenes.append(scene)
    return scenes


def _editable(scene: dict[str, Any]) -> list[dict[str, Any]]:
    return [booth for booth in scene["booths"] if booth["status"] in {"available", "reserved"}]


def _locked(scene: dict[str, Any]) -> dict[str, Any]:
    return next(booth for booth in scene["booths"] if booth["status"] == "locked")


def _find_passing_ir(scene: dict[str, Any], task_id: str, candidates: list[list[dict[str, Any]]]) -> dict[str, Any]:
    for candidate_operations in candidates:
        candidate_ir = make_ir(f"{task_id}-witness", candidate_operations)
        if apply_ir(scene, candidate_ir).status == "PASS":
            return candidate_ir
    raise RuntimeError(f"No passing witness found for {task_id}")


def _grid_anchors(scene: dict[str, Any], width: float, height: float, zone: str | None = None) -> list[tuple[float, float]]:
    boundary = Polygon(scene["boundary"])
    min_x, min_y, max_x, max_y = boundary.bounds
    anchors = [(float(x), float(y)) for y in range(math.floor(min_y) + 1, math.ceil(max_y - height)) for x in range(math.floor(min_x) + 1, math.ceil(max_x - width))]
    if zone == "east":
        anchors = [item for item in anchors if item[0] >= min_x + 0.60 * (max_x - min_x)]
        anchors.sort(key=lambda item: (-item[0], item[1]))
    elif zone == "south":
        anchors = [item for item in anchors if item[1] >= min_y + 0.60 * (max_y - min_y)]
        anchors.sort(key=lambda item: (-item[1], item[0]))
    return anchors


def make_witness(
    scene: dict[str, Any],
    task_id: str,
    family: str,
    complexity: str,
    stress: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    editable = _editable(scene)
    target = max(editable, key=lambda item: item["x"]) if family == "RESIZE_BOOTH" and stress == "BOUNDARY" else editable[0]
    donor = next(item for item in editable if item["id"] != target["id"])
    requirements: dict[str, Any] = {"required_operation_types": [family]}

    if complexity == "C3":
        if family == "ADD_BOOTH":
            candidates = [
                [
                    operation("REMOVE_BOOTH", target_ids=[donor["id"]]),
                    operation("ADD_BOOTH", count=1, width=3, height=3, x=x, y=y, booth_type="standard"),
                ]
                for x, y in _grid_anchors(scene, 3, 3, "east")
            ]
            requirements.update(
                {
                    "required_operation_types": ["REMOVE_BOOTH", "ADD_BOOTH"],
                    "required_targets_by_operation": {"REMOVE_BOOTH": [donor["id"]]},
                    "count": 1,
                    "width": 3,
                    "height": 3,
                    "goal_zone": "east",
                }
            )
        elif family == "MOVE_BOOTH":
            candidates = [
                [
                    operation("REMOVE_BOOTH", target_ids=[donor["id"]]),
                    operation("MOVE_BOOTH", target_ids=[target["id"]], x=x, y=y),
                ]
                for x, y in _grid_anchors(scene, target["width"], target["height"], "east")
            ]
            requirements.update(
                {
                    "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"],
                    "required_targets_by_operation": {"REMOVE_BOOTH": [donor["id"]]},
                    "required_target_ids": [target["id"]],
                    "goal_zone": "east",
                }
            )
        elif family == "RESIZE_BOOTH":
            candidates = [
                [
                    operation("REMOVE_BOOTH", target_ids=[donor["id"]]),
                    operation("MOVE_BOOTH", target_ids=[target["id"]], x=x, y=y),
                    operation("RESIZE_BOOTH", target_ids=[target["id"]], width=3, height=3),
                ]
                for x, y in _grid_anchors(scene, 3, 3, "east")
            ]
            requirements.update(
                {
                    "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH", "RESIZE_BOOTH"],
                    "required_targets_by_operation": {
                        "REMOVE_BOOTH": [donor["id"]],
                        "MOVE_BOOTH": [target["id"]],
                    },
                    "required_target_ids": [target["id"]],
                    "width": 3,
                    "height": 3,
                    "goal_zone": "east",
                    "goal_zone_operation_type": "MOVE_BOOTH",
                }
            )
        elif family == "REMOVE_BOOTH":
            candidates = [[
                operation("REMOVE_BOOTH", target_ids=[target["id"]]),
                operation("MOVE_BOOTH", target_ids=[donor["id"]], x=target["x"], y=target["y"]),
            ]]
            requirements.update(
                {
                    "required_operation_types": ["REMOVE_BOOTH", "MOVE_BOOTH"],
                    "required_targets_by_operation": {"MOVE_BOOTH": [donor["id"]]},
                    "required_target_ids": [target["id"]],
                    "required_anchor": [target["x"], target["y"]],
                    "anchor_operation_type": "MOVE_BOOTH",
                }
            )
        elif family == "SPLIT_BOOTH":
            candidates = [
                [
                    operation("REMOVE_BOOTH", target_ids=[donor["id"]]),
                    operation("SPLIT_BOOTH", target_ids=[target["id"]], count=2, width=2, height=3, x=x, y=y, booth_type="custom"),
                ]
                for x, y in _grid_anchors(scene, 4, 3, "east")
            ]
            requirements.update(
                {
                    "required_operation_types": ["REMOVE_BOOTH", "SPLIT_BOOTH"],
                    "required_targets_by_operation": {"REMOVE_BOOTH": [donor["id"]]},
                    "required_target_ids": [target["id"]],
                    "count": 2,
                    "width": 2,
                    "height": 3,
                    "goal_zone": "east",
                }
            )
        else:
            candidates = [
                [
                    operation("REMOVE_BOOTH", target_ids=[donor["id"]]),
                    operation("RESERVE_AISLE", x=x, y=y, width=4, height=3),
                ]
                for x, y in _grid_anchors(scene, 4, 3, "south")
            ]
            requirements.update(
                {
                    "required_operation_types": ["REMOVE_BOOTH", "RESERVE_AISLE"],
                    "required_targets_by_operation": {"REMOVE_BOOTH": [donor["id"]]},
                    "width": 4,
                    "height": 3,
                    "goal_zone": "south",
                }
            )
        witness = _find_passing_ir(scene, task_id, candidates)
        return witness, requirements

    if family == "ADD_BOOTH":
        candidates = [[operation("ADD_BOOTH", count=1, width=3, height=3, x=x, y=y, booth_type="standard")] for x, y in _grid_anchors(scene, 3, 3, "east")]
        requirements.update({"count": 1, "width": 3, "height": 3, "goal_zone": "east"})
    elif family == "MOVE_BOOTH":
        candidates = [[operation("MOVE_BOOTH", target_ids=[target["id"]], x=x, y=y)] for x, y in _grid_anchors(scene, target["width"], target["height"], "east")]
        requirements.update({"required_target_ids": [target["id"]], "goal_zone": "east"})
    elif family == "RESIZE_BOOTH":
        candidates = [[operation("RESIZE_BOOTH", target_ids=[target["id"]], width=3, height=3)]]
        requirements.update({"required_target_ids": [target["id"]], "width": 3, "height": 3})
    elif family == "REMOVE_BOOTH":
        candidates = [[operation("REMOVE_BOOTH", target_ids=[target["id"]])]]
        requirements.update({"required_target_ids": [target["id"]]})
    elif family == "SPLIT_BOOTH":
        candidates = [[operation("SPLIT_BOOTH", target_ids=[target["id"]], count=2, width=2, height=3, x=target["x"], y=target["y"], booth_type="custom")]]
        requirements.update({"required_target_ids": [target["id"]], "count": 2, "width": 2, "height": 3})
    else:
        candidates = [[operation("RESERVE_AISLE", x=x, y=y, width=2, height=5)] for x, y in _grid_anchors(scene, 2, 5, "south")]
        requirements.update({"width": 2, "height": 5, "goal_zone": "south"})
    witness = _find_passing_ir(scene, task_id, candidates)
    return witness, requirements


def _primary_operation(ir: dict[str, Any], family: str) -> dict[str, Any]:
    return next(item for item in ir["operations"] if item["type"] == family)


def make_probe(scene: dict[str, Any], task_id: str, family: str, stress: str, witness: dict[str, Any]) -> dict[str, Any] | None:
    if stress in {"FEASIBLE_CONTROL", "AMBIGUOUS_TARGET", "MISSING_EVIDENCE"}:
        return None

    boundary = Polygon(scene["boundary"])
    min_x, min_y, max_x, max_y = boundary.bounds
    primary_index = next(index for index, item in enumerate(witness["operations"]) if item["type"] == family)
    geometry_index = primary_index
    if family == "RESIZE_BOOTH":
        move_index = next(
            (index for index, item in enumerate(witness["operations"]) if item["type"] == "MOVE_BOOTH"),
            None,
        )
        if move_index is not None:
            geometry_index = move_index

    removed_ids = {
        target_id
        for item in witness["operations"]
        if item["type"] == "REMOVE_BOOTH"
        for target_id in item.get("target_ids", [])
    }
    primary = witness["operations"][primary_index]
    excluded_ids = removed_ids | set(primary.get("target_ids", []))
    other_booths = [
        booth
        for booth in scene["booths"]
        if booth["id"] not in excluded_ids and booth["status"] in {"available", "reserved"}
    ]
    locked = _locked(scene)

    candidates: list[dict[str, Any]] = []

    def cloned() -> dict[str, Any]:
        candidate = copy.deepcopy(witness)
        candidate["request_id"] = f"{task_id}-probe"
        return candidate

    if stress == "LOCKED_MUTATION":
        for operation_index in reversed(range(len(witness["operations"]))):
            source_operation = witness["operations"][operation_index]
            if source_operation["type"] not in {"MOVE_BOOTH", "RESIZE_BOOTH", "REMOVE_BOOTH", "SPLIT_BOOTH"}:
                continue
            candidate = cloned()
            mutated = candidate["operations"][operation_index]
            mutated["target_ids"] = [locked["id"]]
            if mutated["type"] == "SPLIT_BOOTH":
                mutated["x"], mutated["y"] = locked["x"], locked["y"]
            candidates.append(candidate)

    elif stress == "BOUNDARY":
        geometry = witness["operations"][geometry_index]
        if geometry.get("x") is not None and geometry.get("y") is not None:
            for x, y in (
                (max_x + 2, max_y + 2),
                (max_x + 2, min_y + 1),
                (min_x - 10, min_y + 1),
                (min_x + 1, max_y + 2),
            ):
                candidate = cloned()
                candidate["operations"][geometry_index]["x"] = float(x)
                candidate["operations"][geometry_index]["y"] = float(y)
                candidates.append(candidate)
        else:
            for width in range(4, math.ceil(max_x - min_x) * 2 + 1):
                candidate = cloned()
                candidate["operations"][primary_index]["width"] = float(width)
                candidates.append(candidate)
            for height in range(4, math.ceil(max_y - min_y) * 2 + 1):
                candidate = cloned()
                candidate["operations"][primary_index]["height"] = float(height)
                candidates.append(candidate)

    elif stress == "OVERLAP":
        geometry = witness["operations"][geometry_index]
        if geometry.get("x") is not None and geometry.get("y") is not None:
            for booth in other_booths:
                candidate = cloned()
                candidate["operations"][geometry_index]["x"] = float(booth["x"])
                candidate["operations"][geometry_index]["y"] = float(booth["y"])
                candidates.append(candidate)
        else:
            for width in range(4, math.ceil(max_x - min_x) + 1):
                for height in range(3, min(12, math.ceil(max_y - min_y)) + 1):
                    candidate = cloned()
                    candidate["operations"][primary_index]["width"] = float(width)
                    candidate["operations"][primary_index]["height"] = float(height)
                    candidates.append(candidate)

    elif stress == "PROTECTED_POLYGON":
        if family == "RESERVE_AISLE":
            for booth in other_booths:
                candidate = cloned()
                candidate["operations"][geometry_index]["x"] = float(booth["x"])
                candidate["operations"][geometry_index]["y"] = float(booth["y"])
                candidates.append(candidate)
        else:
            protected_items = scene["obstacles"] + scene["fixed_aisles"] + scene["exits"]
            for item in protected_items:
                protected_min_x, protected_min_y, protected_max_x, protected_max_y = Polygon(item["polygon"]).bounds
                for x in range(math.floor(protected_min_x), math.ceil(protected_max_x) + 1):
                    for y in range(math.floor(protected_min_y), math.ceil(protected_max_y) + 1):
                        candidate = cloned()
                        candidate["operations"][geometry_index]["x"] = float(x)
                        candidate["operations"][geometry_index]["y"] = float(y)
                        candidates.append(candidate)

    for probe_ir in candidates:
        result = apply_ir(scene, probe_ir)
        if result.status == "FAIL" and tuple(result.rule_ids) == (stress,):
            return {"ir": probe_ir, "expected_rule_ids": [stress]}

    observed = [apply_ir(scene, candidate).rule_ids for candidate in candidates[:10]]
    raise RuntimeError(
        f"Probe {task_id} has no exact single-fault {stress} candidate; sampled={observed}"
    )


def _booth_number(scene: dict[str, Any], object_id: str) -> str:
    return next(booth["number"] for booth in scene["booths"] if booth["id"] == object_id)


def _describe_primary(scene: dict[str, Any], family: str, requirements: dict[str, Any], language: str) -> str:
    targets = requirements.get("required_target_ids", [])
    number = _booth_number(scene, targets[0]) if targets else None
    if language == "zh":
        templates = {
            "ADD_BOOTH": f"在东侧开放区域新增 {requirements.get('count', 1)} 个 {requirements.get('width', 3):g}×{requirements.get('height', 3):g} 米标准展位",
            "MOVE_BOOTH": f"把 {number} 移到东侧开放区域",
            "RESIZE_BOOTH": f"把 {number} 调整为 {requirements.get('width', 3):g}×{requirements.get('height', 3):g} 米",
            "REMOVE_BOOTH": f"删除可用展位 {number}",
            "SPLIT_BOOTH": f"把 {number} 拆成 {requirements.get('count', 2)} 个 {requirements.get('width', 2):g}×{requirements.get('height', 3):g} 米展位",
            "RESERVE_AISLE": f"在南侧开放区域预留一条 {requirements.get('width', 2):g}×{requirements.get('height', 5):g} 米通道",
        }
    else:
        templates = {
            "ADD_BOOTH": f"Add {requirements.get('count', 1)} standard booth of {requirements.get('width', 3):g} x {requirements.get('height', 3):g} m in the open east area",
            "MOVE_BOOTH": f"Move {number} to the open east area",
            "RESIZE_BOOTH": f"Resize {number} to {requirements.get('width', 3):g} x {requirements.get('height', 3):g} m",
            "REMOVE_BOOTH": f"Remove available booth {number}",
            "SPLIT_BOOTH": f"Split {number} into {requirements.get('count', 2)} booths of {requirements.get('width', 2):g} x {requirements.get('height', 3):g} m",
            "RESERVE_AISLE": f"Reserve a {requirements.get('width', 2):g} x {requirements.get('height', 5):g} m aisle in the open south area",
        }
    return templates[family]


def render_request(scene: dict[str, Any], family: str, complexity: str, stress: str, requirements: dict[str, Any], witness: dict[str, Any] | None, language: str) -> str:
    if stress == "AMBIGUOUS_TARGET":
        if language == "zh":
            templates = {
                "ADD_BOOTH": "在入口旁边新增一个 3×3 米标准展位。",
                "MOVE_BOOTH": "把入口旁边的一个展位移到东侧开放区域。",
                "RESIZE_BOOTH": "把入口旁边的一个展位调整为 3×3 米。",
                "REMOVE_BOOTH": "删除入口旁边的一个展位。",
                "SPLIT_BOOTH": "把入口旁边的一个展位拆成两个 2×3 米展位。",
                "RESERVE_AISLE": "在入口旁边预留一条 2×5 米通道。",
            }
        else:
            templates = {
                "ADD_BOOTH": "Add one 3 x 3 m standard booth beside the entrance.",
                "MOVE_BOOTH": "Move a booth beside the entrance to the open east area.",
                "RESIZE_BOOTH": "Resize a booth beside the entrance to 3 x 3 m.",
                "REMOVE_BOOTH": "Remove a booth beside the entrance.",
                "SPLIT_BOOTH": "Split a booth beside the entrance into two 2 x 3 m booths.",
                "RESERVE_AISLE": "Reserve a 2 x 5 m aisle beside the entrance.",
            }
        return templates[family]
    if stress == "MISSING_EVIDENCE":
        target = _editable(scene)[0]
        if language == "zh":
            templates = {
                "ADD_BOOTH": "在东侧开放区域新增一个占 1×1 网格单元的标准展位。",
                "MOVE_BOOTH": f"把 {target['number']} 向东移动一个网格单元。",
                "RESIZE_BOOTH": f"把 {target['number']} 的宽度增加一个网格单元，高度保持不变。",
                "REMOVE_BOOTH": f"删除距离 {target['number']} 向东一个网格单元位置的可用展位。",
                "SPLIT_BOOTH": f"把 {target['number']} 拆成两个等大展位，每个宽一个网格单元，高度保持不变。",
                "RESERVE_AISLE": "在南侧开放区域预留一条宽一个网格单元、长两个网格单元的通道。",
            }
        else:
            templates = {
                "ADD_BOOTH": "Add one standard booth occupying 1 x 1 grid cell in the open east area.",
                "MOVE_BOOTH": f"Move {target['number']} one grid cell east.",
                "RESIZE_BOOTH": f"Increase the width of {target['number']} by one grid cell and keep its height unchanged.",
                "REMOVE_BOOTH": f"Remove the available booth located one grid cell east of {target['number']}.",
                "SPLIT_BOOTH": f"Split {target['number']} into two equal booths, each one grid cell wide with unchanged height.",
                "RESERVE_AISLE": "Reserve an aisle one grid cell wide and two grid cells long in the open south area.",
            }
        return templates[family]

    if complexity == "C3" and witness is not None:
        primary_targets = requirements.get("required_target_ids", [])
        target_number = _booth_number(scene, primary_targets[0]) if primary_targets else None
        operation_targets = requirements.get("required_targets_by_operation", {})
        donor_ids = operation_targets.get("REMOVE_BOOTH", [])
        donor_number = _booth_number(scene, donor_ids[0]) if donor_ids else None
        mover_ids = operation_targets.get("MOVE_BOOTH", [])
        mover_number = _booth_number(scene, mover_ids[0]) if mover_ids else None
        if language == "zh":
            descriptions = {
                "ADD_BOOTH": f"先删除 {donor_number}，再在东侧开放区域新增一个 3×3 米标准展位。",
                "MOVE_BOOTH": f"先删除 {donor_number}，再把 {target_number} 移到东侧开放区域。",
                "RESIZE_BOOTH": f"先删除 {donor_number}，再把 {target_number} 移到东侧开放区域并调整为 3×3 米。",
                "REMOVE_BOOTH": f"先删除 {target_number}，再把 {mover_number} 移到刚释放的位置。",
                "SPLIT_BOOTH": f"先删除 {donor_number}，再把 {target_number} 拆成两个 2×3 米展位并放在东侧开放区域。",
                "RESERVE_AISLE": f"先删除 {donor_number}，再在南侧开放区域预留一条 4×3 米通道。",
            }
        else:
            descriptions = {
                "ADD_BOOTH": f"Remove {donor_number}, then add one 3 x 3 m standard booth in the open east area.",
                "MOVE_BOOTH": f"Remove {donor_number}, then move {target_number} to the open east area.",
                "RESIZE_BOOTH": f"Remove {donor_number}, then move {target_number} to the open east area and resize it to 3 x 3 m.",
                "REMOVE_BOOTH": f"Remove {target_number}, then move {mover_number} to the newly released position.",
                "SPLIT_BOOTH": f"Remove {donor_number}, then split {target_number} into two 2 x 3 m booths in the open east area.",
                "RESERVE_AISLE": f"Remove {donor_number}, then reserve a 4 x 3 m aisle in the open south area.",
            }
        base = descriptions[family]
    else:
        base = _describe_primary(scene, family, requirements, language) + ("。" if language == "zh" else ".")

    if stress == "LOCKED_MUTATION":
        return base + ("不得改动已售或锁定展位。" if language == "zh" else " Do not modify sold or locked booths.")
    return base


def build_task(task_index: int, split: str, scene: dict[str, Any], family: str, complexity: str, stress: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    task_id = f"task-{task_index:04d}"
    context_mask = {
        "hide_unit": stress == "MISSING_EVIDENCE",
        "hide_scale": stress == "MISSING_EVIDENCE",
        "hide_disambiguating_labels": stress == "AMBIGUOUS_TARGET",
    }
    if stress in UNKNOWN_STRESS_CLASSES:
        witness = None
        requirements = {"required_operation_types": [family]}
        probe = None
        admissible = "DEFER"
    else:
        witness, requirements = make_witness(scene, task_id, family, complexity, stress)
        probe = make_probe(scene, task_id, family, stress, witness)
        admissible = "VALID_EDIT"
        result = apply_ir(scene, witness)
        gold_stub = {
            "intent_requirements": requirements,
            "admissible_final_outcome": admissible,
            "intended_operation_family": family,
        }
        if not intent_correct(scene, gold_stub, witness, result):
            raise RuntimeError(f"Witness lost intent for {task_id}")

    gold = {
        "semantic_task_id": task_id,
        "scene_id": scene["scene_id"],
        "intended_operation_family": family,
        "complexity": complexity,
        "intent_requirements": requirements,
        "target_stress_class": stress,
        "admissible_final_outcome": admissible,
        "valid_witness_ir": witness,
        "invalid_probe_ir": probe,
        "generator_version": GENERATOR_VERSION,
        "oracle_version": ORACLE_VERSION,
        "machine_audit": "PENDING",
        "author_review": "PENDING",
    }
    requests: list[dict[str, Any]] = []
    for language in ("zh", "en"):
        requests.append(
            {
                "request_id": f"{task_id}-{language}",
                "semantic_task_id": task_id,
                "split": split,
                "scene_id": scene["scene_id"],
                "language": language,
                "text": render_request(scene, family, complexity, stress, requirements, witness, language),
                "operation_family": family,
                "complexity": complexity,
                "pair_id": task_id,
                "context_mask": context_mask,
            }
        )
    return gold, requests


def build_benchmark() -> tuple[list[dict], list[dict], list[dict]]:
    scenes = make_scenes()
    dev_scenes = [scene for scene in scenes if scene["split"] == "development"]
    test_scenes = [scene for scene in scenes if scene["split"] == "test"]
    gold_rows: list[dict] = []
    request_rows: list[dict] = []
    task_index = 1
    test_scene_index = 0
    for family in OPERATION_FAMILIES:
        family_schedule = TEST_STRESS_BY_OPERATION[family]
        for complexity_index, complexity in enumerate(COMPLEXITIES):
            dev_scene = dev_scenes[(task_index + complexity_index) % len(dev_scenes)]
            dev_stress = DEV_STRESS_BY_CELL[(family, complexity)]
            gold, requests = build_task(task_index, "development", dev_scene, family, complexity, dev_stress)
            gold_rows.append(gold)
            request_rows.extend(requests)
            task_index += 1
            for stress in family_schedule[complexity_index * 4 : (complexity_index + 1) * 4]:
                scene = test_scenes[test_scene_index % len(test_scenes)]
                test_scene_index += 1
                gold, requests = build_task(task_index, "test", scene, family, complexity, stress)
                gold_rows.append(gold)
                request_rows.extend(requests)
                task_index += 1
    return scenes, request_rows, gold_rows


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    random.seed(SEED)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    schema_paths = write_schemas(OUTPUT / "schemas")
    scenes, requests, gold = build_benchmark()
    scenes_path = OUTPUT / "scenes.jsonl"
    requests_path = OUTPUT / "requests.jsonl"
    gold_path = OUTPUT / "gold.jsonl"
    write_jsonl(scenes_path, scenes)
    write_jsonl(requests_path, requests)
    write_jsonl(gold_path, gold)

    split_by_scene = Counter(scene["split"] for scene in scenes)
    split_by_request = Counter(row["split"] for row in requests)
    stress_by_test_task = Counter(row["target_stress_class"] for row in gold if next(request["split"] for request in requests if request["semantic_task_id"] == row["semantic_task_id"]) == "test")
    files = {path.name: {"sha256": sha256(path), "bytes": path.stat().st_size} for path in [scenes_path, requests_path, gold_path, *schema_paths.values()]}
    manifest = {
        "dataset": DATASET_VERSION,
        "protocol_version": PROTOCOL_VERSION,
        "generator_version": GENERATOR_VERSION,
        "oracle_version": ORACLE_VERSION,
        "created_date": "2026-07-20",
        "seed": SEED,
        "scene_count": len(scenes),
        "semantic_task_count": len(gold),
        "request_count": len(requests),
        "scene_split": dict(sorted(split_by_scene.items())),
        "request_split": dict(sorted(split_by_request.items())),
        "test_stress_strata": dict(sorted(stress_by_test_task.items())),
        "files": dict(sorted(files.items())),
        "formal_model_calls_started": False,
        "author_review_status": "PENDING",
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
