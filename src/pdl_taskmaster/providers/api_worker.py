from __future__ import annotations

import difflib
import hashlib
import http.client
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections import deque
from pathlib import Path
from typing import Any

from pdl_taskmaster.providers.base import TransportError, WorkerResult
from pdl_taskmaster.providers.call_trace import AttemptTrace, CallTrace, tracking
from pdl_taskmaster.runtime.output_contracts import (
    UNION_WRAPPER,
    ContractForm,
    contract_schema,
    grammar_schema,
    grammar_view,
    is_union_wrapped,
)

_JSON_ONLY_SUFFIX = (
    "\n\nReturn only a JSON object. Do not include markdown fences, commentary, or extra text."
)


_SEMANTIC_READ_OPERATIONS = {"BOOTSTRAP_ANALYSIS", "INTERPRET_ACTIVATION"}

def _default_provider_order() -> list[str]:
    env_order = os.environ.get("OPENROUTER_PROVIDER_ORDER")
    if env_order:
        return [p.strip() for p in env_order.split(",") if p.strip()]
    # Both serve every operation with the harness's schemas (PROVIDERS.md). Groq is
    # not a default: it rejects the EXECUTE and EMIT_RESULT_IR schemas, so a default session
    # would be split across providers. Cerebras is not either: anywhere in the order it closes
    # every free-form object, which drops the positive witness for all providers.
    primary = os.environ.get("OPENROUTER_PROVIDER", "Baseten")
    fallbacks = ["Crusoe"]
    order = [primary]
    for fb in fallbacks:
        if fb.lower() != primary.lower():
            order.append(fb)
    return order


# Provider names OpenRouter routes openai/gpt-oss-120b to (its routing funnel in
# probe 20261001-142720) and the ones this repo names. A configured name outside
# the list gets a warning, never a refusal: OpenRouter adds providers.
KNOWN_PROVIDERS: tuple[str, ...] = (
    "Cerebras", "Groq", "SambaNova", "Crusoe", "Baseten", "DeepInfra", "Fireworks", "Together", "Novita",
    "Parasail", "Nebius", "Amazon Bedrock", "Google Vertex", "CoreWeave", "DigitalOcean", "Phala",
    "SiliconFlow", "Mancer", "AkashML", "DekaLLM", "Mara",
)


def _provider_key(name: str) -> str:
    """A provider name compared without case, spaces or punctuation
    ("amazon-bedrock" is "Amazon Bedrock")."""
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def unknown_provider_names(names: list[str]) -> dict[str, str | None]:
    """Each configured name that is not a known provider, with the closest known
    name (or None)."""
    known = {_provider_key(k): k for k in KNOWN_PROVIDERS}
    unknown: dict[str, str | None] = {}
    for name in names:
        key = _provider_key(name)
        if key and key not in known:
            close = difflib.get_close_matches(key, list(known), n=1, cutoff=0.75)
            unknown[name] = known[close[0]] if close else None
    return unknown


def unknown_provider_warnings(names: list[str]) -> list[str]:
    """One warning line per configured provider name that is not a known one."""
    return [
        f"provider '{name}' is not a known OpenRouter provider name"
        + (f" (did you mean {suggestion}?)" if suggestion else "")
        + "; it is used as given, and a misspelled name makes every call fail with 'No endpoints found'"
        for name, suggestion in unknown_provider_names(names).items()
    ]


DEFAULT_PROVIDER_PINNING: dict[str, Any] = {
    "order": _default_provider_order(),
    "allow_fallbacks": True,
}

DEFAULT_SAFETY_SETTINGS: list[dict[str, str]] = [
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
]


def _unwrap_union_reply(text: str) -> str:
    """The reply to a wrapped union schema, without the wrapper (see above)."""
    try:
        value = json.loads(text)
    except ValueError:
        return text
    if isinstance(value, dict) and set(value) == {UNION_WRAPPER} and isinstance(value[UNION_WRAPPER], dict):
        return json.dumps(value[UNION_WRAPPER], ensure_ascii=False)
    return text


# Providers whose schema check requires every object to be closed. Cerebras: "'additionalProperties'
# is required to be supplied and set to false" (runs 135851/135951). Groq's strict check, over the
# same 56 requests, rejected only incomplete `required` lists, never the free-form witness data nor
# additionalProperties true; and Groq validates each generation against the schema, so leaving the
# free-form object out made every reply carrying a positive witness fail there (session 024627).
_CLOSED_OBJECT_PROVIDERS = frozenset({"cerebras"})


# Providers whose strict structured-output mode needs every property required (optional
# ones nullable): Groq's strict check rejected incomplete required lists; Cerebras.
_STRICT_ALL_REQUIRED_PROVIDERS = frozenset({"groq", "cerebras"})

# Operations whose schema a provider rejects at request time (Groq: the witness union
# nested in these schemas, "anyOf object variant error"; PROVIDERS.md §3). The provider
# still serves them, in JSON mode: it is adapted to, never excluded (ADR-0028 rule 5);
# the host validates the reply against the Pydantic contract either way.
_SCHEMA_REJECTED_OPERATIONS: dict[str, frozenset[str]] = {
    "groq": frozenset({"EXECUTE", "EMIT_RESULT_IR"}),
}

# Operations sent in JSON mode (no schema) whatever the provider: under the EXECUTE
# schema Nemotron stalled in whitespace before closing result_ir (IMPL-0001); without
# it the same request completed 14/14. Moves to the per-stage profile (IMPL-0003).
JSON_MODE_OPERATIONS = frozenset({"EXECUTE", "EXECUTE_UNCONFIRMED"})


def _order_keys(pinning: Any) -> set[str]:
    order = pinning.get("order") if isinstance(pinning, dict) else None
    return {_provider_key(name) for name in order or []}


def _accepts_free_form_objects(pinning: Any) -> bool:
    """Whether the request may carry a free-form object: no provider in its
    order requires closed objects."""
    order = pinning.get("order") if isinstance(pinning, dict) else None
    return not any(str(name).strip().lower() in _CLOSED_OBJECT_PROVIDERS for name in order or [])


def _removed_by_parameter_filter(message: str) -> set[str]:
    """Provider keys OpenRouter's routing summary lists under "Filter by Parameters
    removed ...": endpoints that exist but do not support a parameter of the request."""
    marker = "filter by parameters removed "
    lowered = message.lower()
    start = lowered.find(marker)
    if start < 0:
        return set()
    listed = lowered[start + len(marker):].split(";", 1)[0].split(". ", 1)[0]
    return {_provider_key(tag.split("/", 1)[0]) for tag in listed.split(",") if tag.strip()}


class ProviderError(TransportError):
    """A model call the provider did not complete, with what the host needs to
    report it precisely: category, HTTP status, operation, and each provider's own
    error (OpenRouter lists the providers it tried in metadata.previous_errors)."""

    def __init__(self, category: str, message: str, *, status: int | None = None,
                 attempts: list[dict[str, str]] | None = None, operation: str | None = None,
                 wire_equivalent: bool = False):
        super().__init__(message)
        self.category = category
        # True when the failure is the model's output not matching the schema: the
        # engine treats it like a reply that did not parse (WireError).
        self.wire_equivalent = wire_equivalent
        self.status = status
        self.attempts = attempts or []
        self.operation = operation
        # The generation a provider rejected against the schema, when it returns
        # it (Groq: failed_generation): what the model wrote, for diagnosis only.
        self.failed_generation: str | None = None

    @classmethod
    def from_http(cls, status: int, body: str) -> "ProviderError":
        attempts: list[dict[str, str]] = []
        try:
            parsed_body = json.loads(body)
            error = parsed_body.get("error") or {}
        except (ValueError, AttributeError):
            parsed_body, error = None, {}
        metadata = error.get("metadata") or {} if isinstance(error, dict) else {}

        def provider_message(raw: Any) -> str:
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
            except ValueError:
                return str(raw)[:600]
            if isinstance(parsed, dict):
                inner = parsed.get("error", parsed)
                return str(inner.get("message", inner) if isinstance(inner, dict) else inner)[:600]
            return str(parsed)[:600]

        for previous in metadata.get("previous_errors") or []:
            attempts.append({"provider": str(previous.get("provider_name")), "message": provider_message(previous.get("raw"))})
        if metadata.get("provider_name"):
            attempts.append({"provider": str(metadata["provider_name"]), "message": provider_message(metadata.get("raw"))})
        category = "PROVIDER_REJECTED_REQUEST" if 400 <= status < 500 and status != 429 else "PROVIDER_UNAVAILABLE"
        summary = "; ".join(f"{a['provider']}: {a['message']}" for a in attempts) or body[:600]
        error = cls(category, f"HTTP {status}: {summary}", status=status, attempts=attempts)
        error.failed_generation = _failed_generation(parsed_body)
        return error

    def as_record(self) -> dict[str, Any]:
        record = {"category": self.category, "operation": self.operation, "status": self.status,
                  "attempts": self.attempts, "message": str(self)[:2000]}
        if self.failed_generation:
            record["failed_generation"] = self.failed_generation[:_FAILED_GENERATION_CHARS]
        return record


_FAILED_GENERATION_CHARS = 4000


def _failed_generation(payload: Any, depth: int = 0) -> str | None:
    """The rejected generation a provider attached to its error, wherever the
    response carries it: error.failed_generation, error.metadata, or inside the
    provider's raw error (a JSON string OpenRouter forwards in metadata.raw)."""
    if depth > 8:
        return None
    if isinstance(payload, str):
        if "failed_generation" not in payload:
            return None
        try:
            return _failed_generation(json.loads(payload), depth + 1)
        except ValueError:
            return None
    if isinstance(payload, dict):
        value = payload.get("failed_generation")
        if isinstance(value, str) and value.strip():
            return value
        if value is not None and not isinstance(value, str):
            return json.dumps(value, ensure_ascii=False)
        children: Any = payload.values()
    elif isinstance(payload, list):
        children = payload
    else:
        return None
    for child in children:
        found = _failed_generation(child, depth + 1)
        if found:
            return found
    return None


def _rejecting_provider(error: BaseException, order: list[str]) -> str | None:
    """The configured provider that rejected a generation: OpenRouter names it in
    its error ("Upstream error from <provider>: ..."); otherwise the first one
    tried. Transport metadata only, never task content."""
    marker = "Upstream error from "
    text = str(error)
    if marker in text:
        named = text.split(marker, 1)[1].split(":", 1)[0].strip().lower()
        for provider in order:
            if provider.lower() == named:
                return provider
    return order[0] if order else None


# A reply cut off at the output cap that ends in at least this many whitespace
# characters stalled in the schema's whitespace rather than writing too much: under
# a JSON-schema decoding constraint Nemotron wrote its whole answer and then emitted
# "\n   " for 3K-29K characters before the closing braces (session-20261003-141956;
# 5 of 6 constrained EXECUTE replays). No deliverable ends in a run this long.
STALL_WHITESPACE_CHARS = 1000
# Where each call's exact request bodies are kept, beside call-trace.jsonl (I-9).
REQUEST_DIR = "provider-requests"


class OutputLimitError(ProviderError):
    """The response reached the output-token cap before it finished: in EXECUTE a
    failed attempt to penalise; at any other operation a reported harness error.

    ``partial_text`` is what arrived, for diagnosis only (never parsed or sent back
    to the model). ``whitespace_stall`` is true when the reply ended in a whitespace
    run of at least STALL_WHITESPACE_CHARS under a schema constraint."""

    def __init__(self, limit: int | None, *, partial_text: str | None = None, whitespace_stall: bool = False):
        detail = "; the reply stalled in whitespace under the output schema" if whitespace_stall else ""
        super().__init__("OUTPUT_LIMIT_REACHED",
                         f"response reached the {limit} output-token limit before it finished{detail}")
        self.output_limit = limit
        self.partial_text = partial_text
        self.whitespace_stall = whitespace_stall


def _read_body(resp: Any, trace: AttemptTrace) -> bytes:
    """The response body, in chunks so a partly received response is visible in the trace."""
    read_chunk = getattr(resp, "read1", None)
    if read_chunk is None:  # a response object without chunked reads
        data = resp.read()
        if data:
            trace.mark("response_started")
        trace.response_bytes = len(data or b"")
        return data
    chunks: list[bytes] = []
    while True:
        chunk = read_chunk(65536)
        if not chunk:
            return b"".join(chunks)
        if not chunks:
            trace.mark("response_started")
        chunks.append(chunk)
        trace.response_bytes += len(chunk)


def _sleep_within(delay: float, deadline: float) -> None:
    """Back off, but never past the call's deadline."""
    time.sleep(max(0.0, min(delay, deadline - time.monotonic())))


class ApiWorker:
    """LIVE SEMANTIC WORKER backed by a direct Responses-API HTTP call.

    This is an API-backed alternative to CodexWorker that talks straight to an
    OpenAI-compatible `/responses` endpoint (e.g. OpenRouter) instead of
    shelling out to `codex exec`. It sends exactly the same request.prompt
    every other worker receives -- no tool definitions, no sandbox, no
    agentic system prompt -- so the paid overhead is the actual projection
    content, not a coding-agent's scaffold.
    """

    @staticmethod
    def _normalize_model_name(name: str) -> str:
        s = name.strip()
        if s.lower() in {"gpt-oss-120b", "openai/gpt-oss-120b"}:
            return "openai/gpt-oss-120b"
        return s

    def __init__(
        self,
        *,
        model: str = "nvidia/nemotron-3-super-120b-a12b:free",
        repo_root: str | Path,
        base_url: str = "https://openrouter.ai/api/v1",
        api_key_env: str = "OPENROUTER_API_KEY",
        api_key_command: list[str] | None = None,
        timeout: float = 600.0,
        max_call_seconds: float = 300.0,
        max_output_tokens: int | None = 16384,
        max_repairs: int | None = None,
        draft_execute: bool = False,
        tier_d1: bool = True,
        capture_tokens: bool = True,
        reasoning_effort: str | None = None,
        reasoning_by_operation: dict[str, str] | None = None,
        model_by_operation: dict[str, str] | None = None,
        reorder_keys_for_cache: bool = False,
        structured_output: bool = True,
        provider_pinning: dict[str, Any] | None = None,
        safety_settings: list[dict[str, str]] | None = None,
        max_tokens: int = 4096,
        on_progress: Any = None,
        progress_path: str | Path | None = None,
    ):
        self.model = self._normalize_model_name(model)
        self.max_tokens = int(max_tokens)
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.timeout = timeout  # per socket operation (connect, each read)
        self.max_call_seconds = max_call_seconds  # wall-clock for one call, retries included
        # Output cap per response, reasoning included. The Responses API reads
        # max_output_tokens; the max_tokens field sent before was ignored (high
        # EXECUTE calls returned 22K-35K tokens against max_tokens=4096).
        self.max_output_tokens = int(max_output_tokens) if max_output_tokens else None
        self.max_repairs = max_repairs  # run setting read by the host (0 = stop at the first failure)
        self.draft_execute = draft_execute  # run setting read by the host (A/B option)
        self.tier_d1 = bool(tier_d1 and os.environ.get("PDLT_TIER_D1", "1") == "1")  # run setting read by the host (Tier D1 advantage mechanism)
        self.capture_tokens = capture_tokens
        # An explicit effort applies to every operation (per-operation flags still
        # win); the per-model mapping is the default only when none is given.
        # Otherwise "--reasoning high" never reached EXECUTE (runs 2026-09-30).
        from pdl_taskmaster.runtime.model_classification import resolve_reasoning
        self.reasoning_effort, self.reasoning_by_operation = resolve_reasoning(
            self.model, reasoning_effort, reasoning_by_operation
        )
        self.model_by_operation = dict(model_by_operation or {})
        self.reorder_keys_for_cache = reorder_keys_for_cache
        self.structured_output = structured_output
        self.provider_pinning = provider_pinning if provider_pinning is not None else dict(DEFAULT_PROVIDER_PINNING)
        self.safety_settings = safety_settings if safety_settings is not None else list(DEFAULT_SAFETY_SETTINGS)
        self.on_progress = on_progress
        self.progress_path = Path(progress_path) if progress_path else None
        # Call lifecycle (providers/call_trace.py): the call in flight, the recent ones,
        # and the session file every finished or interrupted call is appended to.
        self.current_call: CallTrace | None = None
        self.call_traces: deque[CallTrace] = deque(maxlen=64)
        self.trace_path: Path | None = None
        self._calls_per_operation: dict[str, int] = {}
        self._requests_stored = 0  # provider-requests/ files written this session
        # Operations whose reply stalled in whitespace under the output schema: sent
        # without the decoding constraint for the rest of the session (the host still
        # validates every reply against the schema).
        self.unconstrained_operations: set[str] = set()
        self.worker_profile = "api"
        self._default_key_lookup = api_key_command is None
        self.api_key_command = api_key_command or self._default_api_key_command(api_key_env)
        bootstrap_path = Path(__file__).resolve().parents[1] / "runtime" / "worker-bootstrap.txt"
        if not bootstrap_path.is_file():
            bootstrap_path = Path(repo_root) / "src" / "pdl_taskmaster" / "runtime" / "worker-bootstrap.txt"
        if not bootstrap_path.is_file():
            bootstrap_path = Path(repo_root) / "scripts" / "runtime" / "worker-bootstrap.txt"
        self.repo_root = Path(repo_root)
        self._bootstrap = bootstrap_path.read_text(encoding="utf-8")
        self._bootstrap_prefix = self._bootstrap.rstrip() + "\n\n"
        from pdl_taskmaster.providers.sys1.client import Sys1Client
        self.sys1_client = Sys1Client(api_key=self._resolve_api_key_safe())
        self.sys1_client.tracer = self  # System 1 calls share this worker's call lifecycle record

    def _resolve_api_key_safe(self) -> str:
        try:
            return self._resolve_api_key()
        except Exception:
            return (os.environ.get("SYS1_API_KEY") or os.environ.get(self.api_key_env) or "").strip()

    @staticmethod
    def _default_api_key_command(env_name: str) -> list[str] | None:
        if os.environ.get(env_name):
            return None
        if sys.platform != "win32":
            return None
        # On Windows, fall back to reading Machine then User scope via PowerShell
        # to pick up variables defined outside the current process environment.
        script = (
            f"$v=[Environment]::GetEnvironmentVariable('{env_name}','Machine'); "
            f"if ([string]::IsNullOrWhiteSpace($v)) {{ $v=[Environment]::GetEnvironmentVariable('{env_name}','User') }}; "
            f"if ([string]::IsNullOrWhiteSpace($v)) {{ Write-Error '{env_name} not found in Machine or User environment'; exit 1 }}; "
            "[Console]::Out.Write($v)"
        )
        return ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script]

    def _resolve_api_key(self) -> str:
        if self.api_key_command is None:
            key = (os.environ.get(self.api_key_env) or "").strip()
            if not key:
                raise TransportError(f"could not resolve {self.api_key_env}: variable is unset or empty")
            return key
        try:
            proc = subprocess.run(
                self.api_key_command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=15,
            )
        except Exception as exc:
            raise TransportError(f"could not run api_key_command: {exc}") from exc
        key = (proc.stdout or "").strip()
        if proc.returncode != 0 or not key:
            if getattr(self, "_default_key_lookup", False):
                # The built-in Windows lookup's stderr echoes its whole script: name the variable instead.
                raise TransportError(
                    f"could not resolve {self.api_key_env}: it is not set in this process or in the "
                    f"Machine or User environment; set {self.api_key_env} and restart the terminal"
                )
            detail = (proc.stderr or "").strip() or "empty key"
            raise TransportError(f"could not resolve {self.api_key_env}: {detail}")
        return key

    def _reasoning_for(self, operation: str | None) -> str | int | None:
        """Per-operation effort wins over the global default; 'none' disables reasoning."""
        if operation is not None and operation in self.reasoning_by_operation:
            return self.reasoning_by_operation[operation]
        return self.reasoning_effort

    def _model_for(self, operation: str | None) -> str:
        """Per-operation model wins over the global default."""
        if operation is not None and operation in self.model_by_operation:
            return self._normalize_model_name(self.model_by_operation[operation])
        return self.model

    def contract_form(self, operation: str | None) -> ContractForm:
        """How this worker constrains an operation's output (ADR-0028 rules 1 and 5):
        the grammar mode and the schema form, from the configured providers. The
        host shows the model its output schema in this same form."""
        keys = _order_keys(self.provider_pinning)
        if (not self.structured_output or operation is None or operation in _SEMANTIC_READ_OPERATIONS
                or operation in self.unconstrained_operations or contract_schema(operation) is None):
            grammar = "none"
        elif operation in JSON_MODE_OPERATIONS or any(
                operation in _SCHEMA_REJECTED_OPERATIONS.get(key, frozenset()) for key in keys):
            grammar = "json"
        else:
            grammar = "schema"
        return ContractForm(grammar=grammar,
                            strict_all_required=bool(keys & _STRICT_ALL_REQUIRED_PROVIDERS),
                            free_form_objects=_accepts_free_form_objects(self.provider_pinning))

    def _split_prompt(self, prompt: str) -> tuple[str, str]:
        """Split a rendered request.prompt back into (instructions, input).

        request.prompt is always bootstrap.rstrip() + "\\n\\n" + <document>.
        If the current bootstrap text doesn't match (e.g. it changed since
        this worker was constructed), fall back to sending the whole prompt
        as input with no separate instructions -- still correct, just
        without the system/user split.
        """
        if prompt.startswith(self._bootstrap_prefix):
            return self._bootstrap.rstrip(), prompt[len(self._bootstrap_prefix):]
        return "", prompt

    @staticmethod
    def _reorder_for_cache(document_json: str) -> str:
        """Reorder the projection document for provider prefix caching.

        Stable/shared content first (output_schema, clause list), volatile
        content last (bound values, operation id). Parsed content is identical;
        only key order changes. Same-shape operations (e.g. the two REVIEW
        calls) then hold a byte-identical prompt prefix, which is what
        provider prefix caches key on. No-op on non-JSON input.
        """
        try:
            doc = json.loads(document_json)
        except json.JSONDecodeError:
            return document_json
        if not isinstance(doc, dict) or not isinstance(doc.get("operation_inputs"), dict):
            return document_json
        inputs = doc["operation_inputs"]
        ordered: dict[str, Any] = {}
        for key in ("output_schema", "artifact_kind", "output_kind"):
            if key in doc:
                ordered[key] = doc[key]
        new_inputs: dict[str, Any] = {}
        for key in ("APPLICABLE_STANDARD_CLAUSES", "HIGHER_PRIORITY_CONSTRAINTS"):
            if key in inputs:
                new_inputs[key] = inputs[key]
        for key, value in inputs.items():
            if key not in new_inputs:
                new_inputs[key] = value
        ordered["operation_inputs"] = new_inputs
        for key, value in doc.items():
            if key not in ordered and key != "operation":
                ordered[key] = value
        ordered["operation"] = doc["operation"]
        return json.dumps(ordered, ensure_ascii=False, separators=(",", ":"))

    def _send_json_with_retries(self, req: urllib.request.Request, deadline: float | None = None) -> dict[str, Any]:
        """POST with exponential-backoff retries; returns the parsed response.

        Retries transient transport conditions: 429/5xx, URLError, timeouts.
        Non-retryable HTTP errors (4xx besides 429) raise immediately.
        """
        raw = None
        # A hard deadline for the whole call: the socket timeout alone bounds each
        # read, so five retried read timeouts could hold one call ~50 minutes.
        if deadline is None:
            deadline = time.monotonic() + self.max_call_seconds
        read_timeouts = 0
        for attempt in range(5):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise ProviderError("PROVIDER_UNAVAILABLE", f"call exceeded its {self.max_call_seconds:.0f}s deadline")
            trace = self._attempt(req)
            try:
                with tracking(trace):
                    with urllib.request.urlopen(req, timeout=min(self.timeout, remaining)) as resp:
                        # Status line and headers received: the API has the request.
                        trace.mark("acknowledged")
                        trace.status = getattr(resp, "status", None)
                        raw = _read_body(resp, trace).decode("utf-8", errors="replace")
                trace.mark("response_complete")
                trace.outcome = "completed"
                try:
                    parsed = json.loads(raw)
                    err = parsed.get("error") if isinstance(parsed, dict) else None
                    if err:
                        message = str(err.get("message") if isinstance(err, dict) else err)
                        if "does not match the expected schema" in message.lower() or "failed_generation" in message:
                            # The model's generation failed the provider's schema check: a
                            # model-output failure. Retrying blind repeated it 5 times at
                            # Groq (probe 20261001-142720); the engine decides instead.
                            mismatch = ProviderError("OUTPUT_MALFORMED",
                                                     f"generation did not match the schema: {message[:800]}",
                                                     wire_equivalent=True)
                            mismatch.response_body = parsed  # for the provider probe's raw record
                            mismatch.failed_generation = (_failed_generation(parsed)
                                                          or self._extract_output_text(parsed) or None)
                            self._report_failed_generation(mismatch)
                            raise mismatch
                    if err and attempt < 4:
                        err_code = str(err.get("code") if isinstance(err, dict) else err).lower()
                        err_msg = str(err.get("message") if isinstance(err, dict) else "").lower()
                        if "server" in err_code or "rate" in err_code or "internal" in err_code or "timeout" in err_code or "failed to validate json" in err_msg:
                            delay = 0.5 * (2 ** attempt)
                            self._progress(
                                f"upstream error ({err.get('code', 'error')}); retrying in {delay:.1f}s (attempt {attempt + 1}/5)..."
                            )
                            _sleep_within(delay, deadline)
                            continue
                    return parsed
                except json.JSONDecodeError:
                    trace.outcome = "unreadable"
                    break
            except KeyboardInterrupt:
                trace.outcome, trace.interrupted_by = "interrupted", "local"
                raise
            except urllib.error.HTTPError as exc:
                trace.mark("acknowledged")
                trace.status, trace.outcome = exc.code, "http_error"
                if (exc.code == 429 or 500 <= exc.code < 600) and attempt < 4:
                    delay = 0.5 * (2 ** attempt)
                    if exc.headers:
                        ra = exc.headers.get("Retry-After")
                        if ra:
                            try:
                                val = float(ra)
                                if 0.0 < val <= 10.0:
                                    delay = val
                            except (ValueError, TypeError):
                                pass
                    self._progress(
                        f"HTTP {exc.code} received; retrying in {delay:.1f}s (attempt {attempt + 1}/5)..."
                    )
                    _sleep_within(delay, deadline)
                    continue
                detail = exc.read().decode("utf-8", errors="replace")[:16000]
                rejected = ProviderError.from_http(exc.code, detail)
                self._report_failed_generation(rejected)
                raise rejected from exc
            except urllib.error.URLError as exc:
                trace.outcome, trace.error = "transport_error", str(exc.reason)
                if attempt < 4:
                    delay = 0.5 * (2 ** attempt)
                    self._progress(
                        f"transport error: {exc.reason}; retrying in {delay:.1f}s (attempt {attempt + 1}/5)..."
                    )
                    _sleep_within(delay, deadline)
                    continue
                raise ProviderError("PROVIDER_UNAVAILABLE", f"transport error: {exc.reason}") from exc
            except (
                TimeoutError,
                socket.timeout,
                ConnectionResetError,
                http.client.IncompleteRead,
                http.client.RemoteDisconnected,
                http.client.HTTPException,
            ) as exc:
                timed_out = isinstance(exc, (TimeoutError, socket.timeout))
                trace.outcome = "timeout" if timed_out else "transport_error"
                trace.interrupted_by = None if timed_out else "remote"  # the server or network ended it
                trace.error = f"{type(exc).__name__}: {exc}"
                if isinstance(exc, (TimeoutError, socket.timeout)):
                    # A response that took the whole read timeout will likely take it
                    # again: retry a read timeout once, then give up.
                    read_timeouts += 1
                    if read_timeouts > 1:
                        raise ProviderError("PROVIDER_UNAVAILABLE", f"read timed out twice ({exc})") from exc
                if attempt < 4 and deadline - time.monotonic() > 0:
                    delay = 0.5 * (2 ** attempt)
                    self._progress(
                        f"connection error ({type(exc).__name__}: {exc}); retrying in {delay:.1f}s (attempt {attempt + 1}/5)..."
                    )
                    _sleep_within(delay, deadline)
                    continue
                raise ProviderError("PROVIDER_UNAVAILABLE", f"connection failed after retries: {exc}") from exc
        if raw is None:
            raise ProviderError("PROVIDER_UNAVAILABLE", "failed after retries")
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ProviderError("PROVIDER_RESPONSE_UNREADABLE", f"non-JSON response: {raw[:500]}") from exc

    def call(self, request: Any) -> WorkerResult:
        trace = self.begin_call(str(getattr(request, "operation", None) or "UNKNOWN"))
        try:
            result = self._call(request)
            trace.final = "completed"
            return result
        except KeyboardInterrupt:
            trace.final = "interrupted"
            raise
        except ProviderError as exc:
            trace.final = "failed"
            trace.error = exc.category
            exc.operation = exc.operation or getattr(request, "operation", None)
            unrouted = self._no_endpoint_error(exc, getattr(request, "operation", None))
            if unrouted is not None:
                raise unrouted from exc
            raise
        except BaseException:
            trace.final = "failed"
            raise
        finally:
            self.end_call(trace)

    def begin_call(self, operation: str) -> CallTrace:
        number = self._calls_per_operation.get(operation, 0) + 1
        self._calls_per_operation[operation] = number
        trace = CallTrace(operation, number=number)
        self.current_call = trace
        self.call_traces.append(trace)
        return trace

    def end_call(self, trace: CallTrace) -> None:
        """Persist the call's lifecycle (also when it was interrupted)."""
        if self.current_call is trace:
            self.current_call = None
        if self.trace_path is None:
            return
        try:
            self.trace_path.parent.mkdir(parents=True, exist_ok=True)
            record = {"at": time.strftime("%Y-%m-%dT%H:%M:%S"), **trace.to_dict()}
            self._store_request_bodies(trace, record)
            with self.trace_path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def _store_request_bodies(self, trace: CallTrace, record: dict[str, Any]) -> None:
        """Keep the exact bytes each attempt sent (TARGET_ARCHITECTURE I-9): model, input,
        instructions, reasoning, caps, pinning and output format, System 1 requests
        included. Credentials travel in headers and are never part of a body. The trace
        record names each file and its SHA-256."""
        directory = self.trace_path.parent / REQUEST_DIR
        for attempt, row in zip(trace.attempts, record["attempts"]):
            if not attempt.body:
                continue
            self._requests_stored += 1
            operation = "".join(c if c.isalnum() or c in "-_" else "-" for c in trace.operation)
            name = f"{self._requests_stored:04d}-{operation}-{trace.number}-a{attempt.attempt}.json"
            directory.mkdir(parents=True, exist_ok=True)
            (directory / name).write_bytes(bytes(attempt.body))
            row["request_file"] = f"{REQUEST_DIR}/{name}"
            row["request_sha256"] = hashlib.sha256(bytes(attempt.body)).hexdigest()

    def _attempt(self, req: urllib.request.Request) -> AttemptTrace:
        """The HTTP attempt this request makes, on the call in flight (or its own)."""
        trace = self.current_call or self.begin_call("UNTRACKED")
        data = req.data if isinstance(req.data, (bytes, bytearray)) else None
        return trace.new_attempt(data)

    def _no_endpoint_error(self, exc: ProviderError, operation: str | None) -> ProviderError | None:
        """OpenRouter's 404 "No endpoints found" while providers are configured,
        as one clear line naming them (a misspelled --api-providers name gave an
        opaque routing-funnel dump). OpenRouter's own text stays in the attempts."""
        order = [str(p) for p in (self.provider_pinning or {}).get("order") or []]
        if exc.status != 404 or not order or "no endpoints found" not in str(exc).lower():
            return None
        hints = "".join(f" ({name}: did you mean {suggestion}?)" if suggestion else f" ({name}: not a known name)"
                        for name, suggestion in unknown_provider_names(order).items())
        filtered = _removed_by_parameter_filter(str(exc))
        unsupported = [name for name in order if _provider_key(name) in filtered]
        parameters = (f"{', '.join(unsupported)} {'does' if len(unsupported) == 1 else 'do'} not support a parameter "
                      f"this request uses, such as structured output: choose a provider that supports it, or run "
                      f"with --no-structured-output") if unsupported else ""
        prefix = (f"OpenRouter found no endpoint for {self._model_for(operation)} at the configured providers "
                  f"({', '.join(order)}): ")
        if unsupported and len(unsupported) == len(order):
            message = prefix + parameters
        else:
            message = prefix + f"check the spelling of each name{hints} and that it serves this model"
            if unsupported:
                message += f"; {parameters}"
        error = ProviderError(exc.category, message, status=exc.status, operation=exc.operation,
                              attempts=[*exc.attempts, {"provider": "OpenRouter", "message": str(exc)[:600]}])
        error.failed_generation = exc.failed_generation
        return error

    def build_request_body(self, request: Any) -> tuple[dict[str, Any], bool, Any]:
        """The complete request this worker sends for ``request``: model, input,
        instructions (the operation guidance), reasoning, caps, provider pinning and
        output format (TARGET_ARCHITECTURE I-9, I-10). Pure: no network, no credentials;
        the same function builds what is sent, what is recorded and what replay keys on.
        Returns the body, whether the schema was union-wrapped, and the effort sent."""
        operation_name = getattr(request, "operation", None)
        instructions, input_text = self._split_prompt(request.prompt)
        if self.reorder_keys_for_cache:
            input_text = self._reorder_for_cache(input_text.lstrip())
        if operation_name != "BYPASS_ORDINARY":
            # A direct reply is plain text: the suffix made it answer in JSON
            # ({"message": "Hello! ..."} printed raw in the REPL).
            input_text = input_text.rstrip() + _JSON_ONLY_SUFFIX

        body: dict[str, Any] = {
            "model": self._model_for(getattr(request, "operation", None)),
            "input": input_text,
        }
        # ADR-0009 finding: schema enforcement on the semantic-read boundary
        # (BOOTSTRAP_ANALYSIS) degrades interpretation quality — a lazy
        # structured summary classifies substantive tasks as instruction-free,
        # losing the entire task upstream of every gate. Structured output is
        # for ops whose SHAPE is the contract (drafts, executions, reviews);
        # the semantic read must stay free-text.
        form = self.contract_form(operation_name)

        extra_guidance = ""
        if operation_name == "BYPASS_ORDINARY" and getattr(request, "environment", None):
            # Capabilities only, from the session sandbox (never task guidance): a
            # direct reply claimed "I cannot execute code" in a session that runs it.
            extra_guidance = "Execution environment of this session (host fact): " + request.environment
        elif operation_name in ("DRAFT_PROMPT", "REVISE_PROMPT"):
            extra_guidance = (
                "\n\nNORMATIVE GUIDELINES AND SPECIFICATION FOR PROMPT PSEUDOCODE (PDL-01 to PDL-09, PROMPT-01 to PROMPT-05):\n"
                "PDL-01 — Structured English: Pseudocode MUST use readable structured English compatible with the project PDL profile.\n"
                "PDL-02 — Operation layout: Each operation SHOULD appear on its own line; equally indented operations are read top to bottom; subordinate operations are indented beneath the operation that controls or qualifies them.\n"
                "PDL-03 — Domain terminology: Pseudocode MUST use task-domain terminology rather than invent a separate task schema.\n"
                "PDL-04 — Action/control casing: Common action verbs and control keywords MAY be uppercased when helpful for readability.\n"
                "PDL-05 — No invented field schema: Pseudocode MUST NOT invent a fielded protocol schema.\n"
                "PDL-06 — Prefer ordinary structured English: Pseudocode MUST NOT imitate programming syntax when ordinary structured English is clearer.\n"
                "PDL-07 — Standard control forms: Standard-compatible IF/ELSE/ENDIF, WHILE/ENDWHILE, REPEAT/UNTIL, FOR/ENDFOR, and CASE/ENDCASE forms MAY be used when useful.\n"
                "PDL-08 — Purpose-complete notation: Prompt and Response Plan Pseudocode MUST be complete for their protocol purpose without artificial expansion into implementation algorithms.\n"
                "PDL-09 — Imperative construction and ingestion boundary: Prompt and Response Plan Pseudocode MUST NOT use data-reading verbs (READ, PARSE, ANALYZE, EXAMINE) with the user prompt, request, or task specification as the object. When the request asks to implement, create, or write software, pseudocode MUST retain active construction verbs (IMPLEMENT, CONSTRUCT, DEFINE) and target language directives. READ MUST be reserved strictly for explicit runtime stream or file ingestion.\n"
                "PROMPT-01 — Semantic fidelity: Prompt Pseudocode MUST represent all and only operative TASK-01 semantics that remain applicable to the requested work after the confirmation protocol is complete.\n"
                "PROMPT-02 — No substantive solution: Prompt Pseudocode MUST NOT solve the task, research task facts, inspect task-specific resources, plan the response, or include substantive task findings.\n"
                "PROMPT-03 — No invented requirements: Prompt Pseudocode MUST NOT invent missing requirements or silently improve the user's request.\n"
                "PROMPT-04 — Unspecified details: If a detail is unspecified, Prompt Pseudocode MUST represent the request as currently understood. Prompt generation MUST NOT be replaced with clarification unless a higher-priority requirement makes the missing input genuinely blocking.\n"
                "PROMPT-05 — Revision semantics: A Prompt revision MUST apply the user's changed TASK-01 semantics and preserve every current TASK-01 requirement not changed by the user.\n\n"
                "OPERATIONAL GUIDELINES FOR PROMPT DRAFTING:\n"
                "1. Express the prompt in clean Structured English using uppercase action verbs (PDL-01, PDL-04).\n"
                "2. Active Construction Directives (PDL-09): When the user asks to implement, write, develop, or create software, data structures, algorithms, or tests, use active construction verbs (IMPLEMENT, CONSTRUCT, DEFINE) and preserve the target language (e.g., 'in Python') and interface contracts.\n"
                "3. No Metatask Ingestion (PDL-09): DO NOT use 'READ the task specification' or 'READ the request'. The user prompt is the communicative frame, not a runtime data stream to be read.\n"
                "4. Parameter vs. Stream Discrimination (PDL-09): Use READ strictly for explicit runtime stream or file ingestion. Represent function parameters, mathematical constants, and data structure inputs as parameters to accept or take, not streams to read.\n"
                "5. Layout: Each distinct operation or requirement MUST appear on its own line (PDL-02).\n"
                "6. No Invented Field Schemas: DO NOT use fielded prefixes like 'TASK:', 'OUTPUT:', 'INPUT:', 'INCLUDE:', 'CONSTRAINTS:' (PDL-05). State each operation directly.\n"
                "7. Zero Execution Prohibitions & Substantive Delivery: Prompt Pseudocode defines the substantive deliverable to be produced upon execution (PROMPT-01). PROMPT-02 means that Prompt Pseudocode itself does not leak or pre-solve the problem during drafting; it is an author-time constraint and MUST NEVER be projected into an execution-time prohibition. Prompt Pseudocode MUST specify that execution computes, solves, and produces the requested concrete solutions, entities, and outputs in full. NEVER command execution to omit, evade, placeholderize, or avoid computing the requested solution (e.g. do not write 'without providing actual entity names', 'without computing a specific coloring solution', 'provide only specification', 'do not compute', 'insert placeholders', or 'no executable code') (PROMPT-01, PROMPT-02, PDL-08, PDL-09)."
            )
        elif operation_name in ("DRAFT_PLAN", "REVISE_PLAN"):
            extra_guidance = (
                "\n\nNORMATIVE GUIDELINES AND SPECIFICATION FOR RESPONSE PLAN PSEUDOCODE (PDL-01 to PDL-09, PLAN-01 to PLAN-10):\n"
                "PDL-01 — Structured English: Pseudocode MUST use readable structured English compatible with the project PDL profile.\n"
                "PDL-02 — Operation layout: Each operation SHOULD appear on its own line; equally indented operations are read top to bottom; subordinate operations are indented beneath the operation that controls or qualifies them.\n"
                "PDL-03 — Domain terminology: Pseudocode MUST use task-domain terminology rather than invent a separate task schema.\n"
                "PDL-04 — Action/control casing: Common action verbs and control keywords MAY be uppercased when helpful for readability.\n"
                "PDL-05 — No invented field schema: Pseudocode MUST NOT invent a fielded protocol schema.\n"
                "PDL-06 — Prefer ordinary structured English: Pseudocode MUST NOT imitate programming syntax when ordinary structured English is clearer.\n"
                "PDL-07 — Standard control forms: Standard-compatible IF/ELSE/ENDIF, WHILE/ENDWHILE, REPEAT/UNTIL, FOR/ENDFOR, and CASE/ENDCASE forms MAY be used when useful.\n"
                "PDL-08 — Purpose-complete notation: Prompt and Response Plan Pseudocode MUST be complete for their protocol purpose without artificial expansion into implementation algorithms.\n"
                "PDL-09 — Imperative construction and ingestion boundary: Prompt and Response Plan Pseudocode MUST NOT use data-reading verbs (READ, PARSE, ANALYZE, EXAMINE) with the user prompt, request, or task specification as the object. When the request asks to implement, create, or write software, pseudocode MUST retain active construction verbs (IMPLEMENT, CONSTRUCT, DEFINE) and target language directives. READ MUST be reserved strictly for explicit runtime stream or file ingestion.\n"
                "PLAN-01 — Coverage before minimization: For each material action or deliverable in the confirmed Prompt Pseudocode, the Response Plan MUST represent it with a high-level operation or cover it unambiguously with a broader operation.\n"
                "PLAN-02 — Minimum sufficient procedure: The Response Plan MUST expose only enough procedure for the user to reject a materially undesirable response approach.\n"
                "PLAN-03 — Neutrality: The Response Plan MUST remain neutral and high-level.\n"
                "PLAN-04 — No answer leakage: The Response Plan MUST NOT answer the request, anticipate findings, choose winners, invent hypotheses, lock arguments, preselect substantive conclusions, or otherwise perform the requested task.\n"
                "PLAN-05 — No unnecessary implementation commitment: The Response Plan MUST NOT choose unrequired sources or over-specify evidence, examples, calculations, sections, or low-level reasoning.\n"
                "PLAN-06 — No substantive research: Response Plan generation MUST NOT research the substantive task.\n"
                "PLAN-07 — Revision semantics: A Plan revision MUST keep the confirmed Prompt fixed, apply only changed TASK-02 semantics, and preserve PLAN-01 through PLAN-03.\n"
                "PLAN-08 — Carried approach constraints: When ordered TASK-02 projections are supplied to a Plan operation, the Response Plan MUST incorporate their operative approach constraints while remaining consistent with the confirmed Prompt and the other Plan requirements.\n"
                "PLAN-10 — Negative constraint operationalization by omission: When Prompt Pseudocode specifies negative constraints, exclusions, or unhandled conditions (e.g. 'do not do X', 'let unhandled exceptions propagate'), the Response Plan MUST operationalize them as structural omission rather than defensive assertions, catch-all wrappers, or redundant re-raises. In programming deliverables, native platform propagation and runtime defaults MUST be relied upon without generating active procedural steps for unrequested conditions.\n\n"
                "OPERATIONAL GUIDELINES FOR RESPONSE PLAN DRAFTING:\n"
                "1. Express the response plan in clean Structured English using uppercase action verbs (PDL-01, PDL-04).\n"
                "2. Layout: Each step MUST appear on its own line (PDL-02). DO NOT invent prefixes like 'STEP 1:', 'ACTION:', 'RESULT:' (PDL-05).\n"
                "3. Procedure to Deliverable: Specify the high-level procedural steps to execute and compute the concrete deliverable (PLAN-01, PLAN-02).\n"
                "4. Active Construction: Plan the concrete procedural steps that produce the deliverable itself (e.g. data structure design, method implementations, algorithm logic, unit test suite). Do not plan steps that ask the user for input unless the prompt requests an interactive dialogue.\n"
                "5. Neutrality & No Placeholders: Do not leak substantive answers into the plan (PLAN-04). PLAN-04 is a planner-time constraint and MUST NEVER be projected into an execution-time prohibition. The Plan MUST specify procedures that compute and produce the requested concrete deliverable upon execution. NEVER insert placeholder steps, evasive notes, or meta-prohibitions commanding execution to avoid calculating, omit concrete values, or withhold the answer (e.g. do not write 'without calculating or outputting a concrete assignment', 'insert placeholders without performing computation', 'do not implement', 'do not provide actual names', or 'contains no executable code') (PLAN-04, PLAN-10, PDL-08, PDL-09)."
            )
        elif operation_name == "DRAFT_EXECUTE":
            extra_guidance = (
                "\n\nDRAFT_EXECUTE: write an execution brief in plain text (brief_body): algorithmic choice, "
                "data structures, and estimated step count against the step budget in AVAILABLE_EXECUTION_TOOLS. "
                "Do not draft witness payloads, delivery markers, or hypothetical outcome branches; focus strictly "
                "on computational feasibility. The brief is passed to the EXECUTE call that follows; do not write the "
                "deliverable here."
            )
        elif operation_name == "EXECUTE":
            extra_guidance = (
                "\n\nNORMATIVE GUIDELINES FOR EXECUTE (EXEC-01, AUTH-03, AUTH-04, GUARD-03):\n"
                "- Deliver the result the confirmed prompt asks for, following the confirmed plan. Do not substitute a description of how the result could be obtained.\n"
                "- AVAILABLE_EXECUTION_TOOLS describes the execution environment exactly. Work within it. REQUEST_INPUT is only for non-semantic data that the user holds and the task cannot proceed without (EXEC-01); an environment capability is never user input.\n"
                "- SUPPLIED_EXECUTION_INPUT_SOURCE, when present, is the user's original source text: use its data, and let the confirmed prompt govern where they differ (AUTH-04).\n"
                "- A deliverable may be code, an analytical derivation, a proof, or a direct answer; all are first-class. Never present a guessed or estimated result as exact or verified.\n"
                "- When the deliverable includes Python code, the host runs it as described in AVAILABLE_EXECUTION_TOOLS. To certify a computed result, print exactly one line `WITNESS: <json>` to stdout."
            )
        elif operation_name == "EXECUTE_UNCONFIRMED":
            extra_guidance = (
                "\n\nNORMATIVE GUIDELINES FOR EXECUTE_UNCONFIRMED (UNC-01, UNC-02, UNC-03, UNC-04, GUARD-03):\n"
                "- Write your working understanding in `interpretation` and your working plan in `approach`, using PDL notation.\n"
                "- Deliver the substantive result in `body`. Work within AVAILABLE_EXECUTION_TOOLS.\n"
                "- REQUEST_INPUT is only for non-semantic data that the user holds and the task cannot proceed without (UNC-04, EXEC-01); people or events described in the task are part of the task, not a source of input.\n"
                "- A deliverable may be code, an analytical derivation, a proof, or a direct answer; all are first-class. Never present a guessed or estimated result as exact or verified.\n"
                "- When the deliverable includes Python code, the host runs it as described in AVAILABLE_EXECUTION_TOOLS. To certify a computed result, print exactly one line `WITNESS: <json>` to stdout."
            )

        if instructions:
            body["instructions"] = instructions + extra_guidance
        elif extra_guidance:
            body["instructions"] = extra_guidance.strip()
        if self.max_output_tokens:
            body["max_output_tokens"] = self.max_output_tokens
        effort = self._reasoning_for(getattr(request, "operation", None))
        if effort == "none":
            body["reasoning"] = {"enabled": False}
        elif effort is not None:
            if isinstance(effort, int) or (isinstance(effort, str) and effort.isdigit()):
                body["reasoning"] = {"max_tokens": int(effort)}
            else:
                body["reasoning"] = {"effort": effort}

        if self.provider_pinning:
            body["provider"] = self.provider_pinning
        if self.safety_settings:
            body["safety_settings"] = self.safety_settings

        # The output constraint for this call: the schema the projection showed the
        # model, in the same form (contract_form; ADR-0028 rules 1 and 5), so it holds
        # in the host's modes for this call too.
        union_wrapped = False
        if form.grammar == "schema":
            output_kind = (getattr(request, "manifest", None) or {}).get("output_kind", "json_object")
            shown = (getattr(getattr(request, "projection", None), "document", None) or {}).get("output_schema")
            sent_schema = grammar_view(shown) if shown is not None else grammar_schema(operation_name, form)
            union_wrapped = is_union_wrapped(sent_schema)
            body["text"] = {"format": {"type": "json_schema", "name": output_kind, "schema": sent_schema}}
        elif form.grammar == "json":
            body["text"] = {"format": {"type": "json_object"}}

        return body, union_wrapped, effort

    def _call(self, request: Any) -> WorkerResult:
        operation_name = getattr(request, "operation", None)

        # ADR-0017 / ADR-0020: Wire System 1 (Jev / ModernBERT) for fast classification, boundary enforcement, and review
        if operation_name == "INTERPRET_ACTIVATION":
            try:
                user_msg = ""
                proj = getattr(request, "projection", None)
                if proj and isinstance(getattr(proj, "document", None), dict):
                    user_msg = proj.document.get("operation_inputs", {}).get("RAW_USER_MESSAGE", "")
                if not user_msg:
                    try:
                        parsed_in = json.loads(request.prompt.split("\n\n", 1)[-1])
                        user_msg = parsed_in.get("operation_inputs", {}).get("RAW_USER_MESSAGE", "")
                    except Exception:
                        pass
                if user_msg:
                    from pdl_taskmaster.providers.sys1.recipes.activation_route import ActivationRouteRecipe
                    recipe = ActivationRouteRecipe()

                    if not self.sys1_client.is_configured:
                        safe_k = self._resolve_api_key_safe()
                        if safe_k:
                            self.sys1_client.api_key = safe_k
                    if self.sys1_client.is_configured:
                        sys1_req = recipe.build_request({"request": user_msg})
                        resp_body, duration_ms = self.sys1_client.call(sys1_req)
                        result = recipe.parse_response(resp_body, duration_ms=duration_ms)
                        if result.passed_gating:
                            wire_payload = recipe.map_to_wire(result)
                            metadata = {
                                "worker": "sys1",
                                "model": self.sys1_client.model,
                                "observed_model": self.sys1_client.model,
                                "recipe": recipe.name,
                                "confidence": result.confidence,
                                "latency_ms": round(duration_ms, 3),
                                "operation": operation_name,
                            }
                            return WorkerResult(json.dumps(wire_payload), metadata)
            except Exception:
                pass

        elif operation_name in ("INTERPRET_PROMPT_REVIEW", "INTERPRET_PLAN_REVIEW"):
            if not self.sys1_client.is_configured:
                safe_k = self._resolve_api_key_safe()
                if safe_k:
                    self.sys1_client.api_key = safe_k
            if self.sys1_client.is_configured:
                try:
                    proj = getattr(request, "projection", None)
                    doc = proj.document if proj and isinstance(getattr(proj, "document", None), dict) else {}
                    op_inputs = doc.get("operation_inputs", {})
                    subject_body = op_inputs.get("BOUND_REVIEW_SUBJECT_BODY", "")
                    user_msg = op_inputs.get("RAW_USER_REVIEW_MESSAGE", "")
                    artifact_kind = "plan" if operation_name == "INTERPRET_PLAN_REVIEW" else "prompt"

                    if not (subject_body and user_msg):
                        try:
                            parsed_in = json.loads(request.prompt.split("\n\n", 1)[-1])
                            op_inputs = parsed_in.get("operation_inputs", {})
                            subject_body = op_inputs.get("BOUND_REVIEW_SUBJECT_BODY", "")
                            user_msg = op_inputs.get("RAW_USER_REVIEW_MESSAGE", "")
                        except Exception:
                            pass

                    if subject_body and user_msg:
                        from pdl_taskmaster.providers.sys1.recipes.confirmation_match import ConfirmationMatchRecipe
                        from pdl_taskmaster.providers.sys1.recipes.review_facets import ReviewFacetsRecipe

                        conf_recipe = ConfirmationMatchRecipe()
                        conf_req = conf_recipe.build_request({"proposal": subject_body, "response": user_msg})
                        conf_body, duration_ms = self.sys1_client.call(conf_req)
                        conf_res = conf_recipe.parse_response(conf_body, duration_ms=duration_ms)

                        if conf_res.passed_gating and conf_res.verdict in ("agrees", "rejects"):
                            wire_payload = conf_recipe.map_to_wire(conf_res)
                            metadata = {
                                "worker": "sys1",
                                "model": self.sys1_client.model,
                                "observed_model": self.sys1_client.model,
                                "recipe": conf_recipe.name,
                                "confidence": conf_res.confidence,
                                "latency_ms": round(duration_ms, 3),
                                "operation": operation_name,
                            }
                            return WorkerResult(json.dumps(wire_payload), metadata)

                        # Evaluate multi-label review facets
                        facets_recipe = ReviewFacetsRecipe()
                        facets_req = facets_recipe.build_request({
                            "artifact_kind": artifact_kind,
                            "content": subject_body,
                            "feedback": user_msg,
                        })
                        facets_body, duration_ms2 = self.sys1_client.call(facets_req)
                        facets_res = facets_recipe.parse_response(facets_body, duration_ms=duration_ms2)
                        if facets_res.passed_gating:
                            wire_payload = facets_recipe.map_to_wire(facets_res)
                            metadata = {
                                "worker": "sys1",
                                "model": self.sys1_client.model,
                                "observed_model": self.sys1_client.model,
                                "recipe": facets_recipe.name,
                                "confidence": facets_res.confidence,
                                "latency_ms": round(duration_ms + duration_ms2, 3),
                                "operation": operation_name,
                            }
                            return WorkerResult(json.dumps(wire_payload), metadata)
                except Exception:
                    pass

        body, union_wrapped, effort = self.build_request_body(request)

        api_key = self._resolve_api_key()
        req = self._responses_request(body, api_key)

        started = time.perf_counter()
        call_deadline = time.monotonic() + self.max_call_seconds
        try:
            data = self._send_json_with_retries(req, call_deadline)
        except ProviderError as exc:
            # EXECUTE keeps one call per counted attempt: its rejection is the
            # attempt's failure. Every other operation falls back (see below).
            if not exc.wire_equivalent or operation_name == "EXECUTE" or "text" not in body:
                raise
            data, req, union_wrapped = self._schema_rejection_fallback(body, api_key, exc, call_deadline,
                                                                       union_wrapped)
        latency_ms = (time.perf_counter() - started) * 1000.0
        # Whether the request that answered carried the output schema (the rejection
        # fallback may have dropped it).
        try:
            constrained = "text" in json.loads(req.data or b"{}")
        except ValueError:
            constrained = "text" in body

        self._progress(f"response received in {latency_ms:.0f}ms")

        if data.get("error"):
            raise ProviderError("PROVIDER_REJECTED_REQUEST", f"provider reported an error: {data['error']}")
        status = data.get("status")
        details = data.get("incomplete_details") or {}
        reason = details.get("reason") if isinstance(details, dict) else details
        self._record_reply(data, schema_constrained=constrained)
        if status not in (None, "completed"):
            if status == "incomplete" and reason in ("max_output_tokens", "max_tokens", "length"):
                partial = self._extract_output_text(data, strip=False)
                trailing = len(partial) - len(partial.rstrip())
                stall = constrained and trailing >= STALL_WHITESPACE_CHARS
                if self.current_call is not None:
                    self.current_call.reply.update(trailing_whitespace=trailing, whitespace_stall=stall)
                if stall and operation_name:
                    # The decoding constraint, not the model's length, ended this reply:
                    # later calls of this operation go without it (the host still
                    # validates every reply). This call stays a failed attempt.
                    self.unconstrained_operations.add(operation_name)
                    self._progress(f"{operation_name}: the reply stalled in whitespace under the output schema "
                                   f"({trailing} trailing characters); later {operation_name} calls in this "
                                   "session are sent without the schema constraint")
                raise OutputLimitError(self.max_output_tokens, partial_text=partial or None, whitespace_stall=stall)
            raise ProviderError("PROVIDER_RESPONSE_UNREADABLE", f"response status={status}: {details}")

        text = self._extract_output_text(data)
        if not text:
            # Empty output with status=completed is a stochastic upstream fault
            # (output tokens consumed, message dropped — observed on shared-pool
            # aggregators). It is a transport condition, not model behavior:
            # retry with the same exponential-backoff treatment as 429/5xx.
            for retry in range(3):
                _sleep_within(0.5 * (2 ** retry), call_deadline)
                data = self._send_json_with_retries(req, call_deadline)
                text = self._extract_output_text(data)
                if text:
                    break
            self._record_reply(data, schema_constrained=constrained)
            if not text:
                raise ProviderError("PROVIDER_RESPONSE_UNREADABLE", "no output text after empty-output retries")
        if union_wrapped:
            text = _unwrap_union_reply(text)

        usage_raw = data.get("usage") or {}
        usage: dict[str, Any] = {}
        for key in ("input_tokens", "output_tokens", "total_tokens"):
            if isinstance(usage_raw.get(key), (int, float)):
                usage[key] = usage_raw[key]
        cached = (usage_raw.get("input_tokens_details") or {}).get("cached_tokens")
        if isinstance(cached, (int, float)):
            usage["cached_tokens"] = cached
        reasoning = (usage_raw.get("output_tokens_details") or {}).get("reasoning_tokens")
        if isinstance(reasoning, (int, float)):
            usage["reasoning_tokens"] = reasoning

        metadata: dict[str, Any] = {
            "worker": "api",
            "model": self.model,
            "observed_model": data.get("model"),
            "mode": "live-api",
            "reasoning_effort": effort if effort is not None else "provider_default",
            "operation": getattr(request, "operation", None),
            "not_a_qualified_measurement_condition": True,
            "base_url": self.base_url,
            "response_id": data.get("id"),
            "latency_ms": round(latency_ms, 3),
            "token_telemetry": "enabled" if self.capture_tokens else "disabled",
        }
        if self.capture_tokens and usage:
            metadata["usage"] = usage
            metadata["usage_source"] = "responses_api"
            metadata["usage_exact"] = True
        return WorkerResult(text, metadata)

    def _record_reply(self, data: dict[str, Any], *, schema_constrained: bool) -> None:
        """What the API reported for the call in flight (call-trace.jsonl): the
        response id (OpenRouter's generation id, for its TTFT and provider), status,
        finish reason, output and reasoning tokens."""
        if self.current_call is None:
            return
        usage = data.get("usage") or {}
        details = data.get("incomplete_details") or {}
        self.current_call.reply.update({
            "response_id": data.get("id"),
            "model": data.get("model"),
            "status": data.get("status"),
            "finish": details.get("reason") if isinstance(details, dict) else details,
            "output_tokens": usage.get("output_tokens"),
            "reasoning_tokens": (usage.get("output_tokens_details") or {}).get("reasoning_tokens"),
            "schema_constrained": schema_constrained,
        })

    def _responses_request(self, body: dict[str, Any], api_key: str) -> urllib.request.Request:
        return urllib.request.Request(
            f"{self.base_url}/responses",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

    def _progress(self, line: str, *, console: str | None = None) -> None:
        """One progress line to the console callback (``console`` when given, a
        shorter form) and the session's worker-progress log (progress_path, set
        by the host per session)."""
        if self.on_progress is not None:
            try:
                self.on_progress(line if console is None else console)
            except Exception:
                pass
        if self.progress_path is not None:
            try:
                path = Path(self.progress_path)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8", newline="\n") as handle:
                    handle.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {' '.join(line.split())}\n")
            except OSError:
                pass

    def _report_failed_generation(self, error: ProviderError) -> None:
        """A rejected generation, as one line in the worker-progress log."""
        if error.failed_generation:
            provider = _rejecting_provider(error, list((self.provider_pinning or {}).get("order") or [])) \
                if "Upstream error from " in str(error) else None
            label = f"failed_generation{f' ({provider})' if provider else ''}"
            self._progress(f"{label}: " + json.dumps(error.failed_generation[:_FAILED_GENERATION_CHARS],
                                                    ensure_ascii=False),
                           console=f"{label}: {len(error.failed_generation)} chars, in the worker-progress log")

    def _schema_rejection_fallback(
        self, body: dict[str, Any], api_key: str, rejection: ProviderError, deadline: float, union_wrapped: bool
    ) -> tuple[dict[str, Any], urllib.request.Request, bool]:
        """A provider rejected the generation against the output schema (Groq
        strict mode, in a live REPL session). Retry on each remaining configured
        provider; with none left, retry once without the decoding constraint. The
        host still validates every reply against the exact pydantic model, so
        nothing is loosened. Returns (response, the request that produced it,
        whether the reply is union-wrapped)."""
        pinning = dict(body.get("provider") or {})
        remaining = list(pinning.get("order") or [])
        rejected: list[str] = []
        error = rejection
        while True:
            provider = _rejecting_provider(error, remaining)
            if provider is not None:
                rejected.append(provider)
                remaining = remaining[remaining.index(provider) + 1:] if provider in remaining else remaining[1:]
            if not remaining:
                break
            self._progress(f"{provider or 'the provider'} rejected the output against the schema; "
                           f"retrying on {remaining[0]}")
            trial = {**body, "provider": {**pinning, "order": remaining, "ignore": list(rejected)}}
            req = self._responses_request(trial, api_key)
            try:
                return self._send_json_with_retries(req, deadline), req, union_wrapped
            except ProviderError as exc:
                if not exc.wire_equivalent:
                    raise
                error = exc
        self._progress("every configured provider rejected the output against the schema; "
                       "retrying once without the schema constraint")
        trial = {key: value for key, value in body.items() if key != "text"}
        req = self._responses_request(trial, api_key)
        try:
            return self._send_json_with_retries(req, deadline), req, False
        except ProviderError as exc:
            if not exc.wire_equivalent:
                raise
            tried = ", ".join(rejected) or "the provider"
            raise ProviderError(
                "OUTPUT_MALFORMED",
                f"the reply did not match the output schema at {tried}, nor once without the constraint",
                wire_equivalent=True,
                attempts=[{"provider": name, "message": "output rejected against the schema"} for name in rejected],
            ) from exc

    @staticmethod
    def _extract_output_text(data: dict[str, Any], *, strip: bool = True) -> str:
        chunks: list[str] = []
        for item in data.get("output") or []:
            if item.get("type") != "message":
                continue
            for part in item.get("content") or []:
                if part.get("type") == "output_text" and isinstance(part.get("text"), str):
                    chunks.append(part["text"])
        text = "".join(chunks)
        return text.strip() if strip else text
