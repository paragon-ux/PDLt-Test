"""F5: validate actual provider rounds, without assuming every registered operation runs."""
import pytest

from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError
from pdl_taskmaster import api
from pdl_taskmaster.runtime.run_settings import RunSettings
from test_api import ROOT, ScriptedWorker
from test_l153_modes import GatewaySys1
from test_l122_provider_compat import (_Sent, _Sandbox, _host, _listed, _request, _worker)


@pytest.mark.parametrize("operation", ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED", "EXECUTE", "DIRECT_ANSWER"])
def test_a_request_without_tools_does_not_require_tools(monkeypatch, operation):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-tools")
    with pytest.raises(_Sent):
        worker.call(_request(operation))
    assert len(sent) == 1 and "tools" not in sent[0]


def test_unused_override_models_cannot_reject_a_direct_request(monkeypatch):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-tools", model_by_operation={"EXECUTE": "missing/unused"})
    with pytest.raises(_Sent):
        worker.call(_request("DIRECT_ANSWER"))
    assert sent[0]["model"] == "plain/no-tools" and "text" not in sent[0]


def test_same_model_is_rechecked_when_later_request_adds_tools(monkeypatch):
    reads = _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-tools")
    with pytest.raises(_Sent):
        worker.call(_request())
    request = _request()
    request.tools = _host(_Sandbox())
    with pytest.raises(ProviderError, match="does not support 'tools'"):
        worker.call(request)
    assert len(sent) == 1 and len(reads) == 1  # cached metadata, new requirements still checked


@pytest.mark.parametrize("worker_default, explicit, tools_required", [
    (False, True, True), (True, False, False), (False, None, False),
])
def test_public_settings_resolve_tools_before_the_provider(tmp_path, monkeypatch, worker_default, explicit,
                                                         tools_required):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-reasoning", agent_tools=worker_default)
    settings = RunSettings(mode="saver", agent_tools=explicit)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, settings=settings,
                          sys1=GatewaySys1(problem_class="VERIFIED_EXECUTION")) as session:
        with pytest.raises(_Sent):
            session.send("Deliver the requested example.")
    assert sent
    assert all(bool(body.get("tools")) is tools_required for body in sent)
    assert all("text" not in body for body in sent)  # bootstrap has no output format


def test_explicit_session_tools_cannot_bypass_capability_validation(tmp_path, monkeypatch):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-tools", agent_tools=False)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT,
                          settings=RunSettings(mode="saver", agent_tools=True),
                          sys1=GatewaySys1(problem_class="VERIFIED_EXECUTION")) as session:
        with pytest.raises(ProviderError, match="does not support 'tools'"):
            session.send("Deliver the requested example.")
    assert not sent


def test_tool_round_and_formatted_fallback_are_checked_separately(monkeypatch):
    model = "openai/gpt-oss-120b"  # recorded family uses JSON mode for EXECUTE
    _listed(monkeypatch, {model: {"id": model, "supported_parameters": ["tools", "reasoning"]}})
    worker, _ = _worker(monkeypatch, model)
    sent = []

    def reply(self, request, deadline=None):
        import json
        sent.append(json.loads(request.data))
        return {"output": [{"type": "message", "content": [{"type": "output_text", "text": "no submission"}]}]}

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", reply)
    request = _request("EXECUTE_UNCONFIRMED")
    request.tools = _host(_Sandbox())
    with pytest.raises(ProviderError, match="does not support 'response_format'"):
        worker.call(request)
    assert len(sent) == 1 and sent[0]["tools"] and "text" not in sent[0]


def test_selected_override_is_validated_before_send(monkeypatch):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-tools", model_by_operation={"DIRECT_ANSWER": "missing/selected"})
    with pytest.raises(ProviderError, match="not in OpenRouter's model list"):
        worker.call(_request("DIRECT_ANSWER"))
    assert not sent


@pytest.mark.parametrize("mode, problem_class, exclusions, tools_required", [
    ("protocol", "STANDARD_EXECUTION", (), False),
    ("direct", "STANDARD_EXECUTION", (), False),
    ("saver", "STANDARD_EXECUTION", (), False),
    ("saver", "VERIFIED_EXECUTION", (), True),
    ("saver", "VERIFIED_EXECUTION", ("submit_bootstrap_analysis",), False),
])
def test_public_routes_validate_only_the_attached_features(tmp_path, monkeypatch, mode, problem_class, exclusions,
                                                          tools_required):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-tools")
    settings = RunSettings(mode=mode, agent_tools_exclude=exclusions)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, settings=settings,
                          sys1=GatewaySys1(problem_class=problem_class)) as session:
        expected = ProviderError if tools_required else _Sent
        with pytest.raises(expected):
            session.send("Deliver the requested example.")
    assert not sent if tools_required else len(sent) == 1 and "tools" not in sent[0]


@pytest.mark.parametrize("enabled, exclusions, tools_required", [
    (False, (), False), (True, (), True),
    (True, ("read_attempt", "run_python", "submit_execute"), False),
])
def test_confirmed_execute_uses_its_actual_flag_and_exclusions(tmp_path, monkeypatch, enabled, exclusions, tools_required):
    _listed(monkeypatch)
    worker, sent = _worker(monkeypatch, "plain/no-tools")
    original_call = worker.call
    scripted = ScriptedWorker()

    def call(request):
        # Earlier stages are scripted; the real confirmed EXECUTE request crosses the provider boundary.
        return original_call(request) if request.operation == "EXECUTE" else scripted.call(request)

    monkeypatch.setattr(worker, "call", call)
    settings = RunSettings(mode="protocol", no_review=False, confirmed_execute_tools=enabled,
                           agent_tools_exclude=exclusions)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, settings=settings,
                          sys1=GatewaySys1()) as session:
        with pytest.raises(ProviderError if tools_required else _Sent):
            session.run("Deliver the requested example.", confirm=True)
    assert not sent if tools_required else len(sent) == 1 and "tools" not in sent[0]
