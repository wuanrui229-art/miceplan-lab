from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .policy_runner import ModelAdapter, ModelCall


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


class JournalIntegrityError(RuntimeError):
    pass


class AppendOnlyHashChain:
    """Small append-only JSONL store with a verifiable SHA-256 chain."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.envelopes: list[dict[str, Any]] = []
        self._load_and_verify()

    @property
    def payloads(self) -> list[dict[str, Any]]:
        return [envelope["payload"] for envelope in self.envelopes]

    def _load_and_verify(self) -> None:
        if not self.path.exists():
            return
        previous = "GENESIS"
        with self.path.open(encoding="utf-8") as handle:
            for expected_sequence, line in enumerate(handle):
                if not line.strip():
                    continue
                try:
                    envelope = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise JournalIntegrityError(f"Invalid JSON in {self.path.name}: {exc}") from exc
                core = {
                    "sequence": expected_sequence,
                    "previous_sha256": previous,
                    "payload": envelope.get("payload"),
                }
                expected_hash = sha256_json(core)
                if envelope.get("sequence") != expected_sequence:
                    raise JournalIntegrityError(f"Non-contiguous sequence in {self.path.name}")
                if envelope.get("previous_sha256") != previous:
                    raise JournalIntegrityError(f"Broken previous hash in {self.path.name}")
                if envelope.get("record_sha256") != expected_hash:
                    raise JournalIntegrityError(f"Record hash mismatch in {self.path.name}")
                self.envelopes.append(envelope)
                previous = expected_hash

    def append(self, payload: dict[str, Any]) -> dict[str, Any]:
        sequence = len(self.envelopes)
        previous = self.envelopes[-1]["record_sha256"] if self.envelopes else "GENESIS"
        core = {"sequence": sequence, "previous_sha256": previous, "payload": payload}
        envelope = {**core, "record_sha256": sha256_json(core)}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(canonical_json(envelope) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self.envelopes.append(envelope)
        return envelope


class RunJournal:
    FILES = {
        "calls": "calls.jsonl",
        "gate_events": "gate_events.jsonl",
        "outcomes": "outcomes.jsonl",
        "errors": "infrastructure_errors.jsonl",
    }

    def __init__(self, run_directory: Path, manifest: dict[str, Any]) -> None:
        self.run_directory = run_directory
        self.run_directory.mkdir(parents=True, exist_ok=True)
        self.manifest_path = run_directory / "run_manifest.json"
        manifest_text = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if self.manifest_path.exists():
            existing = json.loads(self.manifest_path.read_text(encoding="utf-8"))
            if existing != manifest:
                raise JournalIntegrityError("Existing run manifest differs from requested manifest")
        else:
            self.manifest_path.write_text(manifest_text, encoding="utf-8")
        self.manifest = manifest
        self.calls = AppendOnlyHashChain(run_directory / self.FILES["calls"])
        self.gate_events = AppendOnlyHashChain(run_directory / self.FILES["gate_events"])
        self.outcomes = AppendOnlyHashChain(run_directory / self.FILES["outcomes"])
        self.errors = AppendOnlyHashChain(run_directory / self.FILES["errors"])
        self._assert_unique(self.calls.payloads, "call_key")
        self._assert_unique(self.gate_events.payloads, "event_key")
        self._assert_unique(self.outcomes.payloads, "outcome_key")

    @staticmethod
    def _assert_unique(rows: list[dict[str, Any]], field: str) -> None:
        values = [row[field] for row in rows]
        if len(values) != len(set(values)):
            raise JournalIntegrityError(f"Duplicate {field} in append-only journal")

    def call_by_key(self, call_key: str) -> dict[str, Any] | None:
        return next((row for row in self.calls.payloads if row["call_key"] == call_key), None)

    def append_call(self, payload: dict[str, Any]) -> None:
        if self.call_by_key(payload["call_key"]) is not None:
            raise JournalIntegrityError(f"Refusing duplicate model call: {payload['call_key']}")
        self.calls.append(payload)

    def append_error(self, payload: dict[str, Any]) -> None:
        self.errors.append(payload)

    def append_gate_event(self, payload: dict[str, Any]) -> None:
        if any(row["event_key"] == payload["event_key"] for row in self.gate_events.payloads):
            return
        self.gate_events.append(payload)

    def append_outcome(self, payload: dict[str, Any]) -> None:
        if any(row["outcome_key"] == payload["outcome_key"] for row in self.outcomes.payloads):
            return
        self.outcomes.append(payload)

    def has_outcome(self, outcome_key: str) -> bool:
        return any(row["outcome_key"] == outcome_key for row in self.outcomes.payloads)

    def verify(self) -> dict[str, int]:
        for name in self.FILES:
            AppendOnlyHashChain(self.run_directory / self.FILES[name])
        return {
            "calls": len(self.calls.payloads),
            "gate_events": len(self.gate_events.payloads),
            "outcomes": len(self.outcomes.payloads),
            "infrastructure_errors": len(self.errors.payloads),
        }


def model_call_to_dict(call: ModelCall) -> dict[str, Any]:
    value = asdict(call)
    value["infrastructure_errors"] = list(call.infrastructure_errors)
    return value


def model_call_from_dict(value: dict[str, Any]) -> ModelCall:
    return ModelCall(
        call_id=value["call_id"],
        ir=value.get("ir"),
        raw_response=value.get("raw_response"),
        latency_ms=float(value.get("latency_ms", 0)),
        usage={key: int(item or 0) for key, item in value.get("usage", {}).items()},
        error=value.get("error"),
        infrastructure_attempts=int(value.get("infrastructure_attempts", 1)),
        infrastructure_errors=tuple(value.get("infrastructure_errors", [])),
    )


class JournaledAdapter:
    """Caches successful semantic calls so resume never resamples completed calls."""

    def __init__(self, delegate: ModelAdapter, journal: RunJournal, replicate_id: int) -> None:
        self.delegate = delegate
        self.journal = journal
        self.replicate_id = replicate_id

    def _call_identity(
        self,
        *,
        request: dict[str, Any],
        visible_scene: dict[str, Any],
        prompt: str,
        semantic_attempt: int,
        previous_ir: dict[str, Any] | None,
        feedback: dict[str, Any] | None,
    ) -> dict[str, Any]:
        return {
            "run_id": self.journal.manifest["run_id"],
            "request_id": request["request_id"],
            "replicate_id": self.replicate_id,
            "semantic_attempt": semantic_attempt,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            "visible_scene_sha256": sha256_json(visible_scene),
            "previous_ir_sha256": sha256_json(previous_ir),
            "feedback_sha256": sha256_json(feedback),
        }

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
        identity = self._call_identity(
            request=request,
            visible_scene=visible_scene,
            prompt=prompt,
            semantic_attempt=semantic_attempt,
            previous_ir=previous_ir,
            feedback=feedback,
        )
        call_key = sha256_json(identity)
        existing = self.journal.call_by_key(call_key)
        if existing is not None:
            return model_call_from_dict(existing["model_call"])
        try:
            call = self.delegate.generate(
                request=request,
                visible_scene=visible_scene,
                prompt=prompt,
                semantic_attempt=semantic_attempt,
                previous_ir=previous_ir,
                feedback=feedback,
            )
        except Exception as exc:
            self.journal.append_error(
                {
                    "recorded_at": utc_now(),
                    "call_key": call_key,
                    "identity": identity,
                    "error_type": type(exc).__name__,
                    "message": str(exc),
                    "infrastructure_attempts": getattr(exc, "attempts", None),
                    "attempt_errors": list(getattr(exc, "errors", ())),
                }
            )
            raise
        self.journal.append_call(
            {
                "call_key": call_key,
                "recorded_at": utc_now(),
                "identity": identity,
                "prompt": prompt,
                "request": request,
                "visible_scene": visible_scene,
                "previous_ir": previous_ir,
                "feedback": feedback,
                "model_call": model_call_to_dict(call),
            }
        )
        return call
