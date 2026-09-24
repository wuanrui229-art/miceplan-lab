from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator
from shapely.geometry import Polygon, box

from .oracle import ORACLE_VERSION, validate_candidate


ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "data" / "miceplan_lab_real_holdout_v0"
VISUALS = OUTPUT / "formal_visual_review_v1"
SCHEMA = ROOT / "data" / "miceplan_lab_v1_1" / "schemas" / "scene.schema.json"
GENERATOR_VERSION = "miceplan-lab-track-r-shell-builder-v1.0"
SEED = 240723
FT_TO_M = 0.3048
FT2_TO_M2 = 0.09290304


def rectangle(width: float, height: float) -> list[list[float]]:
    return [[0.0, 0.0], [width, 0.0], [width, height], [0.0, height]]


SPECS: list[dict[str, Any]] = [
    {
        "index": 1,
        "slug": "pennsylvania-hall-a",
        "venue": "Pennsylvania Convention Center",
        "room": "Exhibit Hall A",
        "operation_family": "ADD_BOOTH",
        "boundary": rectangle(112.8, 109.7),
        "published_width_m": 370 * FT_TO_M,
        "published_height_m": 360 * FT_TO_M,
        "published_area_m2": 135000 * FT2_TO_M2,
        "source_page_url": "https://www.paconvention.com/the-center/floor-plans",
        "source_plan_urls": ["https://paconvention.production.carbonhouse.com/assets/doc/200-Level-Exhibit-Hall-200-Level-Meeting-Rooms-Grand-Hall-Rev.-07.2023-79803ff8b0.pdf"],
        "source_sha256": ["79803ff8b0078422064fb2d498d29795ce04e6f94592f1a2634633e5bdc710fc"],
        "geometry_method": "Rectangular hall shell from the official 370 ft by 360 ft dimensions, converted to metres and snapped to 0.1 m.",
        "source_derived_fields": ["rectangular boundary topology", "overall width", "overall height", "published area for QA"],
    },
    {
        "index": 2,
        "slug": "quebec-400a",
        "venue": "Quebec City Convention Centre",
        "room": "Room 400A",
        "operation_family": "MOVE_BOOTH",
        "boundary": rectangle(37.2, 68.3),
        "published_width_m": 37.2,
        "published_height_m": 68.3,
        "published_area_m2": 2577.0,
        "source_page_url": "https://www.convention.qc.ca/en/event-planners/room-capacity-chart/",
        "source_plan_urls": ["https://www.convention.qc.ca/wp-content/uploads/Plans-Capacities-ENG-2025-1.pdf"],
        "source_sha256": ["ab9cf5168ada845ea079afbcebd072d3fcf95ac105c0f446e9c714fe26e7cc4a"],
        "geometry_method": "Rectangular room shell from the official 37.2 m by 68.3 m dimensions, retained at the 0.1 m protocol grid.",
        "source_derived_fields": ["rectangular boundary topology", "overall width", "overall height", "published area for QA"],
    },
    {
        "index": 3,
        "slug": "minneapolis-hall-b",
        "venue": "Minneapolis Convention Center",
        "room": "Exhibit Hall B",
        "operation_family": "RESIZE_BOOTH",
        "boundary": rectangle(91.4, 100.6),
        "published_width_m": 300 * FT_TO_M,
        "published_height_m": 330 * FT_TO_M,
        "published_area_m2": 99000 * FT2_TO_M2,
        "source_page_url": "https://www.minneapolis.org/minneapolis-convention-center/event-planners/floor-plans/level-one/hall-b/",
        "source_plan_urls": ["https://www.minneapolis.org/minneapolis-convention-center/event-planners/floor-plans/level-one/hall-b/"],
        "source_sha256": ["dc8265b534b54f8e8f47121944c037356ca9a68cd47ac68bff3538aefe2cc021"],
        "geometry_method": "Rectangular hall shell from the official 300 ft by 330 ft dimensions, converted to metres and snapped to 0.1 m.",
        "source_derived_fields": ["rectangular boundary topology", "overall width", "overall height", "published area for QA"],
    },
    {
        "index": 4,
        "slug": "gccec-arena",
        "venue": "Gold Coast Convention and Exhibition Centre",
        "room": "Arena",
        "operation_family": "REMOVE_BOOTH",
        "boundary": [[8.1, 0.0], [46.5, 0.0], [52.4, 7.2], [52.4, 37.1], [42.8, 44.0], [3.4, 44.0], [0.0, 39.6], [0.8, 7.0]],
        "published_width_m": 52.4,
        "published_height_m": 44.0,
        "published_area_m2": 2182.0,
        "source_page_url": "https://www.gccec.com.au/event-planning-tool/virtual-tour/floor-plans/",
        "source_plan_urls": ["https://www.gccec.com.au/wp-content/uploads/2023/09/GCCEC_FloorPlan_GroundFloor.pdf"],
        "source_sha256": ["085914ab3e2530ae1ebd7d57991305ebd34e3ab8f0aa8f0d4777d72fd2a7e09e"],
        "geometry_method": "Eight-vertex Arena topology traced from the official ground-floor plan, scaled to the published 52.4 m by 44.0 m extent and snapped to 0.1 m.",
        "source_derived_fields": ["eight-vertex outer-boundary topology", "overall width", "overall height", "published area for QA"],
        "extraction_record": {
            "source_page": 1,
            "trace_bbox_px": [585, 413, 922, 694],
            "trace_vertices_px": [[637, 413], [884, 413], [922, 459], [922, 650], [860, 694], [607, 694], [585, 666], [590, 458]],
        },
    },
    {
        "index": 5,
        "slug": "atlantic-hall-a",
        "venue": "Atlantic City Convention Center",
        "room": "Hall A",
        "operation_family": "SPLIT_BOOTH",
        "boundary": rectangle(36.6, 74.7),
        "published_width_m": 120 * FT_TO_M,
        "published_height_m": 245 * FT_TO_M,
        "published_area_m2": 29400 * FT2_TO_M2,
        "source_page_url": "https://www.accenter.com/plan/floor-plans",
        "source_plan_urls": [
            "https://accenter.production.carbonhouse.com/assets/img/ACCC-Hall-A-f4791847a5.jpg",
            "https://www.accenter.com/assets/doc/Level-2-Specs-c87279678c.pdf",
        ],
        "source_sha256": [
            "f4791847a5a9ff7a2096e76129a061baa50c2e1d2fdc23a97fdfdaa6fef324c9",
            "c87279678cbeb1ccdf2c04621c824ed6a5f2d69b433533114d9b8d6157e8d8b8",
        ],
        "geometry_method": "Rectangular Hall A shell from the official 120 ft by 245 ft specifications; the official map was used only to confirm topology.",
        "source_derived_fields": ["rectangular boundary topology", "overall width", "overall height", "published area for QA"],
    },
    {
        "index": 6,
        "slug": "adelaide-hall-l",
        "venue": "Adelaide Convention Centre",
        "room": "Hall L",
        "operation_family": "RESERVE_AISLE",
        "boundary": rectangle(42.8, 24.2),
        "published_width_m": None,
        "published_height_m": None,
        "published_area_m2": 1035.0,
        "source_page_url": "https://www.adelaidecc.com.au/planning/venue-map/",
        "source_plan_urls": ["https://www.adelaidecc.com.au/wp-content/uploads/2023/08/Hall-L.png"],
        "source_sha256": ["dd1244eef62562cdee685b7292196e18cdd98fa4e42c6bca13eef38f8ef16ae6"],
        "geometry_method": "The official map shows Hall L as a rectangle. Its traced image aspect ratio was scaled to the official 1,035 m2 area, then snapped to 42.8 m by 24.2 m.",
        "source_derived_fields": ["rectangular boundary topology", "image aspect ratio", "published area used for metric scaling"],
        "extraction_record": {"image_size_px": [1228, 920], "highlight_bbox_px": [246, 380, 393, 463]},
    },
    {
        "index": 7,
        "slug": "ewb-hall-1",
        "venue": "Exhibition World Bahrain",
        "room": "Hall 1",
        "operation_family": "ADD_BOOTH",
        "boundary": rectangle(127.0, 70.0),
        "published_width_m": 127.0,
        "published_height_m": 70.0,
        "published_area_m2": 8880.0,
        "source_page_url": "https://www.ewbahrain.com/Organise/Factsheets/",
        "source_plan_urls": ["https://www.ewbahrain.com/MediaManager/Media/Documents/VenueSpaces/ExhibitionHallsFactSheet.pdf"],
        "source_sha256": ["aee1886db827f6e5d39323142e037719a067b14316a3696e69e6e72981fd9b93"],
        "geometry_method": "Rectangular Hall 1 shell from the official 127 m by 70 m dimensions, retained at the 0.1 m protocol grid.",
        "source_derived_fields": ["rectangular boundary topology", "overall width", "overall height", "published area for QA"],
    },
    {
        "index": 8,
        "slug": "ruidoso-exhibit-hall",
        "venue": "Ruidoso Convention Center",
        "room": "Exhibit Hall",
        "operation_family": "MOVE_BOOTH",
        "boundary": rectangle(36.3, 38.4),
        "published_width_m": 119 * FT_TO_M,
        "published_height_m": 126 * FT_TO_M,
        "published_area_m2": 14994 * FT2_TO_M2,
        "source_page_url": "https://www.ruidosoconventioncenter.com/floor-plans",
        "source_plan_urls": ["https://www.ruidosoconventioncenter.com/s/RCC_FolderInsert_FloorPlan_2025-1.pdf"],
        "source_sha256": ["b0d174d02f031dd9c2d2d443d64273aac680bf0365ee788730084fadb2548d85"],
        "geometry_method": "Rectangular exhibit-hall shell from the official 119 ft by 126 ft dimensions, converted to metres and snapped to 0.1 m.",
        "source_derived_fields": ["rectangular boundary topology", "overall width", "overall height", "published area for QA"],
    },
    {
        "index": 9,
        "slug": "cohere-hall-2",
        "venue": "Cohere Centre Ottawa",
        "room": "Hall 2",
        "operation_family": "RESIZE_BOOTH",
        "boundary": rectangle(68.6, 64.9),
        "published_width_m": 225 * FT_TO_M,
        "published_height_m": 213 * FT_TO_M,
        "published_area_m2": 47928 * FT2_TO_M2,
        "source_page_url": "https://coherecentre.ca/floorplans/",
        "source_plan_urls": ["https://coherecentre.ca/wp-content/uploads/2026/05/Cohere-Centre-Floor-Plan-1.pdf"],
        "source_sha256": ["b9bfaa6012436999a2da175ec427fe98ec51df1ba9e32b60432955dfec9a72a1"],
        "geometry_method": "Rectangular Hall 2 shell from the official web-table dimensions of 225 ft by 213 ft; the plan's rounded 50,000 ft2 label is not used for metric scaling.",
        "source_derived_fields": ["rectangular boundary topology", "overall width", "overall height", "web-table area for QA"],
    },
    {
        "index": 10,
        "slug": "pendleton-main-hall",
        "venue": "Pendleton Convention Center",
        "room": "Main Hall",
        "operation_family": "REMOVE_BOOTH",
        "boundary": rectangle(36.0, 34.1),
        "published_width_m": 118 * FT_TO_M,
        "published_height_m": 112 * FT_TO_M,
        "published_area_m2": 13216 * FT2_TO_M2,
        "source_page_url": "https://www.meetinpendleton.com/floor-plans",
        "source_plan_urls": [
            "https://www.meetinpendleton.com/_files/ugd/eff652_04a70c32cda743ffa6ec8e23440acf65.pdf",
            "https://www.meetinpendleton.com/_files/ugd/eff652_7f2f05d1fbbf4726a82b2ddbf30cf428.pdf",
        ],
        "source_sha256": [
            "91e5cbd795aef9e7c9cf371ff70c0461bef2a98350fb2bdd0a60a89c69676ca6",
            "2048864e439f2cb68af13bdf4f1013a9a8e37a547ea5b0d04f48f9a2e7be11be",
        ],
        "geometry_method": "Rectangular Main Hall shell from the official 118 ft by 112 ft room-size chart, converted to metres and snapped to 0.1 m.",
        "source_derived_fields": ["rectangular boundary topology", "overall width", "overall height", "published area for QA"],
    },
]


def rect_points(x: float, y: float, width: float, height: float) -> list[list[float]]:
    return [[round(x, 1), round(y, 1)], [round(x + width, 1), round(y, 1)], [round(x + width, 1), round(y + height, 1)], [round(x, 1), round(y + height, 1)]]


def choose_protected(boundary: Polygon, prefix: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    min_x, min_y, max_x, max_y = boundary.bounds
    width, height = max_x - min_x, max_y - min_y
    aisle_height = 3.0 if height < 30 else 4.0
    y = round((min_y + max_y - aisle_height) / 2, 1)

    aisle_shape = None
    aisle_bounds = None
    for margin in [round(value, 1) for value in (3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0)]:
        candidate = box(min_x + margin, y, max_x - margin, y + aisle_height)
        if boundary.covers(candidate):
            aisle_shape = candidate
            aisle_bounds = (min_x + margin, y, max_x - margin, y + aisle_height)
            break
    if aisle_shape is None or aisle_bounds is None:
        raise RuntimeError(f"No protected aisle placement for {prefix}")

    left, bottom, right, top = aisle_bounds
    exit_width = min(3.0, max(1.5, width * 0.05))
    left_exit = box(left, bottom, left + exit_width, top)
    right_exit = box(right - exit_width, bottom, right, top)
    if not boundary.covers(left_exit) or not boundary.covers(right_exit):
        raise RuntimeError(f"No protected exit placement for {prefix}")

    fixed_aisles = [{"id": f"{prefix}-synthetic-main-aisle", "type": "synthetic_fixed_aisle", "polygon": rect_points(left + exit_width, bottom, right - left - 2 * exit_width, top - bottom)}]
    exits = [
        {"id": f"{prefix}-synthetic-exit-west", "type": "synthetic_exit_clearance", "polygon": rect_points(left, bottom, exit_width, top - bottom)},
        {"id": f"{prefix}-synthetic-exit-east", "type": "synthetic_exit_clearance", "polygon": rect_points(right - exit_width, bottom, exit_width, top - bottom)},
    ]

    protected_shapes = [Polygon(item["polygon"]) for item in fixed_aisles + exits]
    obstacles: list[dict[str, Any]] = []
    candidates = [
        (min_x + 0.75 * width, min_y + 0.25 * height),
        (min_x + 0.75 * width, min_y + 0.75 * height),
        (min_x + 0.25 * width, min_y + 0.25 * height),
        (min_x + 0.25 * width, min_y + 0.75 * height),
    ]
    for x, obstacle_y in candidates:
        points = rect_points(round(x, 1), round(obstacle_y, 1), 1.2, 1.2)
        shape = Polygon(points)
        if boundary.covers(shape) and not any(shape.intersection(item).area > 1e-8 for item in protected_shapes):
            obstacles.append({"id": f"{prefix}-synthetic-column-{len(obstacles) + 1}", "type": "synthetic_column", "polygon": points})
        if len(obstacles) == 2:
            break
    if len(obstacles) < 2:
        raise RuntimeError(f"Could not place two synthetic obstacles for {prefix}")
    return obstacles, fixed_aisles, exits


def place_booths(scene: dict[str, Any], prefix: str) -> list[dict[str, Any]]:
    boundary = Polygon(scene["boundary"])
    min_x, min_y, max_x, max_y = boundary.bounds
    protected = [Polygon(item["polygon"]) for item in scene["obstacles"] + scene["fixed_aisles"] + scene["exits"]]
    booths: list[dict[str, Any]] = []
    width, height = max_x - min_x, max_y - min_y
    x_values = [round(min_x + 2.0 + index * (width - 8.0) / 5, 1) for index in range(6)]
    y_values = [round(min_y + 2.0 + index * (height - 7.0) / 3, 1) for index in range(4)]
    primary_positions = [(x, y) for y in y_values for x in x_values]
    fallback_positions = [
        (round(x, 1), round(y, 1))
        for y in [min_y + 2.0 + step * 5.0 for step in range(max(1, math.ceil((height - 5.0) / 5.0)))]
        for x in [min_x + 2.0 + step * 6.0 for step in range(max(1, math.ceil((width - 6.0) / 6.0)))]
    ]
    for x, y in primary_positions + fallback_positions:
        if len(booths) >= 24:
            break
        if x + 4.0 <= max_x - 1.0 and y + 3.0 <= max_y - 1.0:
            shape = box(x, y, x + 4.0, y + 3.0)
            existing = [box(item["x"], item["y"], item["x"] + item["width"], item["y"] + item["height"]) for item in booths]
            if boundary.covers(shape) and not any(shape.intersection(area).area > 1e-8 for area in protected + existing):
                index = len(booths) + 1
                status = "sold" if index == 1 else "locked" if index == 2 else "reserved" if index == 8 else "available"
                booths.append(
                    {
                        "id": f"{prefix}-synthetic-booth-{index:02d}",
                        "number": f"R{index:03d}",
                        "x": round(x, 1),
                        "y": round(y, 1),
                        "width": 4.0,
                        "height": 3.0,
                        "status": status,
                        "type": "standard",
                    }
                )
    if len(booths) < 12:
        raise RuntimeError(f"Only {len(booths)} booths placed for {prefix}")
    return booths


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


def polygon_svg(points: list[list[float]], min_x: float, min_y: float, scale: float, pad: float, max_y: float) -> str:
    values = []
    for x, y in points:
        sx = pad + (x - min_x) * scale
        sy = pad + (max_y - y) * scale
        values.append(f"{sx:.1f},{sy:.1f}")
    return " ".join(values)


def svg_for(scene: dict[str, Any], spec: dict[str, Any]) -> str:
    boundary = Polygon(scene["boundary"])
    min_x, min_y, max_x, max_y = boundary.bounds
    drawing_w, drawing_h, pad = 820.0, 600.0, 50.0
    scale = min((drawing_w - 2 * pad) / (max_x - min_x), (drawing_h - 2 * pad) / (max_y - min_y))
    content = [
        '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="760" viewBox="0 0 1000 760">',
        '<rect width="1000" height="760" fill="#f7f5ef"/>',
        f'<text x="50" y="38" font-family="Arial" font-size="24" font-weight="700" fill="#183b36">Track R {spec["index"]:02d}: {spec["venue"]}</text>',
        f'<text x="50" y="68" font-family="Arial" font-size="18" fill="#415a55">{spec["room"]} - {spec["operation_family"]} - source-derived shell / synthetic state</text>',
        '<g transform="translate(0,80)">',
        f'<polygon points="{polygon_svg(scene["boundary"], min_x, min_y, scale, pad, max_y)}" fill="#ffffff" stroke="#183b36" stroke-width="3"/>',
    ]
    colors = {"obstacles": "#c05a47", "fixed_aisles": "#e4b84d", "exits": "#5f9f88"}
    for group in ("fixed_aisles", "exits", "obstacles"):
        for item in scene[group]:
            content.append(f'<polygon points="{polygon_svg(item["polygon"], min_x, min_y, scale, pad, max_y)}" fill="{colors[group]}" fill-opacity="0.75" stroke="#183b36" stroke-width="1"/>')
    for booth in scene["booths"]:
        points = rect_points(booth["x"], booth["y"], booth["width"], booth["height"])
        fill = "#839b91" if booth["status"] == "available" else "#6d7898" if booth["status"] == "reserved" else "#414b4a"
        content.append(f'<polygon points="{polygon_svg(points, min_x, min_y, scale, pad, max_y)}" fill="{fill}" stroke="#ffffff" stroke-width="0.8"/>')
    content.extend(
        [
            '</g>',
            '<g transform="translate(850,125)" font-family="Arial" font-size="14" fill="#183b36">',
            '<text x="0" y="0" font-size="16" font-weight="700">Legend</text>',
            '<rect x="0" y="18" width="18" height="12" fill="#839b91"/><text x="26" y="29">synthetic booth</text>',
            '<rect x="0" y="46" width="18" height="12" fill="#e4b84d"/><text x="26" y="57">synthetic aisle</text>',
            '<rect x="0" y="74" width="18" height="12" fill="#5f9f88"/><text x="26" y="85">synthetic exit zone</text>',
            '<rect x="0" y="102" width="18" height="12" fill="#c05a47"/><text x="26" y="113">synthetic obstacle</text>',
            f'<text x="0" y="160">Boundary vertices: {len(scene["boundary"])}</text>',
            f'<text x="0" y="184">Booths: {len(scene["booths"])}</text>',
            f'<text x="0" y="208">Area diff: {spec["relative_area_difference"] * 100:.2f}%</text>',
            '</g>',
            '<text x="50" y="730" font-family="Arial" font-size="14" fill="#5d6966">Internal QA view. Original venue plan is not reproduced. Not a professional, regulatory, or event-ready layout.</text>',
            '</svg>',
        ]
    )
    return "\n".join(content) + "\n"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    VISUALS.mkdir(parents=True, exist_ok=True)
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    scenes: list[dict[str, Any]] = []
    provenance_rows: list[dict[str, Any]] = []
    file_records: list[dict[str, Any]] = []

    for spec in SPECS:
        prefix = f"track-r-{spec['index']:02d}"
        boundary = Polygon(spec["boundary"])
        if not boundary.is_valid or boundary.area <= 0:
            raise RuntimeError(f"Invalid boundary for {prefix}")
        obstacles, fixed_aisles, exits = choose_protected(boundary, prefix)
        scene = {
            "scene_id": f"{prefix}-{spec['slug']}",
            "split": "test",
            "version": "v1",
            "unit": "m",
            "boundary": spec["boundary"],
            "booths": [],
            "obstacles": obstacles,
            "fixed_aisles": fixed_aisles,
            "exits": exits,
            "complexity_features": {},
        }
        scene["booths"] = place_booths(scene, prefix)
        scene["complexity_features"] = {
            "boundary_vertices": len(scene["boundary"]),
            "booth_count": len(scene["booths"]),
            "protected_polygon_count": len(obstacles) + len(fixed_aisles) + len(exits),
        }
        errors = sorted(validator.iter_errors(scene), key=lambda item: list(item.path))
        if errors:
            raise RuntimeError(f"Schema failure for {prefix}: {errors[0].message}")
        oracle = validate_candidate(scene, json.loads(json.dumps(scene)))
        if oracle.status != "PASS":
            raise RuntimeError(f"Oracle failure for {prefix}: {oracle.rule_ids}")

        min_x, min_y, max_x, max_y = boundary.bounds
        reconstructed_width = max_x - min_x
        reconstructed_height = max_y - min_y
        reconstructed_area = boundary.area
        published_area = float(spec["published_area_m2"])
        relative_area_difference = abs(reconstructed_area - published_area) / published_area
        if relative_area_difference > 0.05:
            raise RuntimeError(f"Area tolerance failure for {prefix}: {relative_area_difference}")
        if spec["published_width_m"] is not None and abs(reconstructed_width - spec["published_width_m"]) / spec["published_width_m"] > 0.02:
            raise RuntimeError(f"Width tolerance failure for {prefix}")
        if spec["published_height_m"] is not None and abs(reconstructed_height - spec["published_height_m"]) / spec["published_height_m"] > 0.02:
            raise RuntimeError(f"Height tolerance failure for {prefix}")
        spec["relative_area_difference"] = relative_area_difference

        scene_path = OUTPUT / f"formal_scene_{spec['index']:02d}_{spec['slug'].replace('-', '_')}.json"
        write_json(scene_path, scene)
        scene_hash = sha256(scene_path)
        provenance = {
            "track_r_index": spec["index"],
            "formal_track_r_member": True,
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
            "geometry_method": spec["geometry_method"],
            "source_derived_fields": spec["source_derived_fields"],
            "synthetic_fields": ["booths", "booth states", "fixed aisle", "exit clearances", "obstacles", "object identifiers"],
            "extraction_record": spec.get("extraction_record"),
            "generator_version": GENERATOR_VERSION,
            "generator_seed": SEED,
            "source_artifact_redistributed": False,
            "runtime_oracle_start_state": "PASS",
            "independent_oracle_version": ORACLE_VERSION,
            "qa_note": "The shell passes frozen width/height and area tolerances. All non-boundary layout objects are synthetic and are not claimed to be venue-authentic.",
        }
        provenance_path = OUTPUT / f"formal_provenance_{spec['index']:02d}_{spec['slug'].replace('-', '_')}.json"
        write_json(provenance_path, provenance)
        svg_path = VISUALS / f"track_r_{spec['index']:02d}_{spec['slug'].replace('-', '_')}.svg"
        svg_path.write_text(svg_for(scene, spec), encoding="utf-8")
        scenes.append(scene)
        provenance_rows.append(provenance)
        file_records.append(
            {
                "track_r_index": spec["index"],
                "scene_file": scene_path.name,
                "scene_sha256": scene_hash,
                "provenance_file": provenance_path.name,
                "provenance_sha256": sha256(provenance_path),
                "visual_review_file": str(svg_path.relative_to(OUTPUT)),
                "visual_review_sha256": sha256(svg_path),
            }
        )

    scenes_path = OUTPUT / "formal_scenes_v1.jsonl"
    provenance_path = OUTPUT / "formal_provenance_v1.jsonl"
    write_jsonl(scenes_path, scenes)
    write_jsonl(provenance_path, provenance_rows)
    manifest = {
        "version": "track-r-formal-scenes-v1",
        "created_at": "2026-07-23",
        "generator_version": GENERATOR_VERSION,
        "generator_seed": SEED,
        "source_selection_manifest": "formal_selection_manifest_v1.json",
        "source_artifact_manifest": "source_artifact_manifest_v1.json",
        "scene_count": len(scenes),
        "all_split_test": all(scene["split"] == "test" for scene in scenes),
        "all_source_scenes_independent_oracle_pass": True,
        "source_artifacts_redistributed": False,
        "formal_requests_generated": False,
        "model_calls_made": 0,
        "author_visual_review_status": "PENDING",
        "files": file_records,
        "aggregate_files": {
            "formal_scenes_v1.jsonl": {"sha256": sha256(scenes_path), "bytes": scenes_path.stat().st_size},
            "formal_provenance_v1.jsonl": {"sha256": sha256(provenance_path), "bytes": provenance_path.stat().st_size},
        },
    }
    write_json(OUTPUT / "formal_scene_manifest_v1.json", manifest)
    print(json.dumps({"scene_count": len(scenes), "manifest": str(OUTPUT / 'formal_scene_manifest_v1.json')}, indent=2))


if __name__ == "__main__":
    main()
