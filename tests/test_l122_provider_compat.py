"""L122: PDLt's requests are not tuned to one model.

- A model without a recorded reasoning profile gets no reasoning setting unless one is given.
- Every request to OpenRouter carries PDLt's own attribution headers.
- Before its first call, each model's supported parameters (OpenRouter's model list) are checked against what
  the session will send it; a mismatch fails closed with one clear line and no request sent.
- Work-tool arguments and submissions are validated as strictly as replies (L121 flag I-2).
"""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pdl_taskmaster.providers import model_capabilities
from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError
from pdl_taskmaster.runtime import agent_tools
from pdl_taskmaster.runtime.model_classification import get_proportional_reasoning_mapping, resolve_reasoning

ROOT = Path(__file__).resolve().parents[1]
LFM = "liquid/lfm-2.5-2.6b:free"
INKLING = "thinkingmachines/inkling-small:free"
NEMOTRON = "nvidia/nemotron-3-super-120b-a12b:free"

# supported_parameters as OpenRouter listed them on 2026-10-15 (GET /api/v1/models).
MODEL_LIST = {
    LFM: {"id": LFM, "supported_parameters": [
        "frequency_penalty", "include_reasoning", "logprobs", "max_completion_tokens", "max_tokens", "min_p",
        "presence_penalty", "reasoning", "repetition_penalty", "response_format", "seed", "stop",
        "structured_outputs", "temperature", "tool_choice", "tools", "top_k", "top_logprobs"],
          "top_provider": {"max_completion_tokens": 8192}},
    INKLING: {"id": INKLING, "supported_parameters": [
        "frequency_penalty", "include_reasoning", "max_tokens", "presence_penalty", "reasoning",
        "reasoning_effort", "seed", "stop", "temperature", "tools", "top_p"]},
    NEMOTRON: {"id": NEMOTRON, "supported_parameters": [
        "include_reasoning", "max_tokens", "reasoning", "reasoning_effort", "response_format", "seed",
        "structured_outputs", "temperature", "tool_choice", "tools", "top_p"]},
    "plain/no-reasoning": {"id": "plain/no-reasoning", "supported_parameters": [
        "response_format", "structured_outputs", "tools"]},
    "plain/no-tools": {"id": "plain/no-tools", "supported_parameters": ["response_format", "structured_outputs"]},
    "plain/json-only": {"id": "plain/json-only", "supported_parameters": ["response_format"]},
}


class _Sent(Exception):
    """Raised by the fake transport: the check passed and a request was about to go out."""


def _worker(monkeypatch, model, **kwargs):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    worker = ApiWorker(model=model, repo_root=ROOT, **kwargs)
    sent = []

    def fake_send(self, req, deadline=None):
        sent.append(json.loads(req.data))
        raise _Sent()

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    return worker, sent


def _listed(monkeypatch, models=MODEL_LIST):
    reads = []

    def model_list(base_url, timeout):
        reads.append(base_url)
        return dict(models)

    monkeypatch.setattr(model_capabilities, "model_list", model_list)
    return reads


def _request(operation="BOOTSTRAP_ANALYSIS"):
    return SimpleNamespace(operation=operation, prompt="Analyse this task.")


# 1. Reasoning: omitted unless set, for a model without a recorded profile.

@pytest.mark.parametrize("model", [LFM, INKLING, "some-lab/other-model"])
def test_a_model_without_a_profile_sends_no_reasoning(model):
    assert resolve_reasoning(model) == (None, {})
    worker = ApiWorker(model=model, repo_root=ROOT)
    for operation in ("BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "EXECUTE_UNCONFIRMED"):
        body, _, effort = worker.build_request_body(_request(operation))
        assert "reasoning" not in body and effort is None, operation


def test_an_explicit_effort_is_sent():
    worker = ApiWorker(model=LFM, repo_root=ROOT, reasoning_effort="low")
    assert worker.build_request_body(_request())[0]["reasoning"] == {"effort": "low"}
    by_op = ApiWorker(model=LFM, repo_root=ROOT, reasoning_by_operation={"EXECUTE_UNCONFIRMED": "high"})
    assert by_op.build_request_body(_request("EXECUTE_UNCONFIRMED"))[0]["reasoning"] == {"effort": "high"}
    assert "reasoning" not in by_op.build_request_body(_request())[0]


def test_recorded_profiles_are_unchanged():
    assert get_proportional_reasoning_mapping(NEMOTRON) == get_proportional_reasoning_mapping("openai/gpt-oss-120b")
    assert get_proportional_reasoning_mapping(NEMOTRON)["BOOTSTRAP_ANALYSIS"] == "low"  # L155
    default, _ = resolve_reasoning(NEMOTRON)
    assert default == "low"


# 2. Attribution headers.

def test_requests_carry_pdlts_attribution_headers():
    worker = ApiWorker(model=LFM, repo_root=ROOT)
    headers = {key.lower(): value for key, value in worker._responses_request({}, "k").header_items()}
    assert headers["x-title"] == "PDLt"
    assert headers["http-referer"].startswith("https://github.com/")


def test_system1_requests_carry_them_too(monkeypatch):
    from pdl_taskmaster.providers.sys1 import client as sys1_client
    from pdl_taskmaster.providers.sys1.schema import Sys1Request

    seen = {}

    def urlopen(req, timeout=None):
        seen.update({key.lower(): value for key, value in req.header_items()})
        raise _Sent()

    monkeypatch.setattr(sys1_client.urllib.request, "urlopen", urlopen)
    client = sys1_client.Sys1Client(api_key="k", endpoint="https://openrouter.ai/api/alpha/decisions", model="m")
    with pytest.raises(Exception):
        client.call(Sys1Request(state={}, questions={}))
    assert seen["x-title"] == "PDLt" and "http-referer" in seen


# 3. Capability check.

def test_a_model_that_lacks_a_parameter_fails_closed_before_any_request(monkeypatch):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-reasoning", reasoning_effort="high")
    with pytest.raises(ProviderError) as caught:
        worker.call(_request())
    assert caught.value.category == "MODEL_UNSUPPORTED" and caught.value.operation == "BOOTSTRAP_ANALYSIS"
    message = str(caught.value)
    assert "'reasoning'" in message and "--api-reasoning-effort" in message and "No request was sent" in message
    assert sent == []


def test_a_model_without_output_formats_is_served_without_one(monkeypatch):
    # Inkling lists neither response_format nor structured_outputs: adapted to, never excluded (ADR-0028 rule 5);
    # the host still validates every reply.
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, INKLING)
    with pytest.raises(_Sent):
        worker.call(_request("EXECUTE_UNCONFIRMED"))
    assert "text" not in sent[0] and "provider" not in sent[0]


def test_a_model_that_supports_the_session_passes(monkeypatch):
    reads = _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, LFM, agent_tools=True)
    for _ in range(2):
        with pytest.raises(_Sent):
            worker.call(_request())
    assert len(sent) == 2 and len(reads) == 1  # checked once per model


def test_the_check_follows_the_settings(monkeypatch):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, INKLING, structured_output=False)
    with pytest.raises(_Sent):
        worker.call(_request())
    no_reasoning, _ = _worker(monkeypatch, "plain/no-reasoning", reasoning_effort="high")
    with pytest.raises(ProviderError, match="'reasoning'.*--api-reasoning-effort"):
        no_reasoning.call(_request())
    no_tools, _ = _worker(monkeypatch, "plain/no-tools", agent_tools=True)
    with pytest.raises(ProviderError, match="'tools'.*without --agent-tools"):
        no_tools.call(_request())


def test_an_unlisted_model_fails_closed(monkeypatch):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "nobody/misspelt-model")
    with pytest.raises(ProviderError, match="not in OpenRouter's model list") as caught:
        worker.call(_request())
    assert caught.value.category == "MODEL_UNSUPPORTED" and sent == []


def test_an_unreadable_list_fails_closed(monkeypatch):
    def unreadable(base_url, timeout):
        raise OSError("connection refused")

    monkeypatch.setattr(model_capabilities, "model_list", unreadable)
    worker, sent = _worker(monkeypatch, LFM)
    with pytest.raises(ProviderError) as caught:
        worker.call(_request())
    assert caught.value.category == "MODEL_CAPABILITY_UNKNOWN" and sent == []


def test_other_endpoints_are_not_checked(monkeypatch):
    reads = _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, INKLING, base_url="https://example.invalid/v1")
    with pytest.raises(_Sent):
        worker.call(_request())
    assert reads == []


def test_free_variants_never_fall_back_to_the_paid_model():
    models = {"lab/model": {"id": "lab/model"}}
    assert model_capabilities.lookup(models, "lab/model:nitro") == {"id": "lab/model"}
    assert model_capabilities.lookup(models, "lab/model:free") is None


# 4. Tool arguments as strict as replies.

class _Sandbox:
    def __init__(self):
        self.runs = []

    def run_code(self, code, **kwargs):
        self.runs.append(code)
        return SimpleNamespace(exit_code=0, steps_used=1, step_budget_exceeded=False, timed_out=False,
                               stdout="1\n", stderr="")


def _host(sandbox, validate=lambda outcome: ([], [])):
    return agent_tools.ToolHost(sandbox, 10, 1.0, 1, ["print(1)"], "OPERATOR CORRECTION: c", validate)


@pytest.mark.parametrize("name, arguments", [
    ("run_python", '{"code": "print(1)", "timeout": 99}'),
    ("run_python", '{"code": 5}'),
    ("run_python", "{}"),
    ("run_python", "[]"),
    ("run_python", "not json"),
    ("read_attempt", '{"n": 1}'),
])
def test_work_tool_arguments_outside_the_schema_are_refused(name, arguments):
    sandbox = _Sandbox()
    output = _host(sandbox).dispatch(name, arguments)
    assert output.startswith(f"error: the arguments do not match {name}'s input schema") and "nothing ran" in output
    assert sandbox.runs == []


def test_valid_work_tool_arguments_run():
    sandbox = _Sandbox()
    host = _host(sandbox)
    host.dispatch("run_python", '{"code": "print(1)"}')
    assert sandbox.runs == ["print(1)"]
    assert "print(1)" in host.dispatch("read_attempt", "{}")


def test_argument_models_match_the_published_input_schemas():
    for tool in agent_tools.TOOLS:
        model = agent_tools.ARGUMENT_MODELS.get(tool["name"])
        if model is None:
            continue
        schema = model.model_json_schema()
        assert set(schema.get("properties", {})) == set(tool["inputSchema"]["properties"]), tool["name"]
        assert set(schema.get("required", [])) == set(tool["inputSchema"].get("required", [])), tool["name"]
        assert tool["inputSchema"]["additionalProperties"] is False


def test_a_submission_with_fields_beside_outcome_is_refused():
    checked = []
    host = _host(None, validate=lambda outcome: (checked.append(outcome), ([], []))[1])
    envelope, accepted = host.submit('{"outcome": {"kind": "RESULT"}, "note": "x"}')
    assert accepted is None and envelope["ok"] is False and checked == []
    assert "fields beside outcome: note" in envelope["errors"][0]["problem"]
    envelope, accepted = host.submit('{"outcome": {"kind": "RESULT"}}')
    assert accepted == {"kind": "RESULT"} and checked == [{"kind": "RESULT"}]


# 5. Request settings per model: a recorded profile or the model's metadata, never one model's defaults for all.

def _body(worker, operation):
    return worker.build_request_body(_request(operation))[0]


def test_a_structured_outputs_model_gets_a_strict_schema_at_execute(monkeypatch):
    _listed(monkeypatch)
    worker = ApiWorker(model=LFM, repo_root=ROOT)
    for operation in ("EXECUTE_UNCONFIRMED", "EXECUTE"):
        body = _body(worker, operation)
        fmt = body["text"]["format"]
        assert fmt["type"] == "json_schema" and fmt["strict"] is True, operation
        assert body["provider"] == {"require_parameters": True}, operation  # no recorded order for this model
    draft = _body(worker, "DRAFT_PROMPT")
    assert draft["text"]["format"]["type"] == "json_schema" and "strict" not in draft["text"]["format"]
    assert draft["provider"] == {"require_parameters": True}


def test_a_json_only_model_keeps_json_mode(monkeypatch):
    _listed(monkeypatch)
    worker = ApiWorker(model="plain/json-only", repo_root=ROOT)
    for operation in ("EXECUTE_UNCONFIRMED", "DRAFT_PROMPT"):
        body = _body(worker, operation)
        assert body["text"] == {"format": {"type": "json_object"}} and "provider" not in body, operation


@pytest.mark.parametrize("model", [NEMOTRON, "openai/gpt-oss-120b"])
def test_recorded_profiles_keep_json_mode_and_their_provider_order(monkeypatch, model):
    from pdl_taskmaster.providers.api_worker import DEFAULT_PROVIDER_PINNING

    _listed(monkeypatch, {**MODEL_LIST, "openai/gpt-oss-120b": {
        "id": "openai/gpt-oss-120b", "supported_parameters": ["reasoning", "response_format", "structured_outputs"]}})
    worker = ApiWorker(model=model, repo_root=ROOT)
    body = _body(worker, "EXECUTE_UNCONFIRMED")
    assert body["text"] == {"format": {"type": "json_object"}}
    assert body["provider"] == DEFAULT_PROVIDER_PINNING  # no require_parameters without a schema
    draft = _body(worker, "DRAFT_PLAN")
    assert draft["provider"] == {**DEFAULT_PROVIDER_PINNING, "require_parameters": True}


def test_unknown_metadata_keeps_the_earlier_forms():
    worker = ApiWorker(model=LFM, repo_root=ROOT, base_url="https://example.invalid/v1")
    assert _body(worker, "EXECUTE_UNCONFIRMED")["text"] == {"format": {"type": "json_object"}}
    assert _body(worker, "DRAFT_PROMPT")["text"]["format"]["type"] == "json_schema"


def test_safety_settings_are_sent_only_when_configured(monkeypatch):
    from pdl_taskmaster.providers.api_worker import DEFAULT_SAFETY_SETTINGS

    _listed(monkeypatch)
    for model in (LFM, NEMOTRON):
        assert "safety_settings" not in _body(ApiWorker(model=model, repo_root=ROOT), "BOOTSTRAP_ANALYSIS")
    configured = ApiWorker(model=LFM, repo_root=ROOT, safety_settings=DEFAULT_SAFETY_SETTINGS)
    assert _body(configured, "BOOTSTRAP_ANALYSIS")["safety_settings"] == DEFAULT_SAFETY_SETTINGS


def test_the_output_cap_is_capped_at_the_listed_maximum(monkeypatch):
    _listed(monkeypatch)
    assert _body(ApiWorker(model=LFM, repo_root=ROOT), "BOOTSTRAP_ANALYSIS")["max_output_tokens"] == 8192
    assert _body(ApiWorker(model=LFM, repo_root=ROOT, max_output_tokens=4000),
                 "BOOTSTRAP_ANALYSIS")["max_output_tokens"] == 4000
    assert _body(ApiWorker(model=NEMOTRON, repo_root=ROOT), "BOOTSTRAP_ANALYSIS")["max_output_tokens"] == 16384


def test_a_configured_provider_order_applies_to_every_model(monkeypatch):
    _listed(monkeypatch)
    pinned = ApiWorker(model=LFM, repo_root=ROOT, provider_pinning={"order": ["Chutes"], "allow_fallbacks": False})
    assert _body(pinned, "BOOTSTRAP_ANALYSIS")["provider"] == {"order": ["Chutes"], "allow_fallbacks": False}
    monkeypatch.setenv("OPENROUTER_PROVIDER_ORDER", "Liquid")
    from_env = ApiWorker(model=LFM, repo_root=ROOT)
    assert _body(from_env, "BOOTSTRAP_ANALYSIS")["provider"]["order"] == ["Liquid"]
    from_env.provider_pinning = {**from_env.provider_pinning, "allow_fallbacks": False}  # the dev command's form
    assert _body(from_env, "BOOTSTRAP_ANALYSIS")["provider"] == {"order": ["Liquid"], "allow_fallbacks": False}


def test_the_schema_fallback_drops_require_parameters_with_the_schema(monkeypatch):
    _listed(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    worker = ApiWorker(model=LFM, repo_root=ROOT)
    body = _body(worker, "EXECUTE_UNCONFIRMED")
    sent = []

    def fake_send(self, req, deadline=None):
        sent.append(json.loads(req.data))
        return {"output": []}

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    worker._schema_rejection_fallback(body, "k", ProviderError("PROVIDER_REJECTED_REQUEST", "schema"), 0.0, True)
    assert "text" not in sent[-1] and "provider" not in sent[-1]
