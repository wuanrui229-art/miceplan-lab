from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from shapely.geometry import Polygon, box

from system.miceplan.geometry import GeometryValidator
from system.miceplan.models import HallLayout

from .build_track_r_scenes import SPECS, rect_points
from .oracle import ORACLE_VERSION, validate_candidate


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "miceplan_lab_real_holdout_v0"
SCHEMA = ROOT / "data" / "miceplan_lab_v1_1" / "schemas" / "scene.schema.json"
GENERATOR_VERSION = "miceplan-lab-track-r-source-faithful-builder-v2.0"
SEED = 240723


CONFIG: dict[int, dict[str, Any]] = {
    1: {"target": 72, "booth": (5.0, 4.0), "pattern": "cross"},
    2: {"target": 40, "booth": (4.0, 3.0), "pattern": "double_horizontal"},
    3: {"target": 60, "booth": (5.0, 4.0), "pattern": "cross"},
    4: {"target": 30, "booth": (4.0, 3.0), "pattern": "arena_cross"},
    5: {"target": 36, "booth": (4.0, 3.0), "pattern": "spine"},
    6: {"target": 20, "booth": (4.0, 3.0), "pattern": "single_vertical"},
    7: {"target": 72, "booth": (6.0, 4.0), "pattern": "double_spine"},
    8: {"target": 28, "booth": (4.0, 3.0), "pattern": "cross"},
    9: {"target": 48, "booth": (5.0, 4.0), "pattern": "ladder"},
    10: {"target": 32, "booth": (2.7, 2.7), "pattern": "trade_show"},
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def polygon_object(object_id: str, object_type: str, x: float, y: float, width: float, height: float) -> dict[str, Any]:
    return {"id": object_id, "type": object_type, "polygon": rect_points(x, y, width, height)}


def source_structures(index: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    obstacles: list[dict[str, Any]] = []
    exits: list[dict[str, Any]] = []
    notes: dict[str, Any] = {"source_structure_basis": [], "synthetic_structure_basis": []}

    if index == 1:
        for column_index, x in enumerate((18.0, 43.0, 70.0, 95.0), start=1):
            for row_index, y in enumerate((18.0, 43.0, 70.0, 95.0), start=1):
                obstacles.append(
                    polygon_object(
                        f"track-r-v2-01-source-column-{column_index}-{row_index}",
                        "source_derived_column_clearance",
                        x - 1.5,
                        y - 1.5,
                        3.0,
                        3.0,
                    )
                )
        exits = [
            polygon_object("track-r-v2-01-source-exit-west", "source_derived_exit_clearance", 0.0, 50.0, 4.6, 4.6),
            polygon_object("track-r-v2-01-source-exit-east", "source_derived_exit_clearance", 108.2, 50.0, 4.6, 4.6),
            polygon_object("track-r-v2-01-source-exit-south", "source_derived_exit_clearance", 54.1, 0.0, 4.6, 4.6),
        ]
        notes["source_structure_basis"] = [
            "Official Hall A plan page 9 shows an interior column grid and perimeter emergency exits.",
            "Column clearances use the plan's five-foot-per-side note, conservatively represented as 3.0 m squares.",
            "Normalized positions are plan-traced approximations, not surveyed coordinates.",
        ]
    elif index == 2:
        exits = [
            polygon_object("track-r-v2-02-source-access-south", "source_derived_access_clearance", 15.5, 0.0, 6.0, 4.0),
            polygon_object("track-r-v2-02-source-access-east", "source_derived_access_clearance", 33.2, 31.0, 4.0, 6.0),
        ]
        notes["source_structure_basis"] = [
            "Access sides are reconstructed from the official level-4 plan.",
            "No unsupported interior obstacle is added.",
        ]
    elif index == 3:
        for column_index, (x, y) in enumerate(((18.4, 23.0), (71.4, 23.0), (18.4, 76.0), (71.4, 76.0)), start=1):
            obstacles.append(
                polygon_object(
                    f"track-r-v2-03-source-column-{column_index}",
                    "source_derived_column",
                    x,
                    y,
                    1.6,
                    1.6,
                )
            )
        exits = [
            polygon_object("track-r-v2-03-source-exit-west", "source_derived_exit_clearance", 0.0, 47.8, 4.0, 5.0),
            polygon_object("track-r-v2-03-source-exit-east", "source_derived_exit_clearance", 87.4, 47.8, 4.0, 5.0),
            polygon_object("track-r-v2-03-source-exit-south", "source_derived_exit_clearance", 43.7, 0.0, 4.0, 5.0),
        ]
        notes["source_structure_basis"] = [
            "The official Hall B plan confirms four columns in a two-by-two arrangement and perimeter emergency exits.",
            "The 174 ft centre spacing from the official hall specification controls the reconstructed column spacing.",
        ]
    elif index == 4:
        exits = [
            polygon_object("track-r-v2-04-synthetic-egress-west", "synthetic_egress_clearance", 1.2, 19.0, 3.5, 5.0),
            polygon_object("track-r-v2-04-synthetic-egress-east", "synthetic_egress_clearance", 47.8, 19.0, 3.5, 5.0),
        ]
        notes["source_structure_basis"] = ["The eight-vertex arena shell is source-derived."]
        notes["synthetic_structure_basis"] = [
            "Exact egress-clearance coordinates could not be metrically recovered from the source and are explicitly synthetic."
        ]
    elif index == 5:
        exits = [
            polygon_object("track-r-v2-05-source-entrance-south", "source_derived_entrance_clearance", 15.3, 0.0, 6.0, 4.0),
            polygon_object("track-r-v2-05-source-door-east-1", "source_derived_door_clearance", 32.6, 17.0, 4.0, 5.0),
            polygon_object("track-r-v2-05-source-door-east-2", "source_derived_door_clearance", 32.6, 52.0, 4.0, 5.0),
        ]
        notes["source_structure_basis"] = [
            "The official Hall A map shows the main entrance on the short south side and repeated doors along the east side.",
            "No interior column is shown or invented.",
        ]
    elif index == 6:
        exits = [
            polygon_object("track-r-v2-06-source-foyer-access", "source_derived_access_clearance", 0.0, 9.5, 4.0, 5.0),
            polygon_object("track-r-v2-06-source-hall-m-access", "source_derived_access_clearance", 19.4, 0.0, 4.0, 4.0),
        ]
        notes["source_structure_basis"] = [
            "The official venue map shows Hall L adjoining the foyer to the west and Hall M to the south.",
            "The venue describes the room as pillarless, so no columns are added.",
        ]
    elif index == 7:
        exits = [
            polygon_object("track-r-v2-07-synthetic-egress-west", "synthetic_egress_clearance", 0.0, 31.0, 4.0, 8.0),
            polygon_object("track-r-v2-07-synthetic-egress-east", "synthetic_egress_clearance", 123.0, 31.0, 4.0, 8.0),
        ]
        notes["source_structure_basis"] = [
            "The official fact sheet supplies the hall shell, utility-trench capability, and loading access but not locatable interior geometry."
        ]
        notes["synthetic_structure_basis"] = [
            "Egress clearances are experimental placeholders and are not claimed to reproduce venue doors.",
            "No source-unverifiable column is added.",
        ]
    elif index == 8:
        exits = [
            polygon_object("track-r-v2-08-source-loading-north-1", "source_derived_loading_clearance", 5.0, 34.4, 5.0, 4.0),
            polygon_object("track-r-v2-08-source-loading-north-2", "source_derived_loading_clearance", 26.0, 34.4, 5.0, 4.0),
            polygon_object("track-r-v2-08-source-public-south", "source_derived_entrance_clearance", 15.2, 0.0, 6.0, 4.0),
        ]
        notes["source_structure_basis"] = [
            "The official plan shows loading-dock doors on the north side and public/lobby access on the south side.",
            "No interior column is shown or invented.",
        ]
    elif index == 9:
        exits = [
            polygon_object("track-r-v2-09-source-shipping-west-1", "source_derived_loading_clearance", 0.0, 13.0, 4.0, 6.0),
            polygon_object("track-r-v2-09-source-shipping-west-2", "source_derived_loading_clearance", 0.0, 45.0, 4.0, 6.0),
            polygon_object("track-r-v2-09-source-prefunction-east", "source_derived_access_clearance", 64.6, 29.5, 4.0, 6.0),
        ]
        notes["source_structure_basis"] = [
            "The official plan shows shipping/receiving access on the west and prefunction/meeting circulation on the east.",
            "No interior column is shown or invented.",
        ]
    elif index == 10:
        exits = [
            polygon_object("track-r-v2-10-source-access-west", "source_derived_access_clearance", 0.0, 14.5, 4.0, 5.0),
            polygon_object("track-r-v2-10-source-access-east", "source_derived_access_clearance", 32.0, 14.5, 4.0, 5.0),
        ]
        notes["source_structure_basis"] = [
            "The official trade-show plan supplies access relationships and labelled 8 ft, 10 ft, and 12 ft aisle precedents.",
            "The synthetic booth state is comparable in pattern only; it does not copy the venue's 71-space plan.",
        ]
    else:
        raise ValueError(index)

    return obstacles, exits, notes


def fixed_aisles(index: int) -> list[dict[str, Any]]:
    prefix = f"track-r-v2-{index:02d}"
    if index == 1:
        rectangles = [(54.0, 4.6, 4.0, 100.5), (4.6, 52.0, 103.6, 4.0)]
    elif index == 2:
        rectangles = [(4.0, 21.0, 29.2, 3.2), (4.0, 44.0, 29.2, 3.2)]
    elif index == 3:
        rectangles = [(43.7, 5.0, 4.0, 90.6), (4.0, 48.8, 83.4, 4.0)]
    elif index == 4:
        rectangles = [(24.0, 4.0, 4.0, 36.0), (4.7, 20.0, 43.1, 4.0)]
    elif index == 5:
        rectangles = [(16.3, 4.0, 4.0, 66.7), (4.0, 35.5, 28.6, 3.5)]
    elif index == 6:
        rectangles = [(19.4, 4.0, 4.0, 20.2)]
    elif index == 7:
        rectangles = [(39.5, 4.0, 4.0, 62.0), (83.5, 4.0, 4.0, 62.0), (4.0, 33.0, 119.0, 4.0)]
    elif index == 8:
        rectangles = [(16.2, 4.0, 4.0, 30.4), (4.0, 17.2, 28.3, 4.0)]
    elif index == 9:
        rectangles = [(32.3, 4.0, 4.0, 56.9), (4.0, 20.0, 60.6, 4.0), (4.0, 40.0, 60.6, 4.0)]
    elif index == 10:
        rectangles = [(16.1, 4.0, 3.7, 26.1), (4.0, 10.0, 28.0, 2.4), (4.0, 22.0, 28.0, 3.0)]
    else:
        raise ValueError(index)
    return [
        polygon_object(f"{prefix}-synthetic-aisle-{position}", "synthetic_fixed_aisle", *rectangle)
        for position, rectangle in enumerate(rectangles, start=1)
    ]


def _round_robin(groups: list[list[tuple[float, float]]]) -> list[tuple[float, float]]:
    ordered: list[tuple[float, float]] = []
    position = 0
    while any(position < len(group) for group in groups):
        for group in groups:
            if position < len(group):
                ordered.append(group[position])
        position += 1
    return ordered


def place_booths(
    boundary: Polygon,
    protected_items: list[dict[str, Any]],
    index: int,
    target: int,
    booth_width: float,
    booth_height: float,
) -> list[dict[str, Any]]:
    min_x, min_y, max_x, max_y = boundary.bounds
    protected = [Polygon(item["polygon"]) for item in protected_items]
    gap_x = 1.2 if booth_width >= 5.0 else 1.0
    gap_y = 1.2 if booth_height >= 4.0 else 1.0
    margin = 2.0
    candidates: list[tuple[float, float]] = []
    y = min_y + margin
    row = 0
    while y + booth_height <= max_y - margin + 1e-9:
        xs: list[float] = []
        x = min_x + margin
        while x + booth_width <= max_x - margin + 1e-9:
            xs.append(round(x, 1))
            x += booth_width + gap_x
        if row % 2:
            xs.reverse()
        for current_x in xs:
            shape = box(current_x, round(y, 1), current_x + booth_width, round(y, 1) + booth_height)
            if boundary.covers(shape) and not any(shape.intersection(area).area > 1e-8 for area in protected):
                candidates.append((current_x, round(y, 1)))
        row += 1
        y += booth_height + gap_y

    centre_x = (min_x + max_x) / 2
    centre_y = (min_y + max_y) / 2
    groups: list[list[tuple[float, float]]] = [[], [], [], []]
    for x, y in candidates:
        right = x + booth_width / 2 >= centre_x
        top = y + booth_height / 2 >= centre_y
        group_index = (2 if top else 0) + (1 if right else 0)
        groups[group_index].append((x, y))
    for group_index, group in enumerate(groups):
        groups[group_index] = sorted(
            group,
            key=lambda point: (
                abs((point[1] + booth_height / 2) - centre_y),
                abs((point[0] + booth_width / 2) - centre_x),
                point[1],
                point[0],
            ),
            reverse=(index + group_index) % 2 == 0,
        )

    ordered = _round_robin(groups)
    if len(ordered) < target:
        raise RuntimeError(f"Track R {index:02d} supports only {len(ordered)} booths; requested {target}.")

    selected = ordered[:target]
    booths: list[dict[str, Any]] = []
    for position, (x, y) in enumerate(selected, start=1):
        if position == 1:
            status = "sold"
        elif position == 2:
            status = "locked"
        elif position % 11 == 0:
            status = "reserved"
        else:
            status = "available"
        booths.append(
            {
                "id": f"track-r-v2-{index:02d}-synthetic-booth-{position:03d}",
                "number": f"V{index:02d}-{position:03d}",
                "x": x,
                "y": y,
                "width": booth_width,
                "height": booth_height,
                "status": status,
                "type": "experimental_standard",
            }
        )
    return booths


def runtime_layout(scene: dict[str, Any]) -> HallLayout:
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


def main() -> None:
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    schema_validator = Draft202012Validator(schema)
    geometry_validator = GeometryValidator()
    scenes: list[dict[str, Any]] = []
    provenance_rows: list[dict[str, Any]] = []
    file_records: list[dict[str, Any]] = []

    for source_spec in SPECS:
        spec = copy.deepcopy(source_spec)
        index = int(spec["index"])
        config = CONFIG[index]
        prefix = f"track-r-v2-{index:02d}"
        boundary = Polygon(spec["boundary"])
        if not boundary.is_valid or boundary.area <= 0:
            raise RuntimeError(f"Invalid source boundary for {prefix}")

        obstacles, exits, structure_notes = source_structures(index)
        aisles = fixed_aisles(index)
        for item in obstacles + exits + aisles:
            if not boundary.covers(Polygon(item["polygon"])):
                raise RuntimeError(f"{item['id']} is outside the source-derived boundary")

        booth_width, booth_height = config["booth"]
        booths = place_booths(
            boundary,
            obstacles + exits + aisles,
            index,
            config["target"],
            booth_width,
            booth_height,
        )
        scene = {
            "scene_id": f"{prefix}-{spec['slug']}",
            "split": "test",
            "version": "v1",
            "unit": "m",
            "boundary": spec["boundary"],
            "booths": booths,
            "obstacles": obstacles,
            "fixed_aisles": aisles,
            "exits": exits,
            "complexity_features": {
                "boundary_vertices": len(spec["boundary"]),
                "booth_count": len(booths),
                "protected_polygon_count": len(obstacles) + len(aisles) + len(exits),
            },
        }

        schema_errors = sorted(schema_validator.iter_errors(scene), key=lambda item: list(item.path))
        if schema_errors:
            raise RuntimeError(f"Schema failure {prefix}: {schema_errors[0].message}")
        independent_result = validate_candidate(scene, copy.deepcopy(scene))
        if independent_result.status != "PASS":
            raise RuntimeError(f"Independent oracle failure {prefix}: {independent_result.rule_ids}")
        layout = runtime_layout(scene)
        runtime_result = geometry_validator.validate(layout, layout)
        if not runtime_result.valid:
            raise RuntimeError(
                f"Runtime validator failure {prefix}: {[check.rule_id for check in runtime_result.checks if not check.passed]}"
            )

        min_x, min_y, max_x, max_y = boundary.bounds
        reconstructed_width = max_x - min_x
        reconstructed_height = max_y - min_y
        reconstructed_area = boundary.area
        published_area = float(spec["published_area_m2"])
        relative_area_difference = abs(reconstructed_area - published_area) / published_area
        if relative_area_difference > 0.05:
            raise RuntimeError(f"Area tolerance failure {prefix}: {relative_area_difference}")

        scene_path = OUTPUT / f"formal_scene_v2_{index:02d}_{spec['slug'].replace('-', '_')}.json"
        write_json(scene_path, scene)
        scene_hash = sha256(scene_path)
        source_object_count = sum(
            item["type"].startswith("source_derived") for item in obstacles + exits
        )
        synthetic_structure_count = sum(
            item["type"].startswith("synthetic") for item in obstacles + exits
        )
        provenance = {
            "track_r_index": index,
            "formal_track_r_member": True,
            "track_r_scene_version": "v2",
            "source_venue": spec["venue"],
            "source_room": spec["room"],
            "operation_family": spec["operation_family"],
            "source_page_url": spec["source_page_url"],
            "source_plan_urls": spec["source_plan_urls"],
            "access_date": "2026-07-23",
            "source_artifact_sha256": spec["source_sha256"],
            "scene_file": scene_path.name,
            "scene_sha256": scene_hash,
            "coordinate_unit": "m",
            "protocol_snap_m": 0.1,
            "published_width_m": spec["published_width_m"],
            "published_height_m": spec["published_height_m"],
            "published_area_m2": published_area,
            "reconstructed_width_m": reconstructed_width,
            "reconstructed_height_m": reconstructed_height,
            "reconstructed_area_m2": reconstructed_area,
            "relative_area_difference": relative_area_difference,
            "boundary_geometry_method": spec["geometry_method"],
            "boundary_source_derived_fields": spec["source_derived_fields"],
            "source_structure_basis": structure_notes["source_structure_basis"],
            "synthetic_structure_basis": structure_notes["synthetic_structure_basis"],
            "source_derived_fixed_object_count": source_object_count,
            "synthetic_non_aisle_fixed_object_count": synthetic_structure_count,
            "synthetic_fields": [
                "experimental booth rectangles",
                "booth identifiers and states",
                "controlled fixed-aisle pattern",
            ],
            "arrangement_family": config["pattern"],
            "target_booth_count": config["target"],
            "booth_footprint_m": [booth_width, booth_height],
            "extraction_record": spec.get("extraction_record"),
            "generator_version": GENERATOR_VERSION,
            "generator_seed": SEED,
            "source_artifact_redistributed": False,
            "schema_validation": "PASS",
            "runtime_validator_start_state": "PASS",
            "independent_oracle_start_state": "PASS",
            "independent_oracle_version": ORACLE_VERSION,
            "qa_note": (
                "Source-derived fixed objects are separately typed from controlled synthetic objects. "
                "The booth state is an experimental layout, not a venue-authentic floor plan or code-approved plan."
            ),
        }
        provenance_path = OUTPUT / f"formal_provenance_v2_{index:02d}_{spec['slug'].replace('-', '_')}.json"
        write_json(provenance_path, provenance)
        scenes.append(scene)
        provenance_rows.append(provenance)
        file_records.append(
            {
                "track_r_index": index,
                "scene_file": scene_path.name,
                "scene_sha256": scene_hash,
                "provenance_file": provenance_path.name,
                "provenance_sha256": sha256(provenance_path),
            }
        )

    scenes_path = OUTPUT / "formal_scenes_v2.jsonl"
    provenance_path = OUTPUT / "formal_provenance_v2.jsonl"
    write_jsonl(scenes_path, scenes)
    write_jsonl(provenance_path, provenance_rows)
    manifest = {
        "version": "track-r-formal-scenes-v2",
        "created_at": "2026-07-23",
        "amendment": "../../MICEPLAN_LAB_TRACK_R_V2_PRETASK_AMENDMENT_2026-07-23.md",
        "supersedes_rejected_version": "formal_scene_manifest_v1.json",
        "generator_version": GENERATOR_VERSION,
        "generator_seed": SEED,
        "source_selection_manifest": "formal_selection_manifest_v1.json",
        "source_artifact_manifest": "source_artifact_manifest_v1.json",
        "scene_count": len(scenes),
        "all_split_test": all(scene["split"] == "test" for scene in scenes),
        "all_schema_pass": True,
        "all_runtime_validator_pass": True,
        "all_independent_oracle_pass": True,
        "source_artifacts_redistributed": False,
        "formal_requests_generated": False,
        "model_calls_made": 0,
        "author_visual_review_status": "PENDING",
        "files": file_records,
        "aggregate_files": {
            "formal_scenes_v2.jsonl": {"sha256": sha256(scenes_path), "bytes": scenes_path.stat().st_size},
            "formal_provenance_v2.jsonl": {"sha256": sha256(provenance_path), "bytes": provenance_path.stat().st_size},
        },
    }
    write_json(OUTPUT / "formal_scene_manifest_v2.json", manifest)
    print(json.dumps({"scene_count": len(scenes), "booth_count": sum(len(scene["booths"]) for scene in scenes)}, indent=2))


if __name__ == "__main__":
    main()
