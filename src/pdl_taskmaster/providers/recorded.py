from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
import hashlib
import json

from pdl_taskmaster.providers.base import WorkerResult


class ReplayMissError(RuntimeError):
    pass


class AmbiguousFixtureError(RuntimeError):
    pass


RequestBuilder = Callable[[Any], dict]


def request_sha256(body: dict) -> str:
    """The replay key of one provider request (TARGET_ARCHITECTURE I-10): the SHA-256 of
    the complete body a worker would send (model, input, instructions, reasoning, caps,
    pinning and output format) in a canonical JSON form."""
    canonical = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass
class RecordedEntry:
    response: str
    metadata: dict[str, Any] = field(default_factory=dict)


class RecordedFixtureBuilder:
    """Collects recorded responses keyed by (operation, request_sha256)."""

    def __init__(self, request_builder: RequestBuilder) -> None:
        self.request_builder = request_builder
        self.entries: dict[tuple[str, str], list[RecordedEntry]] = {}
        self.order: list[tuple[str, str]] = []
        self.prompt_examples: dict[tuple[str, str], str] = {}

    def add(
        self,
        operation: str,
        request_key: str,
        response: str,
        metadata: dict[str, Any] | None = None,
        *,
        source: str = "fixture",
        prompt_text: str | None = None,
    ) -> None:
        key = (operation, request_key)
        self.entries.setdefault(key, []).append(
            RecordedEntry(response, {"source": source, **(metadata or {})})
        )
        if prompt_text is not None:
            self.prompt_examples.setdefault(key, prompt_text)
        if key not in self.order:
            self.order.append(key)

    def build(self, selected_fixture_id: str | None = None) -> "RecordedWorker":
        mapping: dict[tuple[str, str], RecordedEntry] = {}
        for key, entries in self.entries.items():
            unique = {entry.response: entry for entry in entries}
            if len(unique) == 1:
                mapping[key] = next(iter(unique.values()))
                continue
            if selected_fixture_id is None:
                raise AmbiguousFixtureError(
                    f"ambiguous replay mapping for {key[0]} prompt={key[1][:12]}; "
                    "provide an explicit fixture/run ID"
                )
            selected = [
                entry
                for entry in entries
                if entry.metadata.get("source") == selected_fixture_id
            ]
            if len(selected) != 1:
                raise AmbiguousFixtureError(
                    f"fixture ID {selected_fixture_id!r} does not resolve exactly one response "
                    f"for {key[0]} prompt={key[1][:12]}"
                )
            mapping[key] = selected[0]
        return RecordedWorker(mapping, list(self.order), dict(self.prompt_examples), dict(self.entries),
                              request_builder=self.request_builder)


class RecordedWorker:
    """Deterministic replay worker.

    This is a qualification/test implementation of WorkerAdapter, not the
    general-purpose worker contract. A call is matched on the complete provider
    request the live worker would send for it (``request_builder``), so a change to
    anything a model receives, the provider-layer instructions included, is a
    ``ReplayMissError`` (TARGET_ARCHITECTURE I-10).
    """

    def __init__(
        self,
        mapping: dict[tuple[str, str], RecordedEntry],
        order: list[tuple[str, str]] | None = None,
        prompt_examples: dict[tuple[str, str], str] | None = None,
        entries: dict[tuple[str, str], list[RecordedEntry]] | None = None,
        *,
        request_builder: RequestBuilder,
    ):
        self.request_builder = request_builder
        self.mapping = mapping
        self.order = list(order or [])
        self.prompt_examples = prompt_examples or {}
        self.entries = entries or {}

    def call(self, request: Any) -> WorkerResult:
        key = (request.operation, request_sha256(self.request_builder(request)))
        entry = self.mapping.get(key)
        if entry is None:
            raise ReplayMissError(
                f"no recorded response for operation={request.operation} request_sha256={key[1][:12]}"
            )
        return WorkerResult(entry.response, dict(entry.metadata))

    def to_manifest(self) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for key, entry in self.mapping.items():
            operation, request_key = key
            source = str(entry.metadata.get("source", "unknown"))
            fixture_id = hashlib.sha256(
                f"{source}|{operation}|{request_key}".encode("utf-8")
            ).hexdigest()[:16]
            rows.append(
                {
                    "source_evidence_run": source,
                    "operation": operation,
                    "request_sha256": request_key,
                    "raw_response_sha256": hashlib.sha256(entry.response.encode("utf-8")).hexdigest(),
                    "fixture_id": fixture_id,
                }
            )
        return rows
