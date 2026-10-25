"""PR #5 F6: equivalent public settings forms resolve the same session defaults. Offline."""
import pytest
from types import SimpleNamespace

from pdl_taskmaster import api
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.runtime.run_settings import RunSettings

from test_api import ROOT, ScriptedWorker


@pytest.mark.parametrize("values, expected", [
    ({}, ("saver", True, True)),
    ({"max_repairs": 0}, ("saver", True, True)),
    ({"mode": "protocol"}, ("protocol", True, False)),
    ({"no_review": False}, ("protocol", False, True)),
    ({"mode": "direct"}, ("direct", True, True)),
])
def test_typed_and_keyword_settings_have_the_same_effect(tmp_path, values, expected):
    keywords = {key: value for key, value in values.items() if key != "max_repairs"}
    for name, arguments in (("typed", {"settings": RunSettings(**values)}), ("keywords", keywords)):
        worker = ApiWorker(repo_root=ROOT, max_repairs=values.get("max_repairs"))
        with api.Session.open(worker, tmp_path / name, repo_root=ROOT, **arguments) as session:
            engine = session.host.engine
            assert (engine.mode, engine.no_review, engine.agent_tools) == expected


@pytest.mark.parametrize("tools", [False, True])
def test_typed_explicit_tools_win_over_the_route_and_worker_default(tmp_path, tools):
    worker = ApiWorker(repo_root=ROOT, agent_tools=not tools)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT,
                          settings=RunSettings(mode="protocol", agent_tools=tools)) as session:
        assert session.host.engine.agent_tools is tools


def test_unspecified_typed_settings_keep_recorded_worker_defaults(tmp_path):
    with api.Session.open(ScriptedWorker(), tmp_path / "s", repo_root=ROOT,
                          settings=RunSettings()) as session:
        assert (session.host.engine.mode, session.host.engine.agent_tools) == ("protocol", False)


@pytest.mark.parametrize("mode", ["saver", "direct"])
def test_an_explicit_non_protocol_review_is_still_refused(tmp_path, mode):
    with pytest.raises(ValueError, match="review runs the confirmed route"):
        api.Session.open(ApiWorker(repo_root=ROOT), tmp_path / "s", repo_root=ROOT,
                         settings=RunSettings(mode=mode, no_review=False))


@pytest.mark.parametrize("values, expected", [
    ({"withhold_execution_context": True}, ("saver", True)),
    ({"mode": "protocol"}, ("protocol", False)),
    ({"no_review": False}, ("protocol", True)),
    ({"mode": "protocol", "agent_tools": True}, ("protocol", True)),
])
def test_direct_apply_resolves_standalone_defaults_and_explicit_overrides(values, expected):
    engine = SimpleNamespace()
    RunSettings(**values).apply(engine)
    assert (engine.mode, engine.agent_tools) == expected
