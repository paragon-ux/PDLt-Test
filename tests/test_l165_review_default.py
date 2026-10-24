"""L165: no review is the default in every interface, and review is the confirmed route, in protocol mode. With no
mode given, review selects protocol; review with direct or saver is refused, since neither has review. Offline."""
from __future__ import annotations

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.host import repl
from pdl_taskmaster.runtime.run_settings import RunSettings, check_review_mode, default_mode

from test_adr0031_defaults import _api_worker
from test_api import ROOT


def test_no_review_is_the_default_everywhere(monkeypatch):
    monkeypatch.delenv("PDLT_AGENT_TOOLS", raising=False)
    assert RunSettings().no_review is True
    settings = repl._run_settings(repl._build_parser().parse_args([]), _api_worker())
    assert (settings.mode, settings.no_review) == ("saver", True)


@pytest.mark.parametrize("argv", [["--review"], ["--fast"]])
def test_review_with_no_mode_runs_the_confirmed_route_in_protocol_mode(argv):
    args = repl._build_parser().parse_args(argv)
    if args.fast:
        args.no_review = False  # as main() does
    settings = repl._run_settings(args, _api_worker())
    assert (settings.mode, settings.no_review) == ("protocol", False)


def test_review_with_direct_or_saver_is_refused():
    assert default_mode(_api_worker(), review=True) == "protocol"
    check_review_mode("protocol", False)
    check_review_mode("saver", True)
    for mode in ("direct", "saver"):
        with pytest.raises(ValueError, match="review runs the confirmed route, in protocol mode"):
            check_review_mode(mode, False)


def test_the_api_opens_saver_without_review_and_protocol_with_it(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    with api.Session.open(_api_worker(), tmp_path / "a", repo_root=ROOT) as session:
        assert (session.host.engine.mode, session.host.engine.no_review) == ("saver", True)
    with api.Session.open(_api_worker(), tmp_path / "b", repo_root=ROOT, no_review=False) as session:
        assert (session.host.engine.mode, session.host.engine.no_review) == ("protocol", False)
    with pytest.raises(ValueError, match="saver mode has no review"):
        api.Session.open(_api_worker(), tmp_path / "c", repo_root=ROOT, no_review=False, mode="saver")
