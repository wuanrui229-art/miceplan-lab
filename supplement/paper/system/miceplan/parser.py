from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass
from typing import Protocol

from .models import HallLayout, LayoutEditIR, LAYOUT_EDIT_IR_SCHEMA, ModelError, Operation, OperationType


PROMPT_VERSION = "layout-edit-ir-v0.3"


class Parser(Protocol):
    def parse(self, request_text: str, layout: HallLayout) -> LayoutEditIR: ...


def _request_id() -> str:
    return f"req-{uuid.uuid4().hex[:12]}"


def _language(text: str) -> str:
    return "zh" if re.search(r"[\u4e00-\u9fff]", text) else "en"


def _dimension(text: str) -> tuple[float | None, float | None]:
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:m|米)?\s*[x×*]\s*(\d+(?:\.\d+)?)\s*(?:m|米)?", text, re.I)
    return (float(match.group(1)), float(match.group(2))) if match else (None, None)


def _count(text: str) -> int | None:
    patterns = [
        r"\bsplit\b.*?\binto\s+(\d+)\s*(?:booths?)?",
        r"(?:拆分为|拆分成|分成)\D{0,8}(\d+)\s*(?:个)?",
        r"\badd\s+(\d+)\s*(?:booths?)?",
        r"(?:新增|增加)\D{0,8}(\d+)\s*(?:个)?",
        r"(\d+)\s*(?:个)?(?:标准)?展位",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return int(match.group(1))
    return None


@dataclass
class DeterministicBaselineParser:
    """Transparent bilingual baseline, not an LLM implementation."""

    standard_width: float = 3.0
    standard_height: float = 3.0

    def parse(self, request_text: str, layout: HallLayout) -> LayoutEditIR:
        normalized = request_text.strip()
        language = _language(normalized)
        number_to_id = {booth.number.upper(): booth.id for booth in layout.booths}
        referenced_numbers = tuple(dict.fromkeys(re.findall(r"\b[A-Za-z]\d{2,5}\b", normalized.upper())))
        unresolved = [number for number in referenced_numbers if number not in number_to_id]
        target_ids = tuple(number_to_id[number] for number in referenced_numbers if number in number_to_id)
        assumptions: list[str] = []
        hard_constraints = ["within_boundary", "no_overlap", "avoid_protected_polygons", "unique_identifiers"]
        if re.search(r"已售|锁定|保留|不要移动|preserve|sold|locked|do not move", normalized, re.I):
            hard_constraints.append("preserve_sold_and_locked")

        operation_type: OperationType | None = None
        if re.search(r"拆分|分割|split", normalized, re.I):
            operation_type = OperationType.SPLIT_BOOTH
        elif re.search(r"预留.*通道|新增.*通道|reserve.*aisle", normalized, re.I):
            operation_type = OperationType.RESERVE_AISLE
        elif re.search(r"新增|增加|add\b|create\b", normalized, re.I):
            operation_type = OperationType.ADD_BOOTH
        elif re.search(r"移动|移到|move\b|relocate", normalized, re.I):
            operation_type = OperationType.MOVE_BOOTH
        elif re.search(r"调整.*尺寸|缩放|resize", normalized, re.I):
            operation_type = OperationType.RESIZE_BOOTH
        elif re.search(r"删除|移除|remove\b|delete\b", normalized, re.I):
            operation_type = OperationType.REMOVE_BOOTH

        width, height = _dimension(normalized)
        count = _count(normalized)
        booth_type = "standard" if re.search(r"标准|standard", normalized, re.I) else None
        region = None
        region_terms = ((r"北侧|北部|north", "north"), (r"南侧|南部|south", "south"), (r"东侧|东部|east", "east"), (r"西侧|西部|west", "west"))
        for pattern, value in region_terms:
            if re.search(pattern, normalized, re.I):
                region = value
                break

        x = y = None
        coordinate = re.search(r"(?:\bx\s*[=:]?\s*)(-?\d+(?:\.\d+)?)\D{0,10}(?:\by\s*[=:]?\s*)(-?\d+(?:\.\d+)?)", normalized, re.I)
        if coordinate:
            x, y = float(coordinate.group(1)), float(coordinate.group(2))

        requires_confirmation = bool(unresolved) or operation_type is None
        if operation_type in {OperationType.SPLIT_BOOTH, OperationType.REMOVE_BOOTH, OperationType.RESIZE_BOOTH, OperationType.MOVE_BOOTH} and not target_ids:
            requires_confirmation = True
            unresolved.append("target_booth")
        if operation_type in {OperationType.SPLIT_BOOTH, OperationType.ADD_BOOTH} and count is None:
            requires_confirmation = True
            unresolved.append("booth_count")
        if operation_type == OperationType.RESIZE_BOOTH and (width is None or height is None):
            requires_confirmation = True
            unresolved.append("dimensions")
        if operation_type == OperationType.MOVE_BOOTH and (x is None or y is None) and region is None:
            requires_confirmation = True
            unresolved.append("target_position_or_region")
        if operation_type == OperationType.RESERVE_AISLE and (width is None or height is None or x is None or y is None):
            requires_confirmation = True
            unresolved.append("aisle_dimensions_and_position")

        if booth_type == "standard" and width is None and operation_type in {OperationType.ADD_BOOTH, OperationType.SPLIT_BOOTH}:
            width, height = self.standard_width, self.standard_height
            assumptions.append("A configurable 3 m by 3 m standard-booth size was used.")
        if operation_type == OperationType.ADD_BOOTH and (width is None or height is None):
            requires_confirmation = True
            unresolved.append("dimensions_or_standard_type")

        protected_targets = [
            booth.number for booth in layout.booths
            if booth.id in target_ids and booth.status in {"sold", "locked"}
        ]
        if protected_targets:
            requires_confirmation = True
            unresolved.extend(f"protected:{number}" for number in protected_targets)

        operations = () if operation_type is None else (
            Operation(
                type=operation_type,
                target_ids=target_ids,
                count=count,
                width=width,
                height=height,
                x=x,
                y=y,
                region=region,
                booth_type=booth_type,
            ),
        )
        return LayoutEditIR(
            request_id=_request_id(),
            source_layout_version=layout.version,
            language=language,
            operations=operations,
            hard_constraints=tuple(dict.fromkeys(hard_constraints)),
            preferences=(),
            assumptions=tuple(assumptions),
            unresolved_references=tuple(dict.fromkeys(unresolved)),
            requires_confirmation=requires_confirmation,
        )


@dataclass
class OpenAICompatibleStructuredParser:
    endpoint: str
    api_key: str
    model: str
    timeout_seconds: int = 60
    temperature: float = 0

    def _payload(self, request_text: str, layout: HallLayout) -> dict:
        booth_catalog = [
            {"id": booth.id, "number": booth.number, "status": booth.status, "type": booth.type}
            for booth in layout.booths
        ]
        instruction = (
            "Convert one bounded exhibition-layout editing request into LayoutEditIR. "
            "Use only the six schema operation types and resolve visible booth numbers to internal IDs. "
            "Use only north, south, east, or west for region, translating equivalent Chinese and English phrases. "
            "A known relative region is executable by the downstream solver and does not by itself require confirmation; "
            "leave x and y null rather than inventing coordinates. If an object number is unknown, preserve the intended "
            "operation with empty target_ids, preserve any stated region, add the visible number to unresolved_references, "
            "and require confirmation. If a sold or locked object would be changed, resolve and retain its internal ID in "
            "target_ids, preserve the intended operation, add protected:<visible number> to unresolved_references, and "
            "require confirmation. A contradictory request must "
            "produce no operations, include a concise machine-readable contradiction reason such as "
            "contradictory_booth_count, and require confirmation. The count field is the number of booths created by "
            "ADD_BOOTH or SPLIT_BOOTH; it must be null for MOVE_BOOTH, RESIZE_BOOTH, REMOVE_BOOTH, and RESERVE_AISLE. "
            "The booth_type field applies only to ADD_BOOTH and SPLIT_BOOTH and must be null for the other four operations. "
            "For ADD_BOOTH or SPLIT_BOOTH, use standard only when the request says standard; when exact dimensions are "
            "given without the word standard, use custom; otherwise use null. Missing final coordinates for "
            "ADD_BOOTH, SPLIT_BOOTH, or a region-based MOVE_BOOTH are solver responsibilities, not clarification reasons. "
            "Never declare legal compliance or geometric feasibility."
        )
        return {
            "model": self.model,
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": instruction},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "prompt_version": PROMPT_VERSION,
                            "request_id": _request_id(),
                            "source_layout_version": layout.version,
                            "hall_id": layout.hall_id,
                            "booths": booth_catalog,
                            "request": request_text,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "LayoutEditIR", "strict": True, "schema": LAYOUT_EDIT_IR_SCHEMA},
            },
        }

    def request_completion(self, request_text: str, layout: HallLayout) -> dict:
        payload = self._payload(request_text, layout)
        request = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            provider_message = exc.read().decode("utf-8", errors="replace")[:1000]
            raise ModelError(
                f"Structured model call failed with HTTP {exc.code}: {provider_message}"
            ) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise ModelError(f"Structured model call failed: {exc}") from exc
        if not isinstance(body, dict):
            raise ModelError("Model response body must be a JSON object")
        return body

    def parse_completion(self, body: dict) -> LayoutEditIR:
        try:
            content = body["choices"][0]["message"]["content"]
            parsed = json.loads(content) if isinstance(content, str) else content
        except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
            raise ModelError("Model response did not contain a valid LayoutEditIR payload") from exc
        return LayoutEditIR.from_dict(parsed)

    def parse(self, request_text: str, layout: HallLayout) -> LayoutEditIR:
        return self.parse_completion(self.request_completion(request_text, layout))


@dataclass
class OpenAICompatiblePromptOnlyParser(OpenAICompatibleStructuredParser):
    """Prompt-carried contract baseline with no provider-side response constraint."""

    def _payload(self, request_text: str, layout: HallLayout) -> dict:
        payload = super()._payload(request_text, layout)
        payload.pop("response_format", None)
        user_context = json.loads(payload["messages"][1]["content"])
        user_context["output_instruction"] = (
            "Return exactly one JSON object matching output_contract. "
            "Do not use Markdown fences or explanatory prose."
        )
        user_context["output_contract"] = LAYOUT_EDIT_IR_SCHEMA
        payload["messages"][1]["content"] = json.dumps(user_context, ensure_ascii=False)
        return payload
