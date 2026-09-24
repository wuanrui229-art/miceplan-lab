from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import dataclass, field
from typing import Any

from jsonschema import Draft202012Validator

from .contracts import IR_SCHEMA
from .policy_runner import ModelCall


TRANSIENT_HTTP_CODES = {429, 500, 502, 503, 504}
DEEPSEEK_NULL_SENTINEL = "__MICEPLAN_NULL__"


class InfrastructureError(RuntimeError):
    def __init__(self, message: str, attempts: int, errors: list[str]) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.errors = tuple(errors)


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text"]
        return "".join(parts).strip()
    raise ValueError("Provider response content is not text")


def _normalise_usage(value: Any) -> dict[str, int]:
    source = value if isinstance(value, dict) else {}
    return {
        "prompt_tokens": int(source.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(source.get("completion_tokens", 0) or 0),
        "cached_tokens": int(
            source.get("cached_tokens", source.get("prompt_cache_hit_tokens", 0)) or 0
        ),
        "total_tokens": int(source.get("total_tokens", 0) or 0),
    }


def deepseek_strict_schema(value: Any) -> Any:
    """Encode the frozen IR schema in DeepSeek strict-tool's supported subset."""

    if isinstance(value, list):
        return [deepseek_strict_schema(item) for item in value]
    if not isinstance(value, dict):
        return value
    source = dict(value)
    types = source.get("type")
    if isinstance(types, list):
        variants = []
        for type_name in types:
            if type_name == "null":
                # DeepSeek strict mode does not list JSON Schema's null type as
                # supported and requires every anyOf branch to declare a type.
                # Use an unambiguous wire sentinel and decode it before local
                # validation against the unmodified frozen IR schema.
                variants.append({"type": "string", "enum": [DEEPSEEK_NULL_SENTINEL]})
                continue
            variant = {
                key: deepseek_strict_schema(item)
                for key, item in source.items()
                if key not in {"type", "enum"}
            }
            variant["type"] = type_name
            if "enum" in source:
                non_null = [item for item in source["enum"] if item is not None]
                if non_null:
                    variant["enum"] = non_null
            variants.append(variant)
        return {"anyOf": variants}
    unsupported = {"$id", "$schema", "title", "minLength", "maxLength", "minItems", "maxItems"}
    return {
        key: deepseek_strict_schema(item)
        for key, item in source.items()
        if key not in unsupported
    }


def decode_deepseek_null_sentinels(candidate: dict[str, Any]) -> dict[str, Any]:
    """Decode only nullable operation fields from the DeepSeek wire schema."""

    nullable_fields = {"count", "width", "height", "x", "y", "region", "booth_type"}
    decoded = json.loads(json.dumps(candidate, ensure_ascii=False))
    operations = decoded.get("operations")
    if isinstance(operations, list):
        for operation in operations:
            if not isinstance(operation, dict):
                continue
            for field_name in nullable_fields:
                if operation.get(field_name) == DEEPSEEK_NULL_SENTINEL:
                    operation[field_name] = None
    return decoded


@dataclass
class OpenAICompatibleModelAdapter:
    endpoint: str
    api_key: str
    model: str
    temperature: float | None = 0
    max_output_tokens: int = 2048
    max_tokens_parameter: str = "max_tokens"
    extra_request_parameters: dict[str, Any] = field(default_factory=dict)
    timeout_seconds: int = 90
    max_infrastructure_attempts: int = 3

    def _payload(
        self,
        *,
        request: dict[str, Any],
        visible_scene: dict[str, Any],
        prompt: str,
        semantic_attempt: int,
        previous_ir: dict[str, Any] | None,
        feedback: dict[str, Any] | None,
    ) -> dict[str, Any]:
        user_payload: dict[str, Any] = {
            "request_id": request["request_id"],
            "language": request["language"],
            "request": request["text"],
            "visible_scene": visible_scene,
            "semantic_attempt": semantic_attempt,
        }
        if previous_ir is not None:
            user_payload["previous_candidate"] = previous_ir
        if feedback is not None:
            user_payload["runtime_feedback"] = feedback
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True)},
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "MICEPlanLabLayoutEditIR", "strict": True, "schema": IR_SCHEMA},
            },
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        payload[self.max_tokens_parameter] = self.max_output_tokens
        payload.update(self.extra_request_parameters)
        return payload

    def generate(
        self,
        *,
        request: dict[str, Any],
        visible_scene: dict[str, Any],
        prompt: str,
        semantic_attempt: int,
        previous_ir: dict[str, Any] | None = None,
        feedback: dict[str, Any] | None = None,
    ) -> ModelCall:
        payload = self._payload(
            request=request,
            visible_scene=visible_scene,
            prompt=prompt,
            semantic_attempt=semantic_attempt,
            previous_ir=previous_ir,
            feedback=feedback,
        )
        infrastructure_errors: list[str] = []
        started = time.perf_counter_ns()
        body: dict[str, Any] | None = None
        attempts = 0
        for attempts in range(1, self.max_infrastructure_attempts + 1):
            api_request = urllib.request.Request(
                self.endpoint,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(api_request, timeout=self.timeout_seconds) as response:
                    body = json.loads(response.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as exc:
                try:
                    response_text = exc.read().decode("utf-8", errors="replace")[:2000]
                except Exception:
                    response_text = ""
                message = f"HTTP {exc.code}: {exc.reason}"
                if response_text:
                    message += f"; provider_body={response_text}"
                if exc.code not in TRANSIENT_HTTP_CODES:
                    raise InfrastructureError(message, attempts, infrastructure_errors + [message]) from exc
                infrastructure_errors.append(message)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                infrastructure_errors.append(f"{type(exc).__name__}: {exc}")
            if attempts < self.max_infrastructure_attempts:
                time.sleep(2 ** (attempts - 1))
        latency_ms = (time.perf_counter_ns() - started) / 1_000_000
        if body is None:
            raise InfrastructureError(
                "Provider call failed after bounded infrastructure retries",
                attempts,
                infrastructure_errors,
            )

        parsed, semantic_error = self._parse_candidate(body)

        return ModelCall(
            call_id=str(body.get("id") or uuid.uuid4()),
            ir=parsed,
            raw_response=body,
            latency_ms=latency_ms,
            usage=_normalise_usage(body.get("usage")),
            error=semantic_error,
            infrastructure_attempts=attempts,
            infrastructure_errors=tuple(infrastructure_errors),
        )

    def _parse_candidate(self, body: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        try:
            content = body["choices"][0]["message"]["content"]
            candidate = json.loads(_content_text(content))
            Draft202012Validator(IR_SCHEMA).validate(candidate)
            return candidate, None
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return None, f"response_parse_error: {exc}"
        except Exception as exc:
            return None, f"schema_validation_error: {exc}"


@dataclass
class DeepSeekStrictToolAdapter(OpenAICompatibleModelAdapter):
    """DeepSeek beta strict-tool adapter with local validation against the frozen schema."""

    tool_name: str = "emit_layout_edit_ir"

    def _payload(
        self,
        *,
        request: dict[str, Any],
        visible_scene: dict[str, Any],
        prompt: str,
        semantic_attempt: int,
        previous_ir: dict[str, Any] | None,
        feedback: dict[str, Any] | None,
    ) -> dict[str, Any]:
        user_payload: dict[str, Any] = {
            "request_id": request["request_id"],
            "language": request["language"],
            "request": request["text"],
            "visible_scene": visible_scene,
            "semantic_attempt": semantic_attempt,
        }
        if previous_ir is not None:
            user_payload["previous_candidate"] = previous_ir
        if feedback is not None:
            user_payload["runtime_feedback"] = feedback
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False, sort_keys=True),
                },
            ],
            "tools": [
                {
                    "type": "function",
                    "function": {
                        "name": self.tool_name,
                        "description": (
                            "Return the single LayoutEditIR candidate for the supplied MICEPlan-Lab request."
                        ),
                        "strict": True,
                        "parameters": deepseek_strict_schema(IR_SCHEMA),
                    },
                }
            ],
            "tool_choice": {"type": "function", "function": {"name": self.tool_name}},
        }
        if self.temperature is not None:
            payload["temperature"] = self.temperature
        payload[self.max_tokens_parameter] = self.max_output_tokens
        payload.update(self.extra_request_parameters)
        return payload

    def _parse_candidate(self, body: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        try:
            message = body["choices"][0]["message"]
            calls = message["tool_calls"]
            matching = [call for call in calls if call["function"]["name"] == self.tool_name]
            if len(matching) != 1:
                raise ValueError(f"expected exactly one {self.tool_name} tool call")
            candidate = decode_deepseek_null_sentinels(
                json.loads(matching[0]["function"]["arguments"])
            )
            Draft202012Validator(IR_SCHEMA).validate(candidate)
            return candidate, None
        except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
            return None, f"response_parse_error: {exc}"
        except Exception as exc:
            return None, f"schema_validation_error: {exc}"
