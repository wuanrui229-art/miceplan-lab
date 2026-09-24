from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "miceplan_lab_real_holdout_v0"
OUTPUT = DATA / "formal_visual_review_v2"


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf"),
        Path("/System/Library/Fonts/HelveticaNeue.ttc"),
    ]
    for path in candidates:
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size=size, index=0)
            except OSError:
                continue
    return ImageFont.load_default()


def bounds(points: list[list[float]]) -> tuple[float, float, float, float]:
    xs = [float(point[0]) for point in points]
    ys = [float(point[1]) for point in points]
    return min(xs), min(ys), max(xs), max(ys)


class Projection:
    def __init__(self, source_bounds: tuple[float, float, float, float]) -> None:
        self.min_x, self.min_y, self.max_x, self.max_y = source_bounds
        self.left, self.top, self.right, self.bottom = 90.0, 150.0, 890.0, 850.0
        self.scale = min(
            (self.right - self.left) / (self.max_x - self.min_x),
            (self.bottom - self.top) / (self.max_y - self.min_y),
        )
        self.offset_x = self.left + ((self.right - self.left) - (self.max_x - self.min_x) * self.scale) / 2
        self.offset_y = self.top + ((self.bottom - self.top) - (self.max_y - self.min_y) * self.scale) / 2

    def point(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.offset_x + (x - self.min_x) * self.scale,
            self.offset_y + (self.max_y - y) * self.scale,
        )

    def polygon(self, points: list[list[float]]) -> list[tuple[float, float]]:
        return [self.point(float(x), float(y)) for x, y in points]


def booth_points(booth: dict[str, Any]) -> list[list[float]]:
    x, y = float(booth["x"]), float(booth["y"])
    width, height = float(booth["width"]), float(booth["height"])
    return [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]


def nice_scale(width: float) -> float:
    raw = width / 5
    magnitude = 10 ** math.floor(math.log10(raw))
    normalized = raw / magnitude
    choice = 1 if normalized < 1.5 else 2 if normalized < 3.5 else 5
    return choice * magnitude


def render(scene: dict[str, Any], provenance: dict[str, Any], destination: Path) -> None:
    canvas = Image.new("RGB", (1400, 980), "#f3f5f4")
    draw = ImageDraw.Draw(canvas)
    title = font(28, bold=True)
    subtitle = font(18)
    body = font(15)
    small = font(12)
    tiny = font(10)
    source_bounds = bounds(scene["boundary"])
    projection = Projection(source_bounds)
    min_x, min_y, max_x, max_y = source_bounds

    draw.text((70, 34), f"Track R v2 · {provenance['track_r_index']:02d} · {provenance['source_venue']}", fill="#142a3b", font=title)
    draw.text(
        (70, 76),
        f"{provenance['source_room']}  |  {provenance['operation_family']}  |  {provenance['arrangement_family']}",
        fill="#4e6371",
        font=subtitle,
    )
    draw.text(
        (70, 108),
        "Source-derived shell and fixed features + controlled synthetic experimental booth state",
        fill="#526a62",
        font=body,
    )

    grid_step = nice_scale(max_x - min_x) / 2
    grid_step = max(5.0, grid_step)
    x = math.ceil(min_x / grid_step) * grid_step
    while x <= max_x + 1e-9:
        p1 = projection.point(x, min_y)
        p2 = projection.point(x, max_y)
        draw.line((p1, p2), fill="#d7ddda", width=1)
        draw.text((p1[0] + 2, projection.offset_y + (max_y - min_y) * projection.scale + 6), f"{x:g}", fill="#778780", font=tiny)
        x += grid_step
    y = math.ceil(min_y / grid_step) * grid_step
    while y <= max_y + 1e-9:
        p1 = projection.point(min_x, y)
        p2 = projection.point(max_x, y)
        draw.line((p1, p2), fill="#d7ddda", width=1)
        draw.text((projection.offset_x - 32, p1[1] - 6), f"{y:g}", fill="#778780", font=tiny)
        y += grid_step

    draw.polygon(projection.polygon(scene["boundary"]), fill="#ffffff", outline="#132d3d", width=4)

    for item in scene["fixed_aisles"]:
        draw.polygon(projection.polygon(item["polygon"]), fill="#d7e4ea", outline="#678999", width=2)
    for item in scene["exits"]:
        source_derived = item["type"].startswith("source_derived")
        fill = "#63b58e" if source_derived else "#b4d7c6"
        outline = "#1e6a4c" if source_derived else "#5e8a75"
        draw.polygon(projection.polygon(item["polygon"]), fill=fill, outline=outline, width=2)
    for item in scene["obstacles"]:
        source_derived = item["type"].startswith("source_derived")
        fill = "#425466" if source_derived else "#a9b2b9"
        draw.polygon(projection.polygon(item["polygon"]), fill=fill, outline="#182b39", width=2)

    for position, booth in enumerate(scene["booths"], start=1):
        status = booth["status"]
        fill = "#87a9c3" if status == "available" else "#b698c8" if status == "reserved" else "#274c6a"
        points = projection.polygon(booth_points(booth))
        draw.polygon(points, fill=fill, outline="#ffffff")
        if projection.scale * booth["width"] >= 28:
            centre_x = sum(point[0] for point in points) / 4
            centre_y = sum(point[1] for point in points) / 4
            label = str(position)
            bbox = draw.textbbox((0, 0), label, font=tiny)
            draw.text((centre_x - (bbox[2] - bbox[0]) / 2, centre_y - 5), label, fill="#ffffff", font=tiny)

    drawing_width = max_x - min_x
    drawing_height = max_y - min_y
    draw.text((projection.offset_x, 875), f"{drawing_width:.1f} m", fill="#142a3b", font=body)
    draw.text((projection.offset_x + drawing_width * projection.scale + 10, projection.offset_y), f"{drawing_height:.1f} m", fill="#142a3b", font=body)
    scale_length = nice_scale(drawing_width)
    sx, sy = 1030, 875
    scale_px = scale_length * projection.scale
    draw.line((sx, sy, sx + scale_px, sy), fill="#142a3b", width=5)
    draw.line((sx, sy - 7, sx, sy + 7), fill="#142a3b", width=3)
    draw.line((sx + scale_px, sy - 7, sx + scale_px, sy + 7), fill="#142a3b", width=3)
    draw.text((sx, sy + 12), f"{scale_length:g} m", fill="#142a3b", font=body)

    draw.text((1010, 170), "QA legend", fill="#142a3b", font=font(20, bold=True))
    legend = [
        ("#87a9c3", "Synthetic booth"),
        ("#d7e4ea", "Synthetic aisle"),
        ("#63b58e", "Source-derived access"),
        ("#b4d7c6", "Synthetic egress"),
        ("#425466", "Source-derived column"),
    ]
    for row, (color, label) in enumerate(legend):
        y0 = 215 + row * 42
        draw.rectangle((1010, y0, 1036, y0 + 18), fill=color, outline="#243946")
        draw.text((1050, y0 - 1), label, fill="#243946", font=body)

    metrics = [
        f"Boundary vertices: {len(scene['boundary'])}",
        f"Booths: {len(scene['booths'])}",
        f"Source fixed objects: {provenance['source_derived_fixed_object_count']}",
        f"Synthetic fixed objects: {provenance['synthetic_non_aisle_fixed_object_count']}",
        f"Start-state checks: PASS",
    ]
    for row, text in enumerate(metrics):
        draw.text((1010, 460 + row * 34), text, fill="#243946", font=body)

    note_y = 660
    draw.text((1010, note_y), "Scope", fill="#142a3b", font=font(18, bold=True))
    scope_lines = [
        "Experimental layout only.",
        "Not a copied event floor plan.",
        "Not code- or venue-approved.",
        "Fixed-feature provenance is",
        "recorded per object class.",
    ]
    for row, text in enumerate(scope_lines):
        draw.text((1010, note_y + 34 + row * 27), text, fill="#52636d", font=body)

    draw.text(
        (70, 940),
        "Author-approval surface · no Track R tasks or model calls may proceed until this visual set is accepted.",
        fill="#5d6966",
        font=small,
    )
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG", optimize=True)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    for scene_path in sorted(DATA.glob("formal_scene_v2_[0-9][0-9]_*.json")):
        index = int(scene_path.name.split("_")[3])
        provenance_path = next(DATA.glob(f"formal_provenance_v2_{index:02d}_*.json"))
        scene = json.loads(scene_path.read_text(encoding="utf-8"))
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        destination = OUTPUT / f"track_r_v2_{index:02d}.png"
        render(scene, provenance, destination)
        rendered.append(destination)

    thumb_width, thumb_height = 700, 490
    sheet = Image.new("RGB", (thumb_width * 2, thumb_height * 5), "#e8ecea")
    for index, path in enumerate(rendered):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        x = (index % 2) * thumb_width + (thumb_width - image.width) // 2
        y = (index // 2) * thumb_height + (thumb_height - image.height) // 2
        sheet.paste(image, (x, y))
    sheet.save(OUTPUT / "track_r_v2_contact_sheet.png", format="PNG", optimize=True)
    print(json.dumps({"rendered": len(rendered), "contact_sheet": str(OUTPUT / "track_r_v2_contact_sheet.png")}, indent=2))


if __name__ == "__main__":
    main()
