from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .live_adapter import OpenAICompatibleModelAdapter
from .policy_runner import ModelCall


def normalise_openai_usage(value: Any) -> dict[str, int]:
    source = value if isinstance(value, dict) else {}
    prompt_details = source.get("prompt_tokens_details")
    details = prompt_details if isinstance(prompt_details, dict) else {}
    return {
        "prompt_tokens": int(source.get("prompt_tokens", 0) or 0),
        "completion_tokens": int(source.get("completion_tokens", 0) or 0),
        "cached_tokens": int(details.get("cached_tokens", 0) or 0),
        "cache_write_tokens": int(details.get("cache_write_tokens", 0) or 0),
        "total_tokens": int(source.get("total_tokens", 0) or 0),
    }


@dataclass
class OpenAISolAdapter(OpenAICompatibleModelAdapter):
    """OpenAI-specific refusal and usage handling layered over the frozen adapter."""

    def _parse_candidate(self, body: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
        try:
            choice = body["choices"][0]
            message = choice["message"]
        except (KeyError, IndexError, TypeError) as exc:
            return None, f"response_parse_error: {exc}"
        if message.get("refusal"):
            return None, "provider_refusal"
        if choice.get("finish_reason") == "content_filter":
            return None, "provider_content_filter"
        return super()._parse_candidate(body)

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
        call = super().generate(
            request=request,
            visible_scene=visible_scene,
            prompt=prompt,
            semantic_attempt=semantic_attempt,
            previous_ir=previous_ir,
            feedback=feedback,
        )
        usage_source = call.raw_response.get("usage") if isinstance(call.raw_response, dict) else None
        return ModelCall(
            call_id=call.call_id,
            ir=call.ir,
            raw_response=call.raw_response,
            latency_ms=call.latency_ms,
            usage=normalise_openai_usage(usage_source),
            error=call.error,
            infrastructure_attempts=call.infrastructure_attempts,
            infrastructure_errors=call.infrastructure_errors,
        )
