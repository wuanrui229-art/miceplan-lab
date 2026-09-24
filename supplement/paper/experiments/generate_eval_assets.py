from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SYSTEM_ROOT = ROOT / "system"
sys.path.insert(0, str(SYSTEM_ROOT))

from miceplan.geometry import GeometryValidator, rectangle_intersects_polygon, rectangle_within_polygon, rectangles_overlap
from miceplan.models import Booth, HallLayout, LayoutEditIR, Operation, OperationType, PolygonObject
from miceplan.solver import DeterministicLayoutSolver, SolveError


SEED = 20260715
DATASET_NAME = "MICEPlan-Eval-v1.1"
OUTPUT = ROOT / "data" / "miceplan_eval_v1_1"
HALL_COUNTS = {"simple_rectangular": 10, "obstacle_containing": 10, "irregular": 8, "tight_capacity": 6, "stress_capacity": 6}
REQUEST_COUNTS = {"simple": 48, "capacity_stress": 8, "compound": 24, "ambiguous": 20, "contradictory": 16, "revision": 20, "protected_object": 24}
DEVELOPMENT_REQUEST_COUNTS = {"simple": 10, "capacity_stress": 1, "compound": 5, "ambiguous": 4, "contradictory": 3, "revision": 4, "protected_object": 5}


def rectangle_polygon(x: float, y: float, width: float, height: float) -> tuple[tuple[float, float], ...]:
    return ((x, y), (x + width, y), (x + width, y + height), (x, y + height))


def candidate_valid(candidate: Booth, boundary: tuple[tuple[float, float], ...], protected: tuple[PolygonObject, ...], booths: list[Booth]) -> bool:
    return rectangle_within_polygon(candidate, boundary) and not any(rectangles_overlap(candidate, booth) for booth in booths) and not any(rectangle_intersects_polygon(candidate, area.polygon) for area in protected)


def place_source_booths(rng: random.Random, boundary: tuple[tuple[float, float], ...], protected: tuple[PolygonObject, ...], target: int, category: str) -> tuple[Booth, ...]:
    max_x = int(max(point[0] for point in boundary))
    max_y = int(max(point[1] for point in boundary))
    sizes = [(6.0, 6.0), (6.0, 3.0), (3.0, 3.0)]
    booths: list[Booth] = []
    attempts = 0
    while len(booths) < target and attempts < 20_000:
        attempts += 1
        width, height = sizes[(attempts + len(booths)) % len(sizes)]
        x = float(rng.randrange(1, max(2, max_x - int(width))))
        y = float(rng.randrange(1, max(2, max_y - int(height))))
        candidate = Booth(id="candidate", number="candidate", x=x, y=y, width=width, height=height)
        if not candidate_valid(candidate, boundary, protected, booths):
            continue
        index = len(booths)
        if index == 0:
            status = "sold"
        elif index == 1:
            status = "locked"
        elif index % 7 == 0:
            status = "reserved"
        else:
            status = "available"
        prefix = chr(ord("A") + index // 90)
        number = f"{prefix}{101 + index:03d}"
        booth_type = "standard" if (width, height) in {(3.0, 3.0), (6.0, 3.0)} else "custom"
        booths.append(
            Booth(
                id=f"booth-{index + 1:03d}",
                number=number,
                x=x,
                y=y,
                width=width,
                height=height,
                status=status,
                type=booth_type,
                zone="north" if y < max_y / 2 else "south",
                source_version="v1",
            )
        )
    if len(booths) < target:
        raise RuntimeError(f"Could place only {len(booths)} of {target} booths for {category}")
    return tuple(booths)


def make_hall(index: int, category: str, rng: random.Random, split: str) -> HallLayout:
    if category == "irregular":
        width, height = 58.0 + (index % 3) * 4, 40.0 + (index % 2) * 4
        boundary = ((0.0, 0.0), (width, 0.0), (width, height * 0.58), (width * 0.72, height * 0.58), (width * 0.72, height), (0.0, height))
        fixed_aisles = (PolygonObject("aisle-main", rectangle_polygon(width * 0.34, 0, 4, height), "fixed_aisle"),)
    else:
        if category == "simple_rectangular":
            width, height = 64.0 + (index % 3) * 4, 42.0 + (index % 2) * 4
        elif category == "obstacle_containing":
            width, height = 62.0 + (index % 3) * 3, 40.0 + (index % 2) * 4
        elif category == "tight_capacity":
            width, height = 46.0 + (index % 2) * 2, 34.0 + (index % 3) * 2
        else:
            width, height = 40.0 + (index % 2) * 2, 30.0 + (index % 3) * 2
        boundary = rectangle_polygon(0, 0, width, height)
        fixed_aisles = (PolygonObject("aisle-main", rectangle_polygon(0, height * 0.46, width, 4), "fixed_aisle"),)

    obstacles: list[PolygonObject] = []
    if category in {"obstacle_containing", "tight_capacity", "stress_capacity"}:
        obstacle_count = 3 if category == "stress_capacity" else 2
        for obstacle_index in range(obstacle_count):
            ox = width * (0.24 + obstacle_index * 0.22)
            oy = height * (0.20 if obstacle_index % 2 == 0 else 0.70)
            obstacles.append(PolygonObject(f"column-{obstacle_index + 1}", rectangle_polygon(ox, oy, 2, 2), "column"))

    exit_width = 4.0
    exit_x = 0.0 if category == "irregular" else width - exit_width
    exit_clearance = PolygonObject("exit-clearance-east", rectangle_polygon(exit_x, height - 5, exit_width, 5), "exit_clearance")
    protected = tuple(obstacles) + fixed_aisles + (exit_clearance,)
    target_count = {"simple_rectangular": 12, "obstacle_containing": 14, "irregular": 14, "tight_capacity": 22, "stress_capacity": 24}[category]
    booths = place_source_booths(rng, boundary, protected, target_count, category)
    layout = HallLayout(
        hall_id=f"hall-{index + 1:03d}",
        version="v1",
        boundary=boundary,
        booths=booths,
        obstacles=tuple(obstacles),
        exits=(exit_clearance,),
        fixed_aisles=fixed_aisles,
    )
    report = GeometryValidator().validate(layout, layout)
    if not report.valid:
        failures = [check.rule for check in report.checks if not check.passed]
        raise RuntimeError(f"Generated invalid hall {layout.hall_id}: {failures}")
    return layout


def operation_dict(operation: Operation) -> dict[str, Any]:
    return operation.to_dict()


def make_ir(request_id: str, operations: list[Operation], unresolved: list[str] | None = None, confirmation: bool = False, assumptions: list[str] | None = None) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "source_layout_version": "v1",
        "language": "zh" if request_id.endswith("-zh") else "en",
        "operations": [operation_dict(operation) for operation in operations],
        "hard_constraints": ["within_boundary", "no_overlap", "avoid_protected_polygons", "unique_identifiers", "preserve_sold_and_locked"],
        "preferences": [],
        "assumptions": assumptions or [],
        "unresolved_references": unresolved or [],
        "requires_confirmation": confirmation,
    }


def text_pair(language: str, zh: str, en: str) -> str:
    return zh if language == "zh" else en


def build_request(index: int, category: str, language: str, hall: HallLayout) -> dict[str, Any]:
    editable = [booth for booth in hall.booths if booth.status in {"available", "reserved"}]
    protected = [booth for booth in hall.booths if booth.status in {"sold", "locked"}]
    first, second = editable[index % len(editable)], editable[(index + 1) % len(editable)]
    resizable = next((booth for booth in editable if (booth.width, booth.height) != (3.0, 3.0)), first)
    guarded = protected[index % len(protected)]
    request_id = f"eval-{index + 1:03d}-{language}"
    assumptions: list[str] = []

    if category == "capacity_stress":
        text = text_pair(language, "新增 100 个 6×6 米展位，并保持现有展位、通道和出口净空不变。", "Add 100 booths of 6 x 6 m while preserving the existing booths, aisles, and exit clearance.")
        operations = [Operation(OperationType.ADD_BOOTH, count=100, width=6, height=6, booth_type="custom")]
        ir = make_ir(request_id, operations)
        expected = "infeasible"
    elif category == "ambiguous":
        unknown = f"Z{900 + index % 90}"
        text = text_pair(language, f"把 {unknown} 移到北侧。", f"Move {unknown} to the north side.")
        operations = [Operation(OperationType.MOVE_BOOTH, region="north")]
        ir = make_ir(request_id, operations, [unknown], True)
        expected = "needs_confirmation"
    elif category == "contradictory":
        text = text_pair(language, f"把 {first.number} 同时拆成 4 个和 8 个标准展位。", f"Split {first.number} into both 4 and 8 standard booths.")
        ir = make_ir(request_id, [], ["contradictory_booth_count"], True)
        expected = "needs_confirmation"
    elif category == "protected_object":
        text = text_pair(language, f"把已售或锁定展位 {guarded.number} 移到西侧。", f"Move sold or locked booth {guarded.number} to the west side.")
        operations = [Operation(OperationType.MOVE_BOOTH, target_ids=(guarded.id,), region="west")]
        ir = make_ir(request_id, operations, [f"protected:{guarded.number}"], True)
        expected = "needs_confirmation"
    elif category == "revision":
        text = text_pair(language, f"修改当前版本：将 {resizable.number} 调整为 3×3 米，并保留所有已售展位。", f"Revise the current version: resize {resizable.number} to 3 x 3 m and preserve every sold booth.")
        operations = [Operation(OperationType.RESIZE_BOOTH, target_ids=(resizable.id,), width=3, height=3)]
        ir = make_ir(request_id, operations)
        expected = "solver_dependent"
    elif category == "compound":
        text = text_pair(language, f"删除 {first.number}，并在东侧新增 2 个 3×3 米标准展位；保留已售展位。", f"Remove {first.number} and add two 3 x 3 m standard booths on the east side; preserve sold booths.")
        operations = [
            Operation(OperationType.REMOVE_BOOTH, target_ids=(first.id,)),
            Operation(OperationType.ADD_BOOTH, count=2, width=3, height=3, region="east", booth_type="standard"),
        ]
        ir = make_ir(request_id, operations)
        expected = "solver_dependent"
    else:
        variant = index % 6
        if variant == 0:
            text = text_pair(language, "在南侧新增 2 个 3×3 米标准展位。", "Add two 3 x 3 m standard booths on the south side.")
            operations = [Operation(OperationType.ADD_BOOTH, count=2, width=3, height=3, region="south", booth_type="standard")]
        elif variant == 1:
            text = text_pair(language, f"把 {first.number} 移到东侧。", f"Move {first.number} to the east side.")
            operations = [Operation(OperationType.MOVE_BOOTH, target_ids=(first.id,), region="east")]
        elif variant == 2:
            text = text_pair(language, f"把 {resizable.number} 调整为 3×3 米。", f"Resize {resizable.number} to 3 x 3 m.")
            operations = [Operation(OperationType.RESIZE_BOOTH, target_ids=(resizable.id,), width=3, height=3)]
        elif variant == 3:
            text = text_pair(language, f"删除 {first.number}。", f"Remove {first.number}.")
            operations = [Operation(OperationType.REMOVE_BOOTH, target_ids=(first.id,))]
        elif variant == 4:
            splittable = next((booth for booth in editable if booth.width >= 6 and booth.height >= 6), first)
            text = text_pair(language, f"将 {splittable.number} 拆分为 4 个 3×3 米标准展位。", f"Split {splittable.number} into four 3 x 3 m standard booths.")
            operations = [Operation(OperationType.SPLIT_BOOTH, target_ids=(splittable.id,), count=4, width=3, height=3, booth_type="standard")]
        else:
            max_x = max(point[0] for point in hall.boundary)
            max_y = max(point[1] for point in hall.boundary)
            x, y = float(round(max_x - 7)), float(round(max_y * 0.30))
            text = text_pair(language, f"在 x={x:.0f}, y={y:.0f} 处预留一条 3×6 米通道。", f"Reserve a 3 x 6 m aisle at x={x:.0f}, y={y:.0f}.")
            operations = [Operation(OperationType.RESERVE_AISLE, x=x, y=y, width=3, height=6)]
        ir = make_ir(request_id, operations, assumptions=assumptions)
        expected = "solver_dependent"

    parsed_ir = LayoutEditIR.from_dict(ir)
    if expected == "solver_dependent":
        try:
            candidate = DeterministicLayoutSolver().solve(hall, parsed_ir)
            report = GeometryValidator().validate(hall, candidate, parsed_ir)
            expected = "awaiting_approval" if report.valid else "blocked"
        except SolveError:
            expected = "infeasible"

    return {
        "request_id": request_id,
        "hall_id": hall.hall_id,
        "source_version": "v1",
        "split": "development" if int(hall.hall_id.split("-")[-1]) <= 8 else "test",
        "hall_geometry_category": hall.to_dict()["hall_id"],
        "language": language,
        "category": category,
        "text": text,
        "gold_ir": ir,
        "expected_pipeline_state": expected,
        "gold_origin": "template_derived",
        "manual_review_status": "pending",
        "review_notes": None,
    }


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
    rng = random.Random(SEED)
    OUTPUT.mkdir(parents=True, exist_ok=True)
    categories = [category for category, count in HALL_COUNTS.items() for _ in range(count)]
    halls: list[HallLayout] = []
    hall_rows: list[dict[str, Any]] = []
    hall_category_by_id: dict[str, str] = {}
    for index, category in enumerate(categories):
        split = "development" if index < 8 else "test"
        hall = make_hall(index, category, rng, split)
        halls.append(hall)
        hall_category_by_id[hall.hall_id] = category
        row = hall.to_dict()
        row["geometry_category"] = category
        row["split"] = split
        row["generation_seed"] = SEED
        hall_rows.append(row)

    development_schedule: list[tuple[str, str]] = []
    test_schedule: list[tuple[str, str]] = []
    for category, total_count in REQUEST_COUNTS.items():
        development_count = DEVELOPMENT_REQUEST_COUNTS[category]
        development_zh = development_count // 2
        development_en = development_count - development_zh
        test_zh = total_count // 2 - development_zh
        test_en = total_count // 2 - development_en
        development_schedule.extend([(category, "zh")] * development_zh + [(category, "en")] * development_en)
        test_schedule.extend([(category, "zh")] * test_zh + [(category, "en")] * test_en)
    rng.shuffle(development_schedule)
    rng.shuffle(test_schedule)
    development_positions = [index for index in range(sum(REQUEST_COUNTS.values())) if index % len(halls) < 8]
    test_positions = [index for index in range(sum(REQUEST_COUNTS.values())) if index % len(halls) >= 8]
    request_schedule: list[tuple[str, str] | None] = [None] * sum(REQUEST_COUNTS.values())
    for position, pair in zip(development_positions, development_schedule):
        request_schedule[position] = pair
    for position, pair in zip(test_positions, test_schedule):
        request_schedule[position] = pair
    assert all(pair is not None for pair in request_schedule)
    requests: list[dict[str, Any]] = []
    for index, pair in enumerate(request_schedule):
        assert pair is not None
        category, language = pair
        hall = halls[index % len(halls)]
        row = build_request(index, category, language, hall)
        row["hall_geometry_category"] = hall_category_by_id[hall.hall_id]
        requests.append(row)

    halls_path = OUTPUT / "halls.jsonl"
    requests_path = OUTPUT / "requests.jsonl"
    write_jsonl(halls_path, hall_rows)
    write_jsonl(requests_path, requests)

    manifest = {
        "dataset": DATASET_NAME,
        "created_date": "2026-07-16",
        "revision_of": "MICEPlan-Eval-v1",
        "revision_reason": "Development-pilot audit found rounded coordinates in text paired with unrounded coordinates in gold IR.",
        "seed": SEED,
        "coordinate_unit": "m",
        "hall_count": len(hall_rows),
        "request_count": len(requests),
        "hall_categories": dict(Counter(row["geometry_category"] for row in hall_rows)),
        "request_categories": dict(Counter(row["category"] for row in requests)),
        "languages": dict(Counter(row["language"] for row in requests)),
        "splits": {
            "halls": dict(Counter(row["split"] for row in hall_rows)),
            "requests": dict(Counter(row["split"] for row in requests)),
        },
        "expected_pipeline_states": dict(Counter(row["expected_pipeline_state"] for row in requests)),
        "annotation_policy": "Gold IR is template-derived and schema-validated. Manual author review remains pending and must not be described as expert annotation.",
        "files": {
            "halls.jsonl": {"sha256": sha256(halls_path)},
            "requests.jsonl": {"sha256": sha256(requests_path)},
        },
    }
    (OUTPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
