from __future__ import annotations

import html
import json
import sys
from pathlib import Path


PAPER = Path(__file__).resolve().parents[1]
SYSTEM = PAPER / "system"
DATASET = PAPER / "data" / "miceplan_eval_v1_1"
OUTPUT = PAPER / "figures" / "layout_case.svg"
sys.path.insert(0, str(SYSTEM))

from miceplan.models import HallLayout, LayoutEditIR
from miceplan.solver import DeterministicLayoutSolver


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    request = next(row for row in load_jsonl(DATASET / "requests.jsonl") if row["request_id"] == "eval-025-en")
    source_data = next(row for row in load_jsonl(DATASET / "halls.jsonl") if row["hall_id"] == request["hall_id"])
    source = HallLayout.from_dict(source_data)
    gold = LayoutEditIR.from_dict(request["gold_ir"])
    candidate = DeterministicLayoutSolver().solve(source, gold)

    width, height = 700, 820
    panel_x, panel_width, panel_height = 45, 610, 300
    source_y, candidate_y = 105, 465
    min_x = min(x for x, _ in source.boundary)
    max_x = max(x for x, _ in source.boundary)
    min_y = min(y for _, y in source.boundary)
    max_y = max(y for _, y in source.boundary)
    scale = min((panel_width - 30) / (max_x - min_x), (panel_height - 30) / (max_y - min_y))

    source_ids = {booth.id for booth in source.booths}
    candidate_ids = {booth.id for booth in candidate.booths}
    removed = [booth for booth in source.booths if booth.id not in candidate_ids]

    def point(x: float, y: float, panel_y: float) -> tuple[float, float]:
        return panel_x + 15 + (x - min_x) * scale, panel_y + panel_height - 15 - (y - min_y) * scale

    def polygon(points, panel_y: float) -> str:
        return " ".join(f"{px:.1f},{py:.1f}" for px, py in (point(x, y, panel_y) for x, y in points))

    def rect(x: float, y: float, w: float, h: float, panel_y: float) -> tuple[float, float, float, float]:
        left, bottom = point(x, y, panel_y)
        return left, bottom - h * scale, w * scale, h * scale

    def draw_panel(layout: HallLayout, panel_y: float, title: str, candidate_panel: bool) -> list[str]:
        out = [
            f'<text x="45" y="{panel_y - 18}" class="panel-title">{html.escape(title)}</text>',
            f'<rect x="{panel_x}" y="{panel_y}" width="{panel_width}" height="{panel_height}" rx="8" class="panel"/>',
            f'<polygon points="{polygon(layout.boundary, panel_y)}" class="hall"/>',
        ]
        for area in layout.fixed_aisles:
            out.append(f'<polygon points="{polygon(area.polygon, panel_y)}" class="aisle"/>')
        for area in layout.exits:
            out.append(f'<polygon points="{polygon(area.polygon, panel_y)}" class="exit"/>')
        for area in layout.obstacles:
            out.append(f'<polygon points="{polygon(area.polygon, panel_y)}" class="obstacle"/>')
        for booth in layout.booths:
            x, y, w, h = rect(booth.x, booth.y, booth.width, booth.height, panel_y)
            if booth.id not in source_ids:
                css = "booth added"
            elif booth.status in {"sold", "locked"}:
                css = "booth protected"
            else:
                css = "booth"
            out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" class="{css}"/>')
            out.append(f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + 3:.1f}" class="booth-label">{html.escape(booth.number)}</text>')
        if candidate_panel:
            for booth in removed:
                x, y, w, h = rect(booth.x, booth.y, booth.width, booth.height, panel_y)
                out.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="2" class="removed"/>')
                out.append(f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + 3:.1f}" class="removed-label">removed</text>')
        return out

    svg = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<style>
  text {{ font-family: Arial, Helvetica, sans-serif; fill: #172033; }}
  .title {{ font-size: 21px; font-weight: 700; }}
  .subtitle {{ font-size: 13px; fill: #4b5563; }}
  .panel-title {{ font-size: 16px; font-weight: 700; }}
  .panel {{ fill: #fbfcfe; stroke: #cbd5e1; stroke-width: 1.5; }}
  .hall {{ fill: #ffffff; stroke: #334155; stroke-width: 2; }}
  .aisle {{ fill: #dcfce7; stroke: #22c55e; stroke-width: 1.2; }}
  .exit {{ fill: #fef3c7; stroke: #d97706; stroke-width: 1.2; }}
  .obstacle {{ fill: #fee2e2; stroke: #dc2626; stroke-width: 1.2; }}
  .booth {{ fill: #e2e8f0; stroke: #64748b; stroke-width: 1; }}
  .protected {{ fill: #fed7aa; stroke: #ea580c; stroke-width: 1.4; }}
  .added {{ fill: #bfdbfe; stroke: #2563eb; stroke-width: 1.6; }}
  .removed {{ fill: none; stroke: #dc2626; stroke-width: 1.8; stroke-dasharray: 5 4; }}
  .booth-label {{ font-size: 9px; text-anchor: middle; }}
  .removed-label {{ font-size: 8px; fill: #b91c1c; text-anchor: middle; }}
  .legend {{ font-size: 11px; fill: #334155; }}
</style>
<text x="45" y="35" class="title">Executable compound edit on held-out hall-025</text>
<text x="45" y="58" class="subtitle">Remove A103, add two 3 x 3 m booths in the east, and preserve sold booths.</text>''']
    svg.extend(draw_panel(source, source_y, "Accepted source version v1", False))
    svg.extend(draw_panel(candidate, candidate_y, "Validated candidate (awaiting approval)", True))
    legend_y = 795
    svg.extend([
        f'<rect x="65" y="{legend_y - 10}" width="18" height="12" class="booth protected"/><text x="90" y="{legend_y}" class="legend">sold or locked</text>',
        f'<rect x="215" y="{legend_y - 10}" width="18" height="12" class="booth added"/><text x="240" y="{legend_y}" class="legend">new booth</text>',
        f'<rect x="340" y="{legend_y - 10}" width="18" height="12" class="removed"/><text x="365" y="{legend_y}" class="legend">removed source booth</text>',
        f'<rect x="535" y="{legend_y - 10}" width="18" height="12" class="aisle"/><text x="560" y="{legend_y}" class="legend">fixed aisle</text>',
        '</svg>',
    ])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(svg), encoding="utf-8")
    print(OUTPUT)


if __name__ == "__main__":
    main()
