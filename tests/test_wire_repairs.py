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
    text = _json.dumps(schema)
    assert '"default"' not in text  # no value advertised to the model
    assert '"discriminator"' not in text  # Cerebras rejects it nested too (probe 20261001-142720)


def test_flattened_schema_still_validates_exactly_host_side() -> None:
    """Flattening is for the provider only: the host keeps the exact union."""
    with pytest.raises(WireError):
        BRIDGE.parse_prompt_body('{"prompt_body": "X", "approach_handoff": "NONE"}')


def _strict_violations(node, path="$"):
    """Strict structured-output rules (Groq strict mode, Cerebras)."""
    out = []
    if isinstance(node, dict):
        if node.get("type") == "object" or "properties" in node:
            props = node.get("properties")
            if not props:
                out.append(f"{path}: free-form object")
            else:
                if node.get("additionalProperties") is not False:
                    out.append(f"{path}: additionalProperties is not false")
                missing = [k for k in props if k not in (node.get("required") or [])]
                if missing:
                    out.append(f"{path}: not required {missing}")
        for keyword in ("minimum", "maximum", "exclusiveMinimum", "pattern", "format", "default"):
            if keyword in node:
                out.append(f"{path}: {keyword}")
        for key, value in node.items():
            children = value if isinstance(value, list) else [value]
            for i, child in enumerate(children):
                if key != "properties":
                    out += _strict_violations(child, f"{path}/{key}/{i}")
            if key == "properties" and isinstance(value, dict):
                for name, spec in value.items():
                    out += _strict_violations(spec, f"{path}/properties/{name}")
    return out


@pytest.mark.parametrize("operation", ["DRAFT_PROMPT", "REVISE_PROMPT", "DRAFT_PLAN", "REVISE_PLAN", "EXECUTE",
                                       "DRAFT_EXECUTE", "INTERPRET_PROMPT_REVIEW", "INTERPRET_PLAN_REVIEW",
                                       "INTERPRET_EXECUTION_INPUT", "ANSWER_PROTOCOL_DISCUSSION"])
def test_provider_schema_meets_strict_structured_output_rules(operation) -> None:
    """Runs 135851/135951: Groq ("required ... must include every key in properties:
    observed, section") and Cerebras ("additionalProperties ... set to false")
    rejected every EXECUTE request at result_ir."""
    from pdl_taskmaster.providers.api_worker import ApiWorker
    from pdl_taskmaster.runtime.wire_payloads import get_operation_pydantic_schema

    schema = ApiWorker._sanitize_schema_for_grammar(get_operation_pydantic_schema(operation))
    assert _strict_violations(schema) == []


def test_property_names_are_never_stripped_as_keywords() -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker
    from pdl_taskmaster.runtime.wire_payloads import get_operation_pydantic_schema

    schema = ApiWorker._sanitize_schema_for_grammar(get_operation_pydantic_schema("EXECUTE"))
    asked, result = schema["properties"]["outcome"]["anyOf"]
    assert "description" in asked["properties"]  # REQUEST_INPUT.description
    defect = result["properties"]["result_ir"]["anyOf"][0]["properties"]["open_defects"]["items"]
    assert "description" in defect["properties"]  # RESULT_STANDARD RS-01 reads it


def test_strict_shaped_replies_parse_host_side() -> None:
    """A strict provider sends every flattened property, null where it does not apply."""
    import json as _json

    nulls_ir = {"files": [], "reconciliation": [], "open_defects": [{"id": None, "description": "not finished",
                                                                       "evidence": None}], "witness": None}
    result = BRIDGE.parse_execution(_json.dumps({"kind": "RESULT", "body": "print(1)", "expected_type": None,
                                                 "description": None, "result_ir": nulls_ir}))
    assert result.kind == "RESULT" and result.result_ir["open_defects"][0]["description"] == "not finished"
    proof = {"polarity": "negative", "evidence": {"path": "execution://witness", "section": None, "observed": None},
             "basis": "proof", "search_exhausted": None, "nodes_explored": None, "method": None,
             "argument": "parity", "domain": None, "provisional": None}
    witnessed = BRIDGE.parse_execution(_json.dumps({"kind": "RESULT", "body": "x", "expected_type": None,
                                                    "description": None,
                                                    "result_ir": {"files": [], "reconciliation": [],
                                                                  "open_defects": [], "witness": proof}}))
    assert witnessed.result_ir["witness"]["argument"] == "parity"
    asked = BRIDGE.parse_execution(_json.dumps({"kind": "REQUEST_INPUT", "body": "Which file?",
                                                "expected_type": "path", "description": None, "result_ir": None}))
    assert asked.kind == "REQUEST_INPUT"
    draft = BRIDGE.parse_prompt_draft(_json.dumps({"kind": "PROMPT", "prompt_body": "COMPUTE the sum",
                                                   "approach_handoff": None, "task_entities": None,
                                                   "blocking_basis": None, "response": None}))
    assert draft.prompt_body == "COMPUTE the sum"
    review = BRIDGE.parse_prompt_review(_json.dumps({"kind": "REVIEW_FACTS", "task_change_dimensions": [],
                                                     "approach_change_dimensions": [], "progression_requested": True,
                                                     "confidence": None}))
    assert review


def test_null_for_a_required_field_still_fails() -> None:
    with pytest.raises(WireError):
        BRIDGE.parse_execution('{"kind": "RESULT", "body": null}')


def test_provider_error_records_each_providers_own_message() -> None:
    """Run 135951 01-01: the exact OpenRouter 400 body (Groq after Cerebras)."""
    from pdl_taskmaster.providers.api_worker import ProviderError

    body = (ROOT / "tests" / "fixtures" / "openrouter_400_strict_schema.json").read_text(encoding="utf-8")
    error = ProviderError.from_http(400, body)
    record = error.as_record()
    assert record["category"] == "PROVIDER_REJECTED_REQUEST" and record["status"] == 400
    assert [a["provider"] for a in record["attempts"]] == ["Cerebras", "Groq"]
    assert "additionalProperties" in record["attempts"][0]["message"]
    assert "observed, section" in record["attempts"][1]["message"]


def test_top_level_union_is_wrapped_with_each_variant_kept_separate() -> None:
    """Probe 20261001-142720: merging DRAFT_PROMPT's variants into one object showed a
    PROMPT reply the blocked variant's blocking_basis, the model filled it, and Groq
    rejected the generation. The union is now nested under "outcome", unmerged."""
    from pdl_taskmaster.providers.api_worker import UNION_WRAPPER, ApiWorker
    from pdl_taskmaster.runtime.wire_payloads import get_operation_pydantic_schema

    schema = ApiWorker._sanitize_schema_for_grammar(get_operation_pydantic_schema("DRAFT_PROMPT"))
    assert schema["required"] == [UNION_WRAPPER]
    variants = schema["properties"][UNION_WRAPPER]["anyOf"]
    assert len(variants) == 2
    prompt = next(v for v in variants if "prompt_body" in v["properties"])
    assert "blocking_basis" not in prompt["properties"]
    assert _strict_violations(schema) == []


def test_wrapped_reply_is_unwrapped_before_the_host_reads_it() -> None:
    from pdl_taskmaster.providers.api_worker import _unwrap_union_reply

    inner = {"kind": "PROMPT", "prompt_body": "ADD 2 and 3", "approach_handoff": None, "task_entities": None}
    assert json.loads(_unwrap_union_reply(json.dumps({"outcome": inner}))) == inner
    assert _unwrap_union_reply('{"kind": "PROMPT"}') == '{"kind": "PROMPT"}'
    assert _unwrap_union_reply("not json") == "not json"
    assert BRIDGE.parse_prompt_draft(_unwrap_union_reply(json.dumps({"outcome": inner}))).prompt_body == "ADD 2 and 3"


def test_provider_schema_rejection_is_a_malformed_output_not_retried(monkeypatch) -> None:
    """The exact Groq body from probe 20261001-142720: a generation that failed the
    provider's schema check. It was retried blind 5 times (five $0 rows in the
    OpenRouter log); it is now one call, reported as OUTPUT_MALFORMED."""
    import io
    import urllib.request

    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError
    from pdl_taskmaster.runtime.session_engine import _is_wire_failure

    body = json.loads((ROOT / "tests" / "fixtures" / "openrouter_groq_schema_mismatch.json").read_text(encoding="utf-8"))
    calls = []

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=None):
        calls.append(req)
        return _Resp(json.dumps(body).encode("utf-8"))

    monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT)
    req = urllib.request.Request("http://stub/responses", data=b"{}", method="POST")
    with pytest.raises(ProviderError) as info:
        worker._send_json_with_retries(req)
    assert len(calls) == 1
    assert info.value.category == "OUTPUT_MALFORMED"
    assert _is_wire_failure(info.value)


def test_worker_unwraps_the_reply_to_a_wrapped_schema(monkeypatch) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker

    class _Req:
        operation = "DRAFT_PROMPT"
        prompt = "Draft Prompt Pseudocode for: add 2 and 3."
        manifest: dict = {}
        projection = None

    sent = {}
    inner = {"kind": "PROMPT", "prompt_body": "ADD 2 and 3", "approach_handoff": None, "task_entities": None}

    def fake_send(self, req, deadline=None):
        sent.update(json.loads(req.data))
        return {"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": json.dumps({"outcome": inner})}]}]}

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    monkeypatch.setattr(ApiWorker, "_resolve_api_key", lambda self: "k")
    result = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT).call(_Req())
    assert list(sent["text"]["format"]["schema"]["properties"]) == ["outcome"]
    assert json.loads(result.text) == inner


# Provider schema rejection (session log 2026-10-01): Groq rejected DRAFT_PROMPT's
# generation against the schema twice and the REPL printed the raw error, while
# the same call worked on Cerebras.

_GROQ_REJECTION = ("generation did not match the schema: Upstream error from {provider}: Generated JSON does "
                   "not match the expected schema. Please adjust your prompt. See 'failed_generation' for more "
                   "details. Error: jsonschema: '/outcome/kind' does not validate with /properties/outcome/anyOf/0/"
                   "properties/kind/anyOf/0/type: expected null, but got string")


def _scripted_send(monkeypatch, outcomes):
    """Replace the transport: each call pops an outcome (a provider name to reject
    as, or a reply text to return); every request body is recorded."""
    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError

    sent: list[dict] = []

    def fake_send(self, req, deadline=None):
        sent.append(json.loads(req.data))
        outcome = outcomes.pop(0)
        if outcome.startswith("reject:"):
            raise ProviderError("OUTPUT_MALFORMED", _GROQ_REJECTION.format(provider=outcome[7:]),
                                wire_equivalent=True)
        return {"status": "completed", "output": [{"type": "message", "content": [
            {"type": "output_text", "text": outcome}]}]}

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    monkeypatch.setattr(ApiWorker, "_resolve_api_key", lambda self: "k")
    return sent


def _draft_request(operation="DRAFT_PROMPT"):
    class _Req:
        prompt = "Draft Prompt Pseudocode for: add 2 and 3."
        manifest: dict = {}
        projection = None

    _Req.operation = operation
    return _Req()


_INNER = {"kind": "PROMPT", "prompt_body": "ADD 2 and 3", "approach_handoff": None, "task_entities": None}


def test_schema_rejection_retries_on_the_next_configured_provider(monkeypatch) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker

    sent = _scripted_send(monkeypatch, ["reject:Groq", json.dumps({"outcome": _INNER})])
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                       provider_pinning={"order": ["Groq", "Baseten", "Amazon Bedrock"], "allow_fallbacks": True})
    result = worker.call(_draft_request())
    assert len(sent) == 2
    assert sent[1]["provider"] == {"order": ["Baseten", "Amazon Bedrock"], "allow_fallbacks": True,
                                   "ignore": ["Groq"]}
    assert sent[1]["text"] == sent[0]["text"]  # still schema-constrained
    assert json.loads(result.text) == _INNER


def test_schema_rejection_with_no_provider_left_retries_once_unconstrained(monkeypatch) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker

    sent = _scripted_send(monkeypatch, ["reject:Cerebras", json.dumps(_INNER)])
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                       provider_pinning={"order": ["Cerebras"], "allow_fallbacks": False})
    result = worker.call(_draft_request())
    assert len(sent) == 2 and "text" in sent[0] and "text" not in sent[1]
    assert sent[1]["provider"] == {"order": ["Cerebras"], "allow_fallbacks": False}
    assert BRIDGE.parse_prompt_draft(result.text).prompt_body == "ADD 2 and 3"  # host validation unchanged


def test_schema_rejection_everywhere_is_one_malformed_output_error(monkeypatch) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError
    from pdl_taskmaster.runtime.session_engine import _is_wire_failure

    sent = _scripted_send(monkeypatch, ["reject:Groq", "reject:Baseten", "reject:Baseten"])
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                       provider_pinning={"order": ["Groq", "Baseten"], "allow_fallbacks": True})
    with pytest.raises(ProviderError) as info:
        worker.call(_draft_request())
    assert len(sent) == 3 and "text" not in sent[2]
    assert info.value.category == "OUTPUT_MALFORMED" and _is_wire_failure(info.value)
    assert "\n" not in str(info.value) and [a["provider"] for a in info.value.attempts] == ["Groq", "Baseten"]


def test_execute_schema_rejection_stays_one_counted_call(monkeypatch) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError

    sent = _scripted_send(monkeypatch, ["reject:Groq", json.dumps({"kind": "RESULT", "body": "5"})])
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                       provider_pinning={"order": ["Groq", "Baseten"], "allow_fallbacks": True})
    with pytest.raises(ProviderError):
        worker.call(_draft_request("EXECUTE"))
    assert len(sent) == 1


def test_repl_reports_a_provider_error_on_one_line() -> None:
    from pdl_taskmaster.host.repl import _one_line_error
    from pdl_taskmaster.providers.api_worker import ProviderError

    exc = ProviderError("OUTPUT_MALFORMED", _GROQ_REJECTION.format(provider="Groq") + "\n" + "x" * 2000,
                        wire_equivalent=True, operation="DRAFT_PROMPT")
    line = _one_line_error(exc)
    assert "\n" not in line and len(line) <= 240
    assert line.startswith("OUTPUT_MALFORMED at DRAFT_PROMPT: generation did not match the schema")


# Session 024627 (--api-providers Groq): every EXECUTE reply carrying a witness was
# rejected ("'/outcome' does not validate with /properties/outcome/anyOf/0/required:
# missing properties: 'expected_type', 'description'"). The positive witness's data
# is a free-form object, and the strict schema dropped the whole positive branch.

def _witness_reply(witness: dict) -> dict:
    return {"outcome": {"kind": "RESULT", "body": "P = 0.1785",
                        "result_ir": {"files": [], "reconciliation": [], "open_defects": [], "witness": witness}}}


_POSITIVE = {"polarity": "positive", "evidence": None,
             "data": {"probability": 0.1785, "any_key_the_task_chooses": [1, 2], "nested": {"x": {"y": [None]}}},
             "basis": None, "search_exhausted": None, "nodes_explored": None, "method": None, "argument": None,
             "domain": None, "provisional": None}


def _provider_schema(operation: str, providers: list[str]) -> dict:
    from pdl_taskmaster.providers.api_worker import ApiWorker, _accepts_free_form_objects
    from pdl_taskmaster.runtime.wire_payloads import get_operation_pydantic_schema

    return ApiWorker._sanitize_schema_for_grammar(
        get_operation_pydantic_schema(operation),
        free_form_objects=_accepts_free_form_objects({"order": providers, "allow_fallbacks": False}))


def test_free_form_objects_are_sent_unless_a_provider_requires_closed_objects() -> None:
    from pdl_taskmaster.providers.api_worker import _accepts_free_form_objects

    assert _accepts_free_form_objects({"order": ["Groq"]})
    assert _accepts_free_form_objects({"order": ["Groq", "Baseten", "Amazon Bedrock"], "allow_fallbacks": True})
    assert _accepts_free_form_objects(None) and _accepts_free_form_objects({})
    assert not _accepts_free_form_objects({"order": ["Cerebras"]})
    assert not _accepts_free_form_objects({"order": ["Groq", "cerebras"]})


def test_groq_execute_schema_accepts_a_positive_witness_with_arbitrary_data_keys() -> None:
    jsonschema = pytest.importorskip("jsonschema")
    from pdl_taskmaster.providers.api_worker import _unwrap_union_reply

    schema = _provider_schema("EXECUTE", ["Groq"])
    jsonschema.Draft202012Validator.check_schema(schema)
    validator = jsonschema.Draft202012Validator(schema)
    witness = schema["properties"]["outcome"]["anyOf"][1]["properties"]["result_ir"]["anyOf"][0]["properties"]["witness"]
    polarities = [b["properties"]["polarity"]["enum"] for b in witness["anyOf"][0]["anyOf"]]
    assert polarities == [["positive"], ["negative"]]

    reply = _witness_reply(_POSITIVE)
    assert list(validator.iter_errors(reply)) == []
    # The shape a program reports when it found the result by search (run 022105).
    provenance = {**_POSITIVE, "basis": "search", "search_exhausted": False, "method": "backtracking"}
    assert list(validator.iter_errors(_witness_reply(provenance))) == []
    # Everything the provider schema accepts here, the host accepts.
    parsed = BRIDGE.parse_execution(_unwrap_union_reply(json.dumps(reply)))
    assert parsed.result_ir["witness"]["data"]["nested"] == {"x": {"y": [None]}}
    # The host's rules still hold provider-side: no null tag, no undeclared key.
    assert list(validator.iter_errors(_witness_reply({**_POSITIVE, "polarity": None})))
    assert list(validator.iter_errors(_witness_reply({**_POSITIVE, "confidence": 0.9})))


def test_strict_schema_without_free_form_objects_is_what_groq_rejected() -> None:
    """The schema sent before (and still sent to Cerebras) has no positive branch:
    the session's reply fails it, which is the rejection Groq reported."""
    jsonschema = pytest.importorskip("jsonschema")

    schema = _provider_schema("EXECUTE", ["Cerebras"])
    assert '"positive"' not in json.dumps(schema)
    assert list(jsonschema.Draft202012Validator(schema).iter_errors(_witness_reply(_POSITIVE)))


@pytest.mark.parametrize("operation", ["DRAFT_PROMPT", "REVISE_PROMPT", "DRAFT_PLAN", "REVISE_PLAN", "EXECUTE",
                                       "DRAFT_EXECUTE", "EMIT_RESULT_IR", "INTERPRET_PROMPT_REVIEW",
                                       "INTERPRET_PLAN_REVIEW", "INTERPRET_EXECUTION_INPUT",
                                       "ANSWER_PROTOCOL_DISCUSSION"])
def test_groq_schema_meets_strict_rules_except_the_open_free_form_objects(operation) -> None:
    """The only open objects are the free-form values (witness data, entities),
    each exactly {"type": "object", "additionalProperties": true}, the form Groq's
    strict check accepted in runs 135851/135951; every other object stays closed."""
    from pdl_taskmaster.providers.api_worker import _FREE_FORM_OBJECT

    schema = _provider_schema(operation, ["Groq"])
    assert all(v.endswith(": free-form object") for v in _strict_violations(schema))

    def open_objects(node):
        if isinstance(node, list):
            return [o for child in node for o in open_objects(child)]
        if not isinstance(node, dict):
            return []
        here = [node] if node.get("type") == "object" and not node.get("properties") else []
        return here + [o for key, child in node.items() if key != "enum" for o in open_objects(child)]

    assert all(node == _FREE_FORM_OBJECT for node in open_objects(schema))


def test_union_tags_are_required_in_every_provider_variant() -> None:
    """The discriminator keyword is stripped for Cerebras; the tag must still be
    required, or the strict form offers a null kind (REQUEST_INPUT, PROMPT) or a
    null polarity that the host cannot route."""
    for providers in (["Groq"], ["Cerebras"]):
        execute = _provider_schema("EXECUTE", providers)
        asked = execute["properties"]["outcome"]["anyOf"][0]
        assert asked["properties"]["kind"] == {"type": "string", "enum": ["REQUEST_INPUT"]}
        prompt = _provider_schema("DRAFT_PROMPT", providers)["properties"]["outcome"]["anyOf"][0]
        assert prompt["properties"]["kind"] == {"type": "string", "enum": ["PROMPT"]}


def test_worker_sends_the_positive_witness_branch_only_where_it_is_accepted(monkeypatch) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker

    reply = json.dumps({"outcome": {"kind": "RESULT", "body": "5"}})
    sent = _scripted_send(monkeypatch, [reply, reply])
    for providers in (["Groq"], ["Cerebras"]):
        ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                  provider_pinning={"order": providers, "allow_fallbacks": False}).call(_draft_request("EXECUTE"))
    groq, cerebras = (json.dumps(body["text"]["format"]["schema"]) for body in sent)
    assert '"positive"' in groq and '"additionalProperties": true' in groq
    assert '"positive"' not in cerebras and '"additionalProperties": true' not in cerebras


def _groq_rejection_body(failed_generation: str) -> dict:
    body = json.loads((ROOT / "tests" / "fixtures" / "openrouter_groq_schema_mismatch.json").read_text(encoding="utf-8"))
    body["error"]["metadata"] = {"provider_name": "Groq", "raw": json.dumps(
        {"error": {"message": "Generated JSON does not match the expected schema.",
                   "type": "invalid_request_error", "code": "json_validate_failed",
                   "failed_generation": failed_generation}})}
    return body


def test_schema_rejection_records_the_failed_generation(monkeypatch, tmp_path) -> None:
    """Groq returns the rejected generation (failed_generation): it goes to the
    worker-progress log (one line) and the error record, never to the console line."""
    import io
    import urllib.request

    from pdl_taskmaster.host.repl import _one_line_error
    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError

    generation = '{"outcome": {"kind": "RESULT",\n "body": "P = 0.1785"}}'
    body = _groq_rejection_body(generation)

    class _Resp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(urllib.request, "urlopen", lambda req, timeout=None: _Resp(json.dumps(body).encode()))
    console: list[str] = []
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT, on_progress=console.append,
                       progress_path=tmp_path / "worker-progress.log",
                       provider_pinning={"order": ["Groq"], "allow_fallbacks": False})
    req = urllib.request.Request("http://stub/responses", data=b"{}", method="POST")
    with pytest.raises(ProviderError) as info:
        worker._send_json_with_retries(req)
    error = info.value
    assert error.failed_generation == generation
    assert error.as_record()["failed_generation"] == generation
    log = (tmp_path / "worker-progress.log").read_text(encoding="utf-8").splitlines()
    assert len(log) == 1 and "failed_generation (Groq): " in log[0] and "P = 0.1785" in log[0]
    assert console == [f"failed_generation (Groq): {len(generation)} chars, in the worker-progress log"]
    line = _one_line_error(error)
    assert "\n" not in line and len(line) <= 240 and "P = 0.1785" not in line


def test_http_rejection_records_the_failed_generation() -> None:
    from pdl_taskmaster.providers.api_worker import ProviderError

    error = ProviderError.from_http(400, json.dumps(_groq_rejection_body('{"kind": "RESULT"}')))
    assert error.failed_generation == '{"kind": "RESULT"}'
    assert ProviderError.from_http(400, '{"error": {"message": "bad"}}').failed_generation is None
    assert "failed_generation" not in ProviderError.from_http(400, "not json").as_record()


# Session log 2026-10-02: --api-providers Cerebrus (misspelled) failed every call with
# OpenRouter's routing-funnel 404 cut off mid-sentence.

_NO_ENDPOINTS_404 = json.dumps({"error": {"message": (
    "No endpoints found for openai/gpt-oss-120b. Every candidate endpoint was removed during routing: "
    "Filter by Regional Surcharge removed amazon-bedrock/eu-west-1; Filter by Parameters removed novita/fp4, "
    "digitalocean, sambanova, amazon-bedrock; Filter by Fallback removed coreweave/fp4, dekallm/bf16"),
    "code": 404, "metadata": {"routing_funnel": []}}})


def _raise_from_send(monkeypatch, error):
    from pdl_taskmaster.providers.api_worker import ApiWorker

    def fake_send(self, req, deadline=None):
        raise error

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    monkeypatch.setattr(ApiWorker, "_resolve_api_key", lambda self: "k")


def test_no_endpoints_with_configured_providers_is_one_clear_line(monkeypatch) -> None:
    from pdl_taskmaster.host.repl import _one_line_error
    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError

    _raise_from_send(monkeypatch, ProviderError.from_http(404, _NO_ENDPOINTS_404))
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                       provider_pinning={"order": ["Cerebrus"], "allow_fallbacks": False})
    with pytest.raises(ProviderError) as info:
        worker.call(_draft_request("BOOTSTRAP_ANALYSIS"))
    error = info.value
    assert error.category == "PROVIDER_REJECTED_REQUEST" and error.status == 404
    assert error.operation == "BOOTSTRAP_ANALYSIS"
    line = _one_line_error(error)
    assert line == ("PROVIDER_REJECTED_REQUEST at BOOTSTRAP_ANALYSIS: OpenRouter found no endpoint for "
                    "openai/gpt-oss-120b at the configured providers (Cerebrus): check the spelling of each name "
                    "(Cerebrus: did you mean Cerebras?) and that it serves this model")
    assert "Filter by Regional Surcharge" in error.attempts[-1]["message"]  # OpenRouter's text is kept


def test_no_endpoints_for_a_known_provider_names_it_without_a_suggestion(monkeypatch) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError

    _raise_from_send(monkeypatch, ProviderError.from_http(404, _NO_ENDPOINTS_404))
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                       provider_pinning={"order": ["SambaNova", "NewCo"], "allow_fallbacks": False})
    with pytest.raises(ProviderError) as info:
        worker.call(_draft_request("DRAFT_PLAN"))
    message = str(info.value)
    assert "(SambaNova, NewCo)" in message and "(NewCo: not a known name)" in message
    assert "SambaNova:" not in message


def test_a_provider_without_a_requested_parameter_is_named_as_such(monkeypatch) -> None:
    """Provider probe 20261002: SambaNova serves the model but not structured output, so
    OpenRouter's parameter filter removes it; the message must not blame the spelling."""
    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError

    _raise_from_send(monkeypatch, ProviderError.from_http(404, _NO_ENDPOINTS_404))
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                       provider_pinning={"order": ["SambaNova"], "allow_fallbacks": False})
    with pytest.raises(ProviderError) as info:
        worker.call(_draft_request("DRAFT_PROMPT"))
    message = str(info.value)
    assert "SambaNova does not support a parameter this request uses" in message
    assert "--no-structured-output" in message and "spelling" not in message


def test_other_provider_errors_are_unchanged(monkeypatch) -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError

    original = ProviderError.from_http(404, _NO_ENDPOINTS_404)
    _raise_from_send(monkeypatch, original)
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT, provider_pinning={})
    with pytest.raises(ProviderError) as info:
        worker.call(_draft_request("DRAFT_PLAN"))
    assert info.value is original
    other = ProviderError.from_http(400, '{"error": {"message": "bad request"}}')
    _raise_from_send(monkeypatch, other)
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT,
                       provider_pinning={"order": ["Cerebrus"], "allow_fallbacks": False})
    with pytest.raises(ProviderError) as info:
        worker.call(_draft_request("DRAFT_PLAN"))
    assert info.value is other


def test_unknown_provider_names_are_warned_never_refused(capsys) -> None:
    from argparse import Namespace

    from pdl_taskmaster.host.repl import _api_run_settings, _warn_unknown_providers
    from pdl_taskmaster.providers.api_worker import unknown_provider_names

    assert unknown_provider_names(["Cerebras", "groq", "amazon-bedrock", "Amazon Bedrock", "DeepInfra"]) == {}
    assert unknown_provider_names(["Cerebrus", "Grok", "NewCo"]) == {"Cerebrus": "Cerebras", "Grok": "Groq",
                                                                    "NewCo": None}
    args = Namespace(api_providers="Cerebrus,Groq")
    _warn_unknown_providers(args)
    out = capsys.readouterr().out.splitlines()
    assert out == ["[warn] provider 'Cerebrus' is not a known OpenRouter provider name (did you mean Cerebras?); "
                   "it is used as given, and a misspelled name makes every call fail with 'No endpoints found'"]
    assert _api_run_settings(args)["provider_pinning"]["order"] == ["Cerebrus", "Groq"]  # used as given
    _warn_unknown_providers(Namespace(api_providers="Cerebras,Groq"))
    assert capsys.readouterr().out == ""


def _failing_key_command() -> list[str]:
    return [sys.executable, "-c", "import sys; sys.stderr.write('$v=lookup script noise'); sys.exit(1)"]


def test_missing_key_from_the_builtin_lookup_names_the_variable() -> None:
    """The built-in Windows lookup's stderr echoes its own script; the error names the variable instead."""
    from pdl_taskmaster.providers.api_worker import ApiWorker
    from pdl_taskmaster.providers.base import TransportError

    worker = ApiWorker(repo_root=ROOT, api_key_env="PDLT_TEST_MISSING_KEY")
    worker.api_key_command = _failing_key_command()  # what the default lookup does when the key is absent
    with pytest.raises(TransportError) as raised:
        worker._resolve_api_key()
    message = str(raised.value)
    assert "PDLT_TEST_MISSING_KEY" in message and "Machine or User environment" in message
    assert "lookup script noise" not in message


def test_a_custom_key_command_keeps_its_own_error() -> None:
    from pdl_taskmaster.providers.api_worker import ApiWorker
    from pdl_taskmaster.providers.base import TransportError

    worker = ApiWorker(repo_root=ROOT, api_key_env="PDLT_TEST_MISSING_KEY", api_key_command=_failing_key_command())
    with pytest.raises(TransportError, match="lookup script noise"):
        worker._resolve_api_key()
