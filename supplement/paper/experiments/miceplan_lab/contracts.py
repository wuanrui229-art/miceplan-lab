from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import DATASET_VERSION, PROTOCOL_VERSION


OPERATION_FAMILIES = (
    "ADD_BOOTH",
    "MOVE_BOOTH",
    "RESIZE_BOOTH",
    "REMOVE_BOOTH",
    "SPLIT_BOOTH",
    "RESERVE_AISLE",
)

COMPLEXITIES = ("C1", "C2", "C3")

STRESS_CLASSES = (
    "FEASIBLE_CONTROL",
    "BOUNDARY",
    "OVERLAP",
    "PROTECTED_POLYGON",
    "LOCKED_MUTATION",
    "AMBIGUOUS_TARGET",
    "MISSING_EVIDENCE",
)

FAIL_STRESS_CLASSES = {
    "BOUNDARY",
    "OVERLAP",
    "PROTECTED_POLYGON",
    "LOCKED_MUTATION",
}

UNKNOWN_STRESS_CLASSES = {"AMBIGUOUS_TARGET", "MISSING_EVIDENCE"}


POINT_SCHEMA: dict[str, Any] = {
    "type": "array",
    "prefixItems": [{"type": "number"}, {"type": "number"}],
    "items": False,
    "minItems": 2,
    "maxItems": 2,
}

POLYGON_SCHEMA: dict[str, Any] = {
    "type": "array",
    "items": POINT_SCHEMA,
    "minItems": 3,
}

OPERATION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": [
        "type",
        "target_ids",
        "count",
        "width",
        "height",
        "x",
        "y",
        "region",
        "booth_type",
    ],
    "properties": {
        "type": {"type": "string", "enum": list(OPERATION_FAMILIES)},
        "target_ids": {"type": "array", "items": {"type": "string"}},
        "count": {"type": ["integer", "null"], "minimum": 1},
        "width": {"type": ["number", "null"], "exclusiveMinimum": 0},
        "height": {"type": ["number", "null"], "exclusiveMinimum": 0},
        "x": {"type": ["number", "null"]},
        "y": {"type": ["number", "null"]},
        "region": {"type": ["string", "null"], "enum": [None, "north", "south", "east", "west"]},
        "booth_type": {"type": ["string", "null"], "enum": [None, "standard", "custom"]},
    },
}

IR_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://miceplan-lab.local/schema/layout-edit-ir-v1.json",
    "title": "MICEPlan-Lab LayoutEditIR",
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
        "request_id": {"type": "string", "minLength": 1},
        "source_layout_version": {"type": "string", "minLength": 1},
        "language": {"type": "string", "enum": ["zh", "en"]},
        "operations": {"type": "array", "items": OPERATION_SCHEMA},
        "hard_constraints": {"type": "array", "items": {"type": "string"}},
        "preferences": {"type": "array", "items": {"type": "string"}},
        "assumptions": {"type": "array", "items": {"type": "string"}},
        "unresolved_references": {"type": "array", "items": {"type": "string"}},
        "requires_confirmation": {"type": "boolean"},
    },
}

POLYGON_OBJECT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "type", "polygon"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "type": {"type": "string", "minLength": 1},
        "polygon": POLYGON_SCHEMA,
    },
}

BOOTH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["id", "number", "x", "y", "width", "height", "status", "type"],
    "properties": {
        "id": {"type": "string", "minLength": 1},
        "number": {"type": "string", "minLength": 1},
        "x": {"type": "number"},
        "y": {"type": "number"},
        "width": {"type": "number", "exclusiveMinimum": 0},
        "height": {"type": "number", "exclusiveMinimum": 0},
        "status": {"enum": ["available", "reserved", "sold", "locked"]},
        "type": {"type": "string", "minLength": 1},
    },
}

SCENE_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://miceplan-lab.local/schema/scene-v1.json",
    "title": "MICEPlan-Lab Scene",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "scene_id",
        "split",
        "version",
        "unit",
        "boundary",
        "booths",
        "obstacles",
        "fixed_aisles",
        "exits",
        "complexity_features",
    ],
    "properties": {
        "scene_id": {"type": "string", "minLength": 1},
        "split": {"enum": ["development", "test"]},
        "version": {"const": "v1"},
        "unit": {"const": "m"},
        "boundary": POLYGON_SCHEMA,
        "booths": {"type": "array", "items": BOOTH_SCHEMA, "minItems": 6},
        "obstacles": {"type": "array", "items": POLYGON_OBJECT_SCHEMA},
        "fixed_aisles": {"type": "array", "items": POLYGON_OBJECT_SCHEMA},
        "exits": {"type": "array", "items": POLYGON_OBJECT_SCHEMA, "minItems": 2},
        "complexity_features": {
            "type": "object",
            "additionalProperties": False,
            "required": ["boundary_vertices", "booth_count", "protected_polygon_count"],
            "properties": {
                "boundary_vertices": {"type": "integer", "minimum": 4},
                "booth_count": {"type": "integer", "minimum": 6},
                "protected_polygon_count": {"type": "integer", "minimum": 1},
            },
        },
    },
}

CONTEXT_MASK_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["hide_unit", "hide_scale", "hide_disambiguating_labels"],
    "properties": {
        "hide_unit": {"type": "boolean"},
        "hide_scale": {"type": "boolean"},
        "hide_disambiguating_labels": {"type": "boolean"},
    },
}

REQUEST_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://miceplan-lab.local/schema/request-v1.json",
    "title": "MICEPlan-Lab Request",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "request_id",
        "semantic_task_id",
        "split",
        "scene_id",
        "language",
        "text",
        "operation_family",
        "complexity",
        "pair_id",
        "context_mask",
    ],
    "properties": {
        "request_id": {"type": "string", "minLength": 1},
        "semantic_task_id": {"type": "string", "minLength": 1},
        "split": {"enum": ["development", "test"]},
        "scene_id": {"type": "string", "minLength": 1},
        "language": {"enum": ["zh", "en"]},
        "text": {"type": "string", "minLength": 1},
        "operation_family": {"enum": list(OPERATION_FAMILIES)},
        "complexity": {"enum": list(COMPLEXITIES)},
        "pair_id": {"type": "string", "minLength": 1},
        "context_mask": CONTEXT_MASK_SCHEMA,
    },
}

GOLD_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://miceplan-lab.local/schema/gold-v1.json",
    "title": "MICEPlan-Lab Hidden Gold",
    "type": "object",
    "additionalProperties": False,
    "required": [
        "semantic_task_id",
        "scene_id",
        "intended_operation_family",
        "complexity",
        "intent_requirements",
        "target_stress_class",
        "admissible_final_outcome",
        "valid_witness_ir",
        "invalid_probe_ir",
        "generator_version",
        "oracle_version",
        "machine_audit",
        "author_review",
    ],
    "properties": {
        "semantic_task_id": {"type": "string", "minLength": 1},
        "scene_id": {"type": "string", "minLength": 1},
        "intended_operation_family": {"enum": list(OPERATION_FAMILIES)},
        "complexity": {"enum": list(COMPLEXITIES)},
        "intent_requirements": {"type": "object"},
        "target_stress_class": {"enum": list(STRESS_CLASSES)},
        "admissible_final_outcome": {"enum": ["VALID_EDIT", "DEFER"]},
        "valid_witness_ir": {"anyOf": [IR_SCHEMA, {"type": "null"}]},
        "invalid_probe_ir": {
            "anyOf": [
                {
                    "type": "object",
                    "additionalProperties": False,
                    "required": ["ir", "expected_rule_ids"],
                    "properties": {
                        "ir": IR_SCHEMA,
                        "expected_rule_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "minItems": 1,
                        },
                    },
                },
                {"type": "null"},
            ]
        },
        "generator_version": {"type": "string", "minLength": 1},
        "oracle_version": {"type": "string", "minLength": 1},
        "machine_audit": {"enum": ["PENDING", "PASS", "FAIL"]},
        "author_review": {"enum": ["PENDING", "PASS", "FAIL"]},
    },
}

RUN_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "https://miceplan-lab.local/schema/run-manifest-v1.json",
    "title": "MICEPlan-Lab Run Manifest",
    "type": "object",
    "additionalProperties": True,
    "required": [
        "run_id",
        "protocol_version",
        "dataset_version",
        "model_id",
        "provider",
        "access_date",
        "prompt_hashes",
        "schema_hash",
        "scheduled_request_ids",
        "replicate_ids",
    ],
    "properties": {
        "run_id": {"type": "string", "minLength": 1},
        "protocol_version": {"const": PROTOCOL_VERSION},
        "dataset_version": {"const": DATASET_VERSION},
        "model_id": {"type": "string", "minLength": 1},
        "provider": {"type": "string", "minLength": 1},
        "access_date": {"type": "string", "format": "date"},
        "prompt_hashes": {"type": "object"},
        "schema_hash": {"type": "string", "minLength": 1},
        "scheduled_request_ids": {"type": "array", "items": {"type": "string"}},
        "replicate_ids": {"type": "array", "items": {"type": "integer", "minimum": 1}},
    },
}


def write_schemas(directory: Path) -> dict[str, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    schemas = {
        "scene.schema.json": SCENE_SCHEMA,
        "request.schema.json": REQUEST_SCHEMA,
        "gold.schema.json": GOLD_SCHEMA,
        "run.schema.json": RUN_SCHEMA,
        "layout-edit-ir.schema.json": IR_SCHEMA,
    }
    result: dict[str, Path] = {}
    for name, schema in schemas.items():
        path = directory / name
        path.write_text(json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result[name] = path
    return result
