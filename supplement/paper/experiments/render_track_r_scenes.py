from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "miceplan_lab_real_holdout_v0"
OUTPUT = DATA / "formal_visual_review_v1" / "png"


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
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def transform(points: list[list[float]], source_bounds: tuple[float, float, float, float]) -> list[tuple[float, float]]:
    min_x, min_y, max_x, max_y = source_bounds
    left, top, right, bottom = 45.0, 100.0, 710.0, 650.0
    scale = min((right - left) / (max_x - min_x), (bottom - top) / (max_y - min_y))
    offset_x = left + ((right - left) - (max_x - min_x) * scale) / 2
    offset_y = top + ((bottom - top) - (max_y - min_y) * scale) / 2
    return [
        (offset_x + (x - min_x) * scale, offset_y + (max_y - y) * scale)
        for x, y in points
    ]


def booth_points(booth: dict[str, Any]) -> list[list[float]]:
    x, y = float(booth["x"]), float(booth["y"])
    width, height = float(booth["width"]), float(booth["height"])
    return [[x, y], [x + width, y], [x + width, y + height], [x, y + height]]


def render(scene: dict[str, Any], provenance: dict[str, Any], destination: Path) -> None:
    canvas = Image.new("RGB", (1000, 720), "#f7f5ef")
    draw = ImageDraw.Draw(canvas)
    title_font = font(24, bold=True)
    subtitle_font = font(16)
    body_font = font(14)
    small_font = font(12)
    draw.text((45, 28), f"Track R {provenance['track_r_index']:02d}: {provenance['source_venue']}", fill="#183b36", font=title_font)
    draw.text((45, 62), f"{provenance['source_room']} - {provenance['operation_family']} - source-derived shell / synthetic state", fill="#415a55", font=subtitle_font)
    source_bounds = bounds(scene["boundary"])
    draw.polygon(transform(scene["boundary"], source_bounds), fill="#ffffff", outline="#183b36", width=3)

    fills = {"fixed_aisles": "#e4b84d", "exits": "#5f9f88", "obstacles": "#c05a47"}
    for group in ("fixed_aisles", "exits", "obstacles"):
        for item in scene[group]:
            draw.polygon(transform(item["polygon"], source_bounds), fill=fills[group], outline="#183b36")
    for booth in scene["booths"]:
        status = booth["status"]
        fill = "#839b91" if status == "available" else "#6d7898" if status == "reserved" else "#414b4a"
        draw.polygon(transform(booth_points(booth), source_bounds), fill=fill, outline="#ffffff")

    draw.text((760, 130), "Legend", fill="#183b36", font=font(17, bold=True))
    legend = [
        ("#839b91", "synthetic booth"),
        ("#e4b84d", "synthetic aisle"),
        ("#5f9f88", "synthetic exit zone"),
        ("#c05a47", "synthetic obstacle"),
    ]
    for index, (color, label) in enumerate(legend):
        y = 168 + index * 34
        draw.rectangle((760, y, 780, y + 14), fill=color, outline="#183b36")
        draw.text((790, y - 1), label, fill="#183b36", font=body_font)
    draw.text((760, 330), f"Boundary vertices: {len(scene['boundary'])}", fill="#183b36", font=body_font)
    draw.text((760, 356), f"Booths: {len(scene['booths'])}", fill="#183b36", font=body_font)
    draw.text((760, 382), f"Protected areas: {scene['complexity_features']['protected_polygon_count']}", fill="#183b36", font=body_font)
    draw.text((760, 408), f"Area diff: {provenance['relative_area_difference'] * 100:.2f}%", fill="#183b36", font=body_font)
    draw.text((45, 684), "Internal QA view. Original venue plan is not reproduced. Not a professional, regulatory, or event-ready layout.", fill="#5d6966", font=small_font)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, format="PNG", optimize=True)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    for scene_path in sorted(DATA.glob("formal_scene_[0-9][0-9]_*.json")):
        index = int(scene_path.name.split("_")[2])
        provenance_path = next(DATA.glob(f"formal_provenance_{index:02d}_*.json"))
        scene = json.loads(scene_path.read_text(encoding="utf-8"))
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        destination = OUTPUT / f"track_r_{index:02d}.png"
        render(scene, provenance, destination)
        rendered.append(destination)

    thumb_width, thumb_height = 500, 360
    sheet = Image.new("RGB", (thumb_width * 2, thumb_height * 5), "#ece9e0")
    for index, path in enumerate(rendered):
        image = Image.open(path).convert("RGB")
        image.thumbnail((thumb_width, thumb_height), Image.Resampling.LANCZOS)
        x = (index % 2) * thumb_width + (thumb_width - image.width) // 2
        y = (index // 2) * thumb_height + (thumb_height - image.height) // 2
        sheet.paste(image, (x, y))
    sheet.save(OUTPUT / "track_r_contact_sheet.png", format="PNG", optimize=True)
    print(json.dumps({"rendered": len(rendered), "contact_sheet": str(OUTPUT / 'track_r_contact_sheet.png')}, indent=2))


if __name__ == "__main__":
    main()
