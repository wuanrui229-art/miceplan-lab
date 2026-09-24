from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class ModelError(ValueError):
    """Raised when an external payload violates the research contract."""


class OperationType(str, Enum):
    ADD_BOOTH = "ADD_BOOTH"
    MOVE_BOOTH = "MOVE_BOOTH"
    RESIZE_BOOTH = "RESIZE_BOOTH"
    REMOVE_BOOTH = "REMOVE_BOOTH"
    SPLIT_BOOTH = "SPLIT_BOOTH"
    RESERVE_AISLE = "RESERVE_AISLE"


class BoothStatus(str, Enum):
    AVAILABLE = "available"
    RESERVED = "reserved"
    SOLD = "sold"
    LOCKED = "locked"


@dataclass(frozen=True)
class Booth:
    id: str
    number: str
    x: float
    y: float
    width: float
    height: float
    status: str = BoothStatus.AVAILABLE.value
    type: str = "standard"
    zone: str | None = None
    source_version: str = "v1"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Booth":
        required = ("id", "number", "x", "y", "width", "height")
        missing = [key for key in required if key not in data]
        if missing:
            raise ModelError(f"Booth is missing fields: {', '.join(missing)}")
        width, height = float(data["width"]), float(data["height"])
        if width <= 0 or height <= 0:
            raise ModelError("Booth width and height must be positive")
        status = str(data.get("status", BoothStatus.AVAILABLE.value))
        if status not in {item.value for item in BoothStatus}:
            raise ModelError(f"Unknown booth status: {status}")
        return cls(
            id=str(data["id"]),
            number=str(data["number"]),
            x=float(data["x"]),
            y=float(data["y"]),
            width=width,
            height=height,
            status=status,
            type=str(data.get("type", "standard")),
            zone=data.get("zone"),
            source_version=str(data.get("source_version", "v1")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PolygonObject:
    id: str
    polygon: tuple[tuple[float, float], ...]
    type: str = "protected"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PolygonObject":
        points = data.get("polygon")
        if not isinstance(points, list) or len(points) < 3:
            raise ModelError("A polygon requires at least three points")
        normalized = tuple((float(point[0]), float(point[1])) for point in points)
        return cls(id=str(data["id"]), polygon=normalized, type=str(data.get("type", "protected")))

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "polygon": [list(point) for point in self.polygon], "type": self.type}


@dataclass(frozen=True)
class HallLayout:
    hall_id: str
    version: str
    boundary: tuple[tuple[float, float], ...]
    booths: tuple[Booth, ...]
    unit: str = "m"
    obstacles: tuple[PolygonObject, ...] = ()
    exits: tuple[PolygonObject, ...] = ()
    fixed_aisles: tuple[PolygonObject, ...] = ()
    parent_version: str | None = None
    request_id: str | None = None
    accepted_at: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HallLayout":
        if data.get("unit", "m") != "m":
            raise ModelError("The canonical hall unit must be metres")
        boundary = data.get("boundary")
        if not isinstance(boundary, list) or len(boundary) < 3:
            raise ModelError("Hall boundary requires at least three points")
        return cls(
            hall_id=str(data["hall_id"]),
            version=str(data["version"]),
            unit="m",
            boundary=tuple((float(point[0]), float(point[1])) for point in boundary),
            booths=tuple(Booth.from_dict(item) for item in data.get("booths", [])),
            obstacles=tuple(PolygonObject.from_dict(item) for item in data.get("obstacles", [])),
            exits=tuple(PolygonObject.from_dict(item) for item in data.get("exits", [])),
            fixed_aisles=tuple(PolygonObject.from_dict(item) for item in data.get("fixed_aisles", [])),
            parent_version=data.get("parent_version"),
            request_id=data.get("request_id"),
            accepted_at=data.get("accepted_at"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "hall_id": self.hall_id,
            "version": self.version,
            "unit": self.unit,
            "boundary": [list(point) for point in self.boundary],
            "obstacles": [item.to_dict() for item in self.obstacles],
            "exits": [item.to_dict() for item in self.exits],
            "fixed_aisles": [item.to_dict() for item in self.fixed_aisles],
            "booths": [item.to_dict() for item in self.booths],
            "parent_version": self.parent_version,
            "request_id": self.request_id,
            "accepted_at": self.accepted_at,
        }


@dataclass(frozen=True)
class Operation:
    type: OperationType
    target_ids: tuple[str, ...] = ()
    count: int | None = None
    width: float | None = None
    height: float | None = None
    x: float | None = None
    y: float | None = None
    region: str | None = None
    booth_type: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Operation":
        required = {"type", "target_ids", "count", "width", "height", "x", "y", "region", "booth_type"}
        missing = sorted(required - data.keys())
        extras = sorted(data.keys() - required)
        if missing:
            raise ModelError(f"Operation is missing fields: {', '.join(missing)}")
        if extras:
            raise ModelError(f"Operation contains unknown fields: {', '.join(extras)}")
        if not isinstance(data["target_ids"], list):
            raise ModelError("Operation target_ids must be an array")
        try:
            operation_type = OperationType(str(data["type"]))
        except (KeyError, ValueError) as exc:
            raise ModelError(f"Unsupported operation type: {data.get('type')}") from exc
        count = data.get("count")
        if count is not None and (not isinstance(count, int) or isinstance(count, bool) or count <= 0):
            raise ModelError("Operation count must be a positive integer or null")
        numeric: dict[str, float | None] = {}
        for key in ("width", "height", "x", "y"):
            value = data.get(key)
            numeric[key] = None if value is None else float(value)
        if numeric["width"] is not None and numeric["width"] <= 0:
            raise ModelError("Operation width must be positive")
        if numeric["height"] is not None and numeric["height"] <= 0:
            raise ModelError("Operation height must be positive")
        region = data.get("region")
        if region not in {None, "north", "south", "east", "west"}:
            raise ModelError(f"Unsupported operation region: {region}")
        booth_type = data.get("booth_type")
        if booth_type not in {None, "standard", "custom"}:
            raise ModelError(f"Unsupported booth type: {booth_type}")
        return cls(
            type=operation_type,
            target_ids=tuple(str(item) for item in data.get("target_ids", [])),
            count=count,
            width=numeric["width"],
            height=numeric["height"],
            x=numeric["x"],
            y=numeric["y"],
            region=region,
            booth_type=booth_type,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type.value,
            "target_ids": list(self.target_ids),
            "count": self.count,
            "width": self.width,
            "height": self.height,
            "x": self.x,
            "y": self.y,
            "region": self.region,
            "booth_type": self.booth_type,
        }


@dataclass(frozen=True)
class LayoutEditIR:
    request_id: str
    source_layout_version: str
    language: str
    operations: tuple[Operation, ...]
    hard_constraints: tuple[str, ...] = ()
    preferences: tuple[str, ...] = ()
    assumptions: tuple[str, ...] = ()
    unresolved_references: tuple[str, ...] = ()
    requires_confirmation: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LayoutEditIR":
        required = {
            "request_id",
            "source_layout_version",
            "language",
            "operations",
            "hard_constraints",
            "preferences",
            "assumptions",
            "unresolved_references",
            "requires_confirmation",
        }
        missing = sorted(required - data.keys())
        extras = sorted(data.keys() - required)
        if missing:
            raise ModelError(f"LayoutEditIR is missing fields: {', '.join(missing)}")
        if extras:
            raise ModelError(f"LayoutEditIR contains unknown fields: {', '.join(extras)}")
        if data["language"] not in {"zh", "en"}:
            raise ModelError("Language must be zh or en")
        array_fields = ("operations", "hard_constraints", "preferences", "assumptions", "unresolved_references")
        if any(not isinstance(data[key], list) for key in array_fields):
            raise ModelError("LayoutEditIR collection fields must be arrays")
        if not isinstance(data["requires_confirmation"], bool):
            raise ModelError("requires_confirmation must be a boolean")
        return cls(
            request_id=str(data["request_id"]),
            source_layout_version=str(data["source_layout_version"]),
            language=str(data["language"]),
            operations=tuple(Operation.from_dict(item) for item in data["operations"]),
            hard_constraints=tuple(str(item) for item in data["hard_constraints"]),
            preferences=tuple(str(item) for item in data["preferences"]),
            assumptions=tuple(str(item) for item in data["assumptions"]),
            unresolved_references=tuple(str(item) for item in data["unresolved_references"]),
            requires_confirmation=data["requires_confirmation"],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "source_layout_version": self.source_layout_version,
            "language": self.language,
            "operations": [item.to_dict() for item in self.operations],
            "hard_constraints": list(self.hard_constraints),
            "preferences": list(self.preferences),
            "assumptions": list(self.assumptions),
            "unresolved_references": list(self.unresolved_references),
            "requires_confirmation": self.requires_confirmation,
        }


@dataclass(frozen=True)
class RuleCheck:
    rule: str
    passed: bool
    message: str
    object_ids: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {"rule": self.rule, "passed": self.passed, "message": self.message, "object_ids": list(self.object_ids)}


@dataclass(frozen=True)
class ValidationReport:
    valid: bool
    checks: tuple[RuleCheck, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"valid": self.valid, "checks": [item.to_dict() for item in self.checks]}


@dataclass(frozen=True)
class DiffEntry:
    change: str
    object_id: str
    before: dict[str, Any] | None
    after: dict[str, Any] | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Proposal:
    id: str
    project_id: str
    source_version: str
    state: str
    request_text: str
    ir: LayoutEditIR
    candidate: HallLayout | None = None
    validation: ValidationReport | None = None
    diff: tuple[DiffEntry, ...] = ()
    error: str | None = None
    created_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "source_version": self.source_version,
            "state": self.state,
            "request_text": self.request_text,
            "ir": self.ir.to_dict(),
            "candidate": self.candidate.to_dict() if self.candidate else None,
            "validation": self.validation.to_dict() if self.validation else None,
            "diff": [item.to_dict() for item in self.diff],
            "error": self.error,
            "created_version": self.created_version,
        }


LAYOUT_EDIT_IR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "request_id",
        "source_layout_version",
        "language",
        "operations",
        "hard_constraints",
        "preferences",
        "assumptions",
        "unresolved_references",
        "requires_confirmation",
    ],
    "properties": {
        "request_id": {"type": "string"},
        "source_layout_version": {"type": "string"},
        "language": {"type": "string", "enum": ["zh", "en"]},
        "operations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["type", "target_ids", "count", "width", "height", "x", "y", "region", "booth_type"],
                "properties": {
                    "type": {"type": "string", "enum": [item.value for item in OperationType]},
                    "target_ids": {"type": "array", "items": {"type": "string"}},
                    "count": {"type": ["integer", "null"], "minimum": 1},
                    "width": {"type": ["number", "null"], "exclusiveMinimum": 0},
                    "height": {"type": ["number", "null"], "exclusiveMinimum": 0},
                    "x": {"type": ["number", "null"]},
                    "y": {"type": ["number", "null"]},
                    "region": {
                        "type": ["string", "null"],
                        "enum": ["north", "south", "east", "west", None],
                    },
                    "booth_type": {
                        "type": ["string", "null"],
                        "enum": ["standard", "custom", None],
                    },
                },
            },
        },
        "hard_constraints": {"type": "array", "items": {"type": "string"}},
        "preferences": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "unresolved_references": {"type": "array", "items": {"type": "string"}},
        "requires_confirmation": {"type": "boolean"},
    },
}
