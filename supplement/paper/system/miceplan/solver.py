from __future__ import annotations

from dataclasses import replace
from math import ceil

from .geometry import rectangle_intersects_polygon, rectangle_within_polygon, rectangles_overlap
from .models import Booth, HallLayout, LayoutEditIR, OperationType, PolygonObject


class SolveError(RuntimeError):
    pass


def _frange(start: float, stop: float, step: float):
    current = start
    while current <= stop + 1e-9:
        yield round(current, 6)
        current += step


class DeterministicLayoutSolver:
    """A bounded, reproducible grid-search solver for small research layouts."""

    def __init__(self, grid_step: float = 0.5, max_candidates: int = 250_000):
        if grid_step <= 0:
            raise ValueError("grid_step must be positive")
        self.grid_step = grid_step
        self.max_candidates = max_candidates

    def solve(self, layout: HallLayout, ir: LayoutEditIR) -> HallLayout:
        if ir.requires_confirmation:
            raise SolveError("The request requires confirmation before geometry compilation")
        if ir.source_layout_version != layout.version:
            raise SolveError("The request source version does not match the accepted layout")

        booths = list(layout.booths)
        fixed_aisles = list(layout.fixed_aisles)
        next_number = 1
        for operation_index, operation in enumerate(ir.operations):
            by_id = {booth.id: booth for booth in booths}
            targets = [by_id[target_id] for target_id in operation.target_ids if target_id in by_id]
            if len(targets) != len(operation.target_ids):
                raise SolveError("An operation references a booth that is not present in the source version")
            if any(booth.status in {"sold", "locked"} for booth in targets):
                raise SolveError("Sold or locked booth geometry cannot be changed")

            if operation.type == OperationType.REMOVE_BOOTH:
                booths = [booth for booth in booths if booth.id not in operation.target_ids]
            elif operation.type == OperationType.RESIZE_BOOTH:
                if operation.width is None or operation.height is None:
                    raise SolveError("RESIZE_BOOTH requires width and height")
                booths = [
                    replace(booth, width=operation.width, height=operation.height)
                    if booth.id in operation.target_ids else booth
                    for booth in booths
                ]
            elif operation.type == OperationType.MOVE_BOOTH:
                if not targets:
                    raise SolveError("MOVE_BOOTH requires at least one target")
                for target in targets:
                    remaining = [booth for booth in booths if booth.id != target.id]
                    if operation.x is not None and operation.y is not None:
                        moved = replace(target, x=operation.x, y=operation.y)
                        if not self._placement_valid(layout, moved, remaining, fixed_aisles):
                            raise SolveError(f"Explicit position for {target.number} violates a hard geometric constraint")
                    else:
                        moved = self._first_feasible(layout, target.width, target.height, remaining, fixed_aisles, operation.region)
                        moved = replace(moved, id=target.id, number=target.number, status=target.status, type=target.type, zone=target.zone, source_version=target.source_version)
                    booths = [moved if booth.id == target.id else booth for booth in booths]
            elif operation.type == OperationType.ADD_BOOTH:
                if operation.count is None or operation.width is None or operation.height is None:
                    raise SolveError("ADD_BOOTH requires count, width, and height")
                for _ in range(operation.count):
                    placed = self._first_feasible(layout, operation.width, operation.height, booths, fixed_aisles, operation.region)
                    new_booth = replace(
                        placed,
                        id=f"{ir.request_id}-op{operation_index}-b{next_number}",
                        number=self._next_visible_number(booths, next_number),
                        type=operation.booth_type or "standard",
                        source_version=layout.version,
                    )
                    booths.append(new_booth)
                    next_number += 1
            elif operation.type == OperationType.SPLIT_BOOTH:
                if not targets or operation.count is None or operation.width is None or operation.height is None:
                    raise SolveError("SPLIT_BOOTH requires targets, count, width, and height")
                min_x = min(booth.x for booth in targets)
                min_y = min(booth.y for booth in targets)
                max_x = max(booth.x + booth.width for booth in targets)
                max_y = max(booth.y + booth.height for booth in targets)
                booths = [booth for booth in booths if booth.id not in operation.target_ids]
                placed_batch = self._place_in_region(
                    layout,
                    operation.count,
                    operation.width,
                    operation.height,
                    booths,
                    fixed_aisles,
                    (min_x, min_y, max_x, max_y),
                )
                for placed in placed_batch:
                    booths.append(
                        replace(
                            placed,
                            id=f"{ir.request_id}-op{operation_index}-b{next_number}",
                            number=self._next_visible_number(booths, next_number),
                            type=operation.booth_type or "standard",
                            source_version=layout.version,
                        )
                    )
                    next_number += 1
            elif operation.type == OperationType.RESERVE_AISLE:
                if None in {operation.x, operation.y, operation.width, operation.height}:
                    raise SolveError("RESERVE_AISLE requires explicit x, y, width, and height")
                x, y = float(operation.x), float(operation.y)
                width, height = float(operation.width), float(operation.height)
                polygon = ((x, y), (x + width, y), (x + width, y + height), (x, y + height))
                fixed_aisles.append(PolygonObject(id=f"{ir.request_id}-aisle-{operation_index}", polygon=polygon, type="reserved_aisle"))
            else:
                raise SolveError(f"No compiler exists for operation {operation.type.value}")

        return HallLayout(
            hall_id=layout.hall_id,
            version=f"candidate-{ir.request_id}",
            unit=layout.unit,
            boundary=layout.boundary,
            obstacles=layout.obstacles,
            exits=layout.exits,
            fixed_aisles=tuple(fixed_aisles),
            booths=tuple(booths),
            parent_version=layout.version,
            request_id=ir.request_id,
        )

    def _placement_valid(self, layout: HallLayout, candidate: Booth, booths: list[Booth], fixed_aisles: list[PolygonObject]) -> bool:
        if not rectangle_within_polygon(candidate, layout.boundary):
            return False
        if any(rectangles_overlap(candidate, booth) for booth in booths):
            return False
        protected = layout.obstacles + tuple(fixed_aisles) + layout.exits
        return not any(rectangle_intersects_polygon(candidate, item.polygon) for item in protected)

    def _first_feasible(self, layout: HallLayout, width: float, height: float, booths: list[Booth], fixed_aisles: list[PolygonObject], region: str | None) -> Booth:
        min_x = min(point[0] for point in layout.boundary)
        max_x = max(point[0] for point in layout.boundary) - width
        min_y = min(point[1] for point in layout.boundary)
        max_y = max(point[1] for point in layout.boundary) - height
        xs = list(_frange(min_x, max_x, self.grid_step))
        ys = list(_frange(min_y, max_y, self.grid_step))
        if region == "east":
            xs.reverse()
        if region == "south":
            ys.reverse()
        if region in {"east", "west"}:
            positions = ((x, y) for x in xs for y in ys)
        else:
            positions = ((x, y) for y in ys for x in xs)
        examined = 0
        for x, y in positions:
            examined += 1
            if examined > self.max_candidates:
                break
            candidate = Booth(id="candidate", number="candidate", x=x, y=y, width=width, height=height)
            if self._placement_valid(layout, candidate, booths, fixed_aisles):
                return candidate
        raise SolveError("No feasible grid position was found within the configured search bound")

    def _place_in_region(
        self,
        layout: HallLayout,
        count: int,
        width: float,
        height: float,
        booths: list[Booth],
        fixed_aisles: list[PolygonObject],
        bounds: tuple[float, float, float, float],
    ) -> list[Booth]:
        min_x, min_y, max_x, max_y = bounds
        columns = int((max_x - min_x + 1e-9) // width)
        rows = int((max_y - min_y + 1e-9) // height)
        if columns * rows < count:
            raise SolveError("The selected booth region cannot contain the requested split at the declared dimensions")
        placed: list[Booth] = []
        for row in range(ceil(count / columns)):
            for column in range(columns):
                if len(placed) == count:
                    return placed
                candidate = Booth(
                    id="candidate",
                    number="candidate",
                    x=round(min_x + column * width, 6),
                    y=round(min_y + row * height, 6),
                    width=width,
                    height=height,
                )
                if self._placement_valid(layout, candidate, booths + placed, fixed_aisles):
                    placed.append(candidate)
        if len(placed) != count:
            raise SolveError("The selected region has insufficient feasible cells after protected geometry is applied")
        return placed

    @staticmethod
    def _next_visible_number(booths: list[Booth], seed: int) -> str:
        existing = {booth.number for booth in booths}
        value = seed
        while f"AI{value:03d}" in existing:
            value += 1
        return f"AI{value:03d}"
