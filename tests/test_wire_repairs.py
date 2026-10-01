"""Tests for wire-level robustness repairs added after the GLM-4.7 n=3 run:

1. OperationBridge._object tolerates prose/fence placement but never repairs
   malformed JSON content (the DRIP-03 T2 `," "` glitch must still fail).
2. All-empty REVIEW_FACTS maps mechanically to SUBSTANTIVE_DISCUSSION
   (REVIEW-09/13/14) instead of fatally raising review_facts_empty
   (the DRIP-02 T1 / DRIP-04 T1 disqualifications).
3. SessionEngine._call retries once on WireError with an operator correction
   appended outside the projection document (projection hash unchanged).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json

import pytest

from pdl_taskmaster.runtime.operation_bridge import OperationBridge, WireError
from pdl_taskmaster.runtime.session_engine import SessionEngine


BRIDGE = OperationBridge(ROOT)


def test_object_accepts_bare_json() -> None:
    assert BRIDGE._object('{"kind": "CANCEL"}') == {"kind": "CANCEL"}


def test_object_accepts_fenced_json() -> None:
    text = "```json\n{\"kind\": \"CANCEL\"}\n```"
    assert BRIDGE._object(text) == {"kind": "CANCEL"}


def test_object_accepts_prose_wrapped_json() -> None:
    text = 'Here is the outcome you asked for:\n\n{"kind": "CANCEL"}\n\nLet me know.'
    assert BRIDGE._object(text) == {"kind": "CANCEL"}


def test_object_accepts_bom_and_surrounding_whitespace() -> None:
    assert BRIDGE._object('\ufeff  {"kind": "CANCEL"}  ') == {"kind": "CANCEL"}


def test_object_still_rejects_malformed_json() -> None:
    # The exact DRIP-03 T2 token glitch: a stray string token inside the object.
    with pytest.raises(WireError, match="invalid_json"):
        BRIDGE._object('{"kind":"PROMPT","prompt_body":"x", " "approach_handoff":"NONE"}')


def test_object_rejects_non_object_json() -> None:
    with pytest.raises(WireError, match="not_object"):
        BRIDGE._object('["not", "an", "object"]')


def test_review_facts_all_empty_maps_to_substantive_discussion() -> None:
    facts = json.dumps(
        {
            "kind": "REVIEW_FACTS",
            "task_change_dimensions": [],
            "approach_change_dimensions": [],
            "progression_requested": False,
        }
    )
    assert BRIDGE.parse_prompt_review(facts) == {"intent": "SUBSTANTIVE_DISCUSSION"}
    assert BRIDGE.parse_plan_review(facts) == {"intent": "SUBSTANTIVE_DISCUSSION"}


def test_review_facts_with_progression_still_accepts() -> None:
    facts = json.dumps(
        {
            "kind": "REVIEW_FACTS",
            "task_change_dimensions": [],
            "approach_change_dimensions": [],
            "progression_requested": True,
        }
    )
    assert BRIDGE.parse_prompt_review(facts) == {"intent": "ACCEPT_CURRENT"}


def test_retry_once_with_operator_correction(tmp_path: Path) -> None:
    """A WireError on first response triggers exactly one corrective re-call;
    the correction is appended outside the projection document so the
    projection manifest (and its sha256) is identical across both calls."""
    repo_root = Path(__file__).resolve().parents[2]
    responses = iter(["not json at all", '{"kind": "CANCEL"}'])
    seen_prompts: list[str] = []
    seen_manifests: list[dict] = []

    def flaky_model_call(request):
        seen_prompts.append(request.prompt)
        seen_manifests.append(request.manifest)
        return next(responses)

    seen_manifests: list[dict] = []

    engine = SessionEngine(
        repo_root,
        model_call=flaky_model_call,  # type: ignore[arg-type]
        workspace_root=tmp_path,
    )
    engine.workspace = engine._new_workspace()
    traces: list = []
    decision = engine._call(
        "INTERPRET_PROMPT_REVIEW",
        {
            "BOUND_REVIEW_SUBJECT_KIND": "PROMPT",
            "BOUND_REVIEW_SUBJECT_BODY": "test body",
            "RAW_USER_REVIEW_MESSAGE": "hello",
        },
        traces,
        parser=BRIDGE.parse_prompt_review,
    )
    assert decision == {"intent": "CANCEL"}
    assert len(seen_prompts) == 2
    assert len(traces) == 2
    assert "OPERATOR CORRECTION" in seen_prompts[1]
    assert "OPERATOR CORRECTION" not in seen_prompts[0]
    # Retry path must not perturb the compiled projection.
    assert seen_manifests[0] == seen_manifests[1]


def test_retry_exhaustion_raises_original_error(tmp_path: Path) -> None:
    """If both responses fail validation, the FIRST error is raised so the
    root cause (not the retry's symptom) surfaces to the caller."""
    repo_root = Path(__file__).resolve().parents[2]

    def always_bad(request):
        return '{"kind": "TOTALLY_UNKNOWN_KIND"}'

    engine = SessionEngine(
        repo_root,
        model_call=always_bad,  # type: ignore[arg-type]
        workspace_root=tmp_path,
    )
    engine.workspace = engine._new_workspace()
    with pytest.raises(WireError) as excinfo:
        engine._call(
            "INTERPRET_PROMPT_REVIEW",
            {
                "BOUND_REVIEW_SUBJECT_KIND": "PROMPT",
                "BOUND_REVIEW_SUBJECT_BODY": "test body",
                "RAW_USER_REVIEW_MESSAGE": "hello",
            },
            [],
            parser=BRIDGE.parse_prompt_review,
        )
    assert "kind" not in str(excinfo.value) or True  # original error surfaces
    assert str(excinfo.value) == str(WireError("artifact_review_kind"))


def test_parse_plan_body_unescapes_literal_newlines() -> None:
    wire = r'{"neutral_plan_body": "CONFIRM prompt.\n\nOPERATION: Solve.\n\n1. RECEIVE input.\n2. RETURN output."}'
    parsed = BRIDGE.parse_plan_body(wire)
    assert "\n" in parsed
    assert "\\n" not in parsed
    assert parsed == "CONFIRM prompt.\n\nOPERATION: Solve.\n\n1. RECEIVE input.\n2. RETURN output."


def test_parse_prompt_body_unescapes_literal_newlines() -> None:
    wire = r'{"prompt_body": "PARTITION the input string.\n\nMINIMIZE the cuts."}'
    parsed = BRIDGE.parse_prompt_body(wire)
    assert "\n" in parsed
    assert "\\n" not in parsed
    assert parsed == "PARTITION the input string.\n\nMINIMIZE the cuts."


# Pseudocode notation is linted after parsing (plan_soundness, one redraft), never
# enforced as a wire failure and never rewritten by the host (AUTH-05).
_NOTATION_CASES = [
    ("prompt", r'{"prompt_body": "TASK: Partition the string.\nOUTPUT: Return min cuts."}', "PDL-05"),
    # Session 7 Run 2 prompt payload
    ("prompt", '{"prompt_body": "PARTITION the string into palindrome substrings.\\n'
               'DO NOT perform the partitioning; only describe the required result."}', "PDL-08"),
    # Session 7 Run 2 plan payload
    ("plan", '{"neutral_plan_body": "IDENTIFY palindromes.\\n'
             'INSERT placeholders for the substantive results without performing any computation"}', "PLAN-10"),
]


@pytest.mark.parametrize("kind, wire, clause", _NOTATION_CASES)
def test_notation_violations_parse_unchanged_and_are_linted(kind, wire, clause) -> None:
    from pdl_taskmaster.verification.plan_soundness import validate_plan_soundness

    body = BRIDGE.parse_prompt_body(wire) if kind == "prompt" else BRIDGE.parse_plan_body(wire)
    field = "prompt_body" if kind == "prompt" else "neutral_plan_body"
    assert body == json.loads(wire)[field].strip()  # no host rewrite
    lint = validate_plan_soundness(body)
    assert not lint.valid and clause in lint.feedback


def test_parse_plan_review_disambiguates_action_to_revise_approach() -> None:
    # Exact wire payload from Session 4 0005-interpret_plan_review where model
    # reported ACTION_SUBJECT_OR_OBJECT when user said "you have to plan your response now".
    wire = '{"kind": "REVIEW_FACTS", "task_change_dimensions": ["ACTION_SUBJECT_OR_OBJECT"], "approach_change_dimensions": [], "progression_requested": false}'
    res = BRIDGE.parse_plan_review(wire)
    assert res == {"intent": "REVISE_APPROACH"}


def test_api_worker_provider_pinning_and_fallbacks() -> None:
    from pdl_taskmaster.providers.api_worker import DEFAULT_PROVIDER_PINNING
    assert DEFAULT_PROVIDER_PINNING["allow_fallbacks"] is True
    order = DEFAULT_PROVIDER_PINNING["order"]
    assert "Baseten" in order
    assert "Amazon Bedrock" in order





def test_wholly_double_escaped_body_is_decoded_one_level() -> None:
    """Run 215232 r8: newlines and quotes were both escaped one level too deep;
    restoring only the newlines left print(\\"...\\") broken."""
    code = 'import json\nif True:\n    print("No valid partition exists.\\n")\n'
    wire = json.dumps({"kind": "RESULT", "body": json.dumps(code)[1:-1]})
    assert BRIDGE.parse_execution(wire).body == code


def test_api_call_has_a_hard_deadline_and_retries_a_read_timeout_once(monkeypatch) -> None:
    """EXECUTE=high runs (2026-10-01): the socket timeout bounded each read only, and
    read timeouts were retried 4 times, so one call could hold ~50 minutes."""
    import socket
    import urllib.request

    from pdl_taskmaster.providers import api_worker as module
    from pdl_taskmaster.providers.api_worker import ApiWorker, TransportError

    attempts: list[float] = []

    def stalled(req, timeout=None):
        attempts.append(timeout)
        raise socket.timeout("timed out")

    monkeypatch.setattr(module.urllib.request, "urlopen", stalled)
    monkeypatch.setattr(module.time, "sleep", lambda s: None)
    worker = ApiWorker(model="m", repo_root=ROOT, timeout=600.0, max_call_seconds=1200.0)
    req = urllib.request.Request("http://example.invalid", data=b"{}")
    with pytest.raises(TransportError, match="read timed out twice"):
        worker._send_json_with_retries(req)
    assert len(attempts) == 2 and all(t <= 600.0 for t in attempts)

    attempts.clear()
    with pytest.raises(TransportError, match="deadline"):
        worker._send_json_with_retries(req, deadline=module.time.monotonic() - 1)
    assert attempts == []


def test_api_attempt_timeout_never_exceeds_the_remaining_deadline(monkeypatch) -> None:
    import urllib.request

    from pdl_taskmaster.providers import api_worker as module
    from pdl_taskmaster.providers.api_worker import ApiWorker

    seen: list[float] = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return b'{"status": "completed"}'

    def ok(req, timeout=None):
        seen.append(timeout)
        return Response()

    monkeypatch.setattr(module.urllib.request, "urlopen", ok)
    worker = ApiWorker(model="m", repo_root=ROOT, timeout=600.0)
    worker._send_json_with_retries(urllib.request.Request("http://example.invalid", data=b"{}"),
                                   deadline=module.time.monotonic() + 30)
    assert seen and seen[0] <= 30


def test_worker_sends_the_output_cap_and_reports_truncation(monkeypatch) -> None:
    """The Responses API reads max_output_tokens; max_tokens was ignored (high EXECUTE
    returned 22K-35K tokens against max_tokens=4096)."""
    import json as _json
    import urllib.request

    from pdl_taskmaster.providers import api_worker as module
    from pdl_taskmaster.providers.api_worker import ApiWorker, OutputLimitError

    sent = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def read(self):
            return _json.dumps({"status": "incomplete", "incomplete_details": {"reason": "max_output_tokens"},
                                "output": []}).encode()

    def capture(req, timeout=None):
        sent.update(_json.loads(req.data))
        return Response()

    monkeypatch.setattr(module.urllib.request, "urlopen", capture)
    monkeypatch.setenv("OPENROUTER_API_KEY", "stub")
    worker = ApiWorker(model="m", repo_root=ROOT, max_output_tokens=8000)

    class Request:
        operation = "EXECUTE"
        prompt = "SYSTEM\n\nUSER"
        manifest = {}
        projection = None

    with pytest.raises(OutputLimitError) as caught:
        worker.call(Request())
    assert sent.get("max_output_tokens") == 8000 and "max_tokens" not in sent
    assert caught.value.output_limit == 8000


@pytest.mark.parametrize("operation", ["DRAFT_PROMPT", "REVISE_PROMPT", "DRAFT_PLAN", "REVISE_PLAN", "EXECUTE",
                                       "DRAFT_EXECUTE", "INTERPRET_PROMPT_REVIEW", "INTERPRET_PLAN_REVIEW",
                                       "INTERPRET_EXECUTION_INPUT", "ANSWER_PROTOCOL_DISCUSSION"])
def test_provider_schema_is_one_object_without_defaults(operation) -> None:
    """Run 132344: Groq and Cerebras reject a top-level anyOf/oneOf/discriminator
    ("schema must have type 'object'"), so every schema call silently fell back to a
    slower provider, or failed outright with fallbacks off."""
    import json as _json

    from pdl_taskmaster.providers.api_worker import ApiWorker
    from pdl_taskmaster.runtime.wire_payloads import get_operation_pydantic_schema

    raw = get_operation_pydantic_schema(operation)
    if not isinstance(raw, dict):
        pytest.skip("no pydantic schema for this operation")
    schema = ApiWorker._sanitize_schema_for_grammar(raw)
    assert schema.get("type") == "object"
    assert not {"anyOf", "oneOf", "discriminator", "enum", "not"} & set(schema)
    assert '"default"' not in _json.dumps(schema)  # no value advertised to the model
    if "kind" in schema["properties"]:
        assert "kind" in schema["required"]


def test_flattened_schema_still_validates_exactly_host_side() -> None:
    """Flattening is for the provider only: the host keeps the exact union."""
    with pytest.raises(WireError):
        BRIDGE.parse_prompt_body('{"prompt_body": "X", "approach_handoff": "NONE"}')
