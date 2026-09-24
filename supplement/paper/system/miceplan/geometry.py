from __future__ import annotations

from itertools import combinations

from .models import Booth, DiffEntry, HallLayout, LayoutEditIR, RuleCheck, ValidationReport

EPSILON = 1e-9


def _cross(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> float:
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def _point_on_segment(point: tuple[float, float], a: tuple[float, float], b: tuple[float, float]) -> bool:
    if abs(_cross(a, b, point)) > EPSILON:
        return False
    return min(a[0], b[0]) - EPSILON <= point[0] <= max(a[0], b[0]) + EPSILON and min(a[1], b[1]) - EPSILON <= point[1] <= max(a[1], b[1]) + EPSILON


def point_in_polygon(point: tuple[float, float], polygon: tuple[tuple[float, float], ...], include_boundary: bool = True) -> bool:
    inside = False
    for index, a in enumerate(polygon):
        b = polygon[(index + 1) % len(polygon)]
        if _point_on_segment(point, a, b):
            return include_boundary
        if (a[1] > point[1]) != (b[1] > point[1]):
            x_at_y = (b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0]
            if x_at_y > point[0]:
                inside = not inside
    return inside


def _proper_segment_intersection(a: tuple[float, float], b: tuple[float, float], c: tuple[float, float], d: tuple[float, float]) -> bool:
    ab_c, ab_d = _cross(a, b, c), _cross(a, b, d)
    cd_a, cd_b = _cross(c, d, a), _cross(c, d, b)
    return ((ab_c > EPSILON and ab_d < -EPSILON) or (ab_c < -EPSILON and ab_d > EPSILON)) and ((cd_a > EPSILON and cd_b < -EPSILON) or (cd_a < -EPSILON and cd_b > EPSILON))


def booth_polygon(booth: Booth) -> tuple[tuple[float, float], ...]:
    return (
        (booth.x, booth.y),
        (booth.x + booth.width, booth.y),
        (booth.x + booth.width, booth.y + booth.height),
        (booth.x, booth.y + booth.height),
    )


def _edges(polygon: tuple[tuple[float, float], ...]):
    for index, point in enumerate(polygon):
        yield point, polygon[(index + 1) % len(polygon)]


def rectangle_within_polygon(booth: Booth, polygon: tuple[tuple[float, float], ...]) -> bool:
    rectangle = booth_polygon(booth)
    if not all(point_in_polygon(point, polygon, include_boundary=True) for point in rectangle):
        return False
    return not any(_proper_segment_intersection(a, b, c, d) for a, b in _edges(rectangle) for c, d in _edges(polygon))


def rectangles_overlap(first: Booth, second: Booth) -> bool:
    return (
        first.x < second.x + second.width - EPSILON
        and first.x + first.width > second.x + EPSILON
        and first.y < second.y + second.height - EPSILON
        and first.y + first.height > second.y + EPSILON
    )


def rectangle_intersects_polygon(booth: Booth, polygon: tuple[tuple[float, float], ...]) -> bool:
    rectangle = booth_polygon(booth)
    if any(_proper_segment_intersection(a, b, c, d) for a, b in _edges(rectangle) for c, d in _edges(polygon)):
        return True
    center = (booth.x + booth.width / 2, booth.y + booth.height / 2)
    if point_in_polygon(center, polygon, include_boundary=False):
        return True
    if any(point_in_polygon(point, polygon, include_boundary=False) for point in rectangle):
        return True
    return any(
        booth.x + EPSILON < point[0] < booth.x + booth.width - EPSILON
        and booth.y + EPSILON < point[1] < booth.y + booth.height - EPSILON
        for point in polygon
    )


def compute_diff(source: HallLayout, candidate: HallLayout) -> tuple[DiffEntry, ...]:
    before = {booth.id: booth for booth in source.booths}
    after = {booth.id: booth for booth in candidate.booths}
    result: list[DiffEntry] = []
    for object_id in sorted(before.keys() | after.keys()):
        old, new = before.get(object_id), after.get(object_id)
        if old is None:
            change = "added"
        elif new is None:
            change = "removed"
        elif (old.x, old.y) != (new.x, new.y) and (old.width, old.height) != (new.width, new.height):
            change = "moved_and_resized"
        elif (old.x, old.y) != (new.x, new.y):
            change = "moved"
        elif (old.width, old.height) != (new.width, new.height):
            change = "resized"
        elif old != new:
            change = "metadata_changed"
        else:
            change = "unchanged"
        if change != "unchanged":
            result.append(DiffEntry(change, object_id, old.to_dict() if old else None, new.to_dict() if new else None))
    return tuple(result)


class GeometryValidator:
    def validate(self, source: HallLayout, candidate: HallLayout, ir: LayoutEditIR | None = None) -> ValidationReport:
        checks: list[RuleCheck] = []
        outside = [booth.id for booth in candidate.booths if not rectangle_within_polygon(booth, candidate.boundary)]
        checks.append(RuleCheck("within_boundary", not outside, "All booths are inside the configured hall boundary." if not outside else "Booths extend outside the configured hall boundary.", tuple(outside)))

        overlaps = [(first.id, second.id) for first, second in combinations(candidate.booths, 2) if rectangles_overlap(first, second)]
        overlap_ids = tuple(dict.fromkeys(item for pair in overlaps for item in pair))
        checks.append(RuleCheck("no_overlap", not overlaps, "No booth interiors overlap." if not overlaps else f"Detected {len(overlaps)} booth-overlap pair(s).", overlap_ids))

        protected = candidate.obstacles + candidate.fixed_aisles + candidate.exits
        outside_protected = [area.id for area in protected if not all(point_in_polygon(point, candidate.boundary, include_boundary=True) for point in area.polygon)]
        checks.append(RuleCheck("protected_polygons_within_boundary", not outside_protected, "All protected polygons are inside the configured hall boundary." if not outside_protected else "A protected polygon extends outside the configured hall boundary.", tuple(outside_protected)))
        collisions: list[str] = []
        protected_ids: list[str] = []
        for booth in candidate.booths:
            for area in protected:
                if rectangle_intersects_polygon(booth, area.polygon):
                    collisions.append(booth.id)
                    protected_ids.append(area.id)
        collision_objects = tuple(dict.fromkeys(collisions + protected_ids))
        checks.append(RuleCheck("avoid_protected_polygons", not collisions, "No booth intersects an obstacle, protected aisle, or exit-clearance polygon." if not collisions else "At least one booth intersects a protected polygon.", collision_objects))

        ids = [booth.id for booth in candidate.booths]
        numbers = [booth.number for booth in candidate.booths]
        duplicate_ids = sorted({item for item in ids if ids.count(item) > 1})
        duplicate_numbers = sorted({item for item in numbers if numbers.count(item) > 1})
        checks.append(RuleCheck("unique_identifiers", not duplicate_ids and not duplicate_numbers, "Booth IDs and visible numbers are unique." if not duplicate_ids and not duplicate_numbers else "Duplicate booth IDs or visible numbers were found.", tuple(duplicate_ids + duplicate_numbers)))

        candidate_by_id = {booth.id: booth for booth in candidate.booths}
        changed_protected: list[str] = []
        for booth in source.booths:
            if booth.status in {"sold", "locked"} and candidate_by_id.get(booth.id) != booth:
                changed_protected.append(booth.id)
        checks.append(RuleCheck("preserve_sold_and_locked", not changed_protected, "Sold and locked booths preserve identity, geometry, and metadata." if not changed_protected else "A sold or locked booth was removed or changed.", tuple(changed_protected)))

        if ir is not None:
            operation_failures: list[str] = []
            source_ids = {booth.id for booth in source.booths}
            new_booths = [booth for booth in candidate.booths if booth.id not in source_ids]
            current = {booth.id: booth for booth in candidate.booths}
            original = {booth.id: booth for booth in source.booths}
            for index, operation in enumerate(ir.operations):
                label = f"operation:{index}:{operation.type.value}"
                if operation.type.value in {"ADD_BOOTH", "SPLIT_BOOTH"}:
                    matching = [booth for booth in new_booths if booth.id.startswith(f"{ir.request_id}-")]
                    if operation.count is not None and len(matching) < operation.count:
                        operation_failures.append(label)
                    if operation.width is not None and any(abs(booth.width - operation.width) > EPSILON for booth in matching):
                        operation_failures.append(label)
                    if operation.height is not None and any(abs(booth.height - operation.height) > EPSILON for booth in matching):
                        operation_failures.append(label)
                elif operation.type.value == "REMOVE_BOOTH" and any(target in current for target in operation.target_ids):
                    operation_failures.append(label)
                elif operation.type.value == "MOVE_BOOTH" and any(target not in current or (current[target].x, current[target].y) == (original[target].x, original[target].y) for target in operation.target_ids):
                    operation_failures.append(label)
                elif operation.type.value == "RESIZE_BOOTH" and any(target not in current or (current[target].width, current[target].height) == (original[target].width, original[target].height) for target in operation.target_ids):
                    operation_failures.append(label)
                elif operation.type.value == "RESERVE_AISLE" and not any(area.id.startswith(f"{ir.request_id}-aisle-{index}") for area in candidate.fixed_aisles):
                    operation_failures.append(label)
            checks.append(RuleCheck("operation_satisfaction", not operation_failures, "The candidate satisfies every explicit edit operation." if not operation_failures else "At least one explicit edit operation is not satisfied.", tuple(dict.fromkeys(operation_failures))))

        return ValidationReport(valid=all(check.passed for check in checks), checks=tuple(checks))
