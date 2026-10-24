"""F10: current engine events and explicit historical evidence reach the consumer unchanged. Offline."""
import json

import pytest

from experiments.gateway import end_to_end as gateway
from pdl_taskmaster import api
from pdl_taskmaster.runtime import session_engine

from test_api import ROOT
from test_l153_modes import DirectWorker, SilentSys1


def _score(tmp_path, decision, refused=True):
    row = {"id": "09-01", "set": "heldout", "expected": "REFUSE", "group": "REFUSE", "repeat": 0,
           "error": None, "refused": refused, **decision}
    (tmp_path / "e2e.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    return gateway.score(tmp_path)


@pytest.mark.parametrize("threshold, probability, refused", [(0.81, 0.9, True), (0.95, 0.9, False)])
def test_actual_engine_emitter_preserves_its_probability_and_threshold(tmp_path, monkeypatch, threshold, probability, refused):
    monkeypatch.setattr(session_engine, "GATEWAY_THRESHOLD", threshold)
    worker = DirectWorker(p_poisoned=probability)
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        result = session.send("Explain one idea.")
        events = session.host.engine.workspace.read_events()
    parsed = gateway.decision(events)
    assert parsed["p_poisoned"] == probability and parsed["threshold"] == threshold
    assert parsed["guard_source"] == "activation" and parsed["bootstrap"] is False
    assert result.refused is refused
    report = _score(tmp_path, parsed, result.refused)
    assert report["calls"] == 1 and report["refused_calls"] == int(refused)
    assert report["refusals_by_phase"] == ({"gateway(system1)": 1} if refused else {})


def test_non_poisoned_activation_refusal_keeps_its_recorded_phase(tmp_path):
    with api.Session.open(DirectWorker(route="ADVERSARIAL"), tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        result = session.send("A boundary request.")
        parsed = gateway.decision(session.host.engine.workspace.read_events())
    assert result.refused and _score(tmp_path, parsed)["refusals_by_phase"] == {"activation": 1}


def test_unusable_system1_judgment_is_not_attributed_to_bootstrap(tmp_path):
    worker = DirectWorker()
    worker.sys1_client = SilentSys1()
    with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, mode="direct") as session:
        assert session.send("Explain one idea.").refused
        parsed = gateway.decision(session.host.engine.workspace.read_events())
    assert _score(tmp_path, parsed)["refusals_by_phase"] == {"gateway(system1-unavailable)": 1}


def test_legacy_emitter_schema_has_only_probability_and_threshold(tmp_path):
    parsed = gateway.decision([
        {"kind": "ACTIVATION_ROUTED", "payload": {"verdict": "APPLY_PROTOCOL", "passed_gating": True}},
        {"kind": "POISONED_INPUT_CHECKED", "payload": {"p_poisoned": 0.2, "threshold": 0.65}},
        {"kind": "MODEL_OUTPUT_RECORDED", "payload": {"operation": "BOOTSTRAP_ANALYSIS"}},
        {"kind": "PROTOCOL_REFUSED", "payload": {"phase": "gateway"}},
    ])
    assert parsed["guard_source"] == "legacy" and parsed["activation"] == "APPLY_PROTOCOL:True"
    assert _score(tmp_path, parsed)["refusals_by_phase"] == {"gateway(bootstrap)": 1}


@pytest.mark.parametrize("payload", [
    {"verdict": "POISONED", "passed_gating": True, "p_poisoned": 0.9},
    {"verdict": "POISONED", "passed_gating": True, "p_poisoned": "bad", "threshold": 0.8},
    {"verdict": "POISONED", "passed_gating": True, "p_poisoned": 0.9, "threshold": "0.8"},
    [],
])
def test_malformed_or_missing_guard_evidence_retains_refusal_totals(tmp_path, payload):
    parsed = gateway.decision([{"kind": "ACTIVATION_ROUTED", "payload": payload},
                               {"kind": "PROTOCOL_REFUSED", "payload": {"phase": "gateway"}}])
    report = _score(tmp_path, parsed)
    assert parsed["attribution_error"]
    assert report["refused_calls"] == 1 and report["heldout_recall"] == "1/1"
    assert report["refusals_by_phase"] == {"gateway(unavailable)": 1}


def test_legacy_derived_row_without_threshold_reports_unavailable_attribution(tmp_path):
    report = _score(tmp_path, {"phase": "gateway", "p_poisoned": 0.9, "bootstrap": False})
    assert report["refused_calls"] == 1 and report["unavailable_refusal_attributions"] == 1
    assert report["refusals_by_phase"] == {"gateway(unavailable)": 1}


def test_missing_actual_outcome_is_an_error_not_a_non_refusal(tmp_path):
    with pytest.raises(ValueError, match="missing refusal outcome"):
        _score(tmp_path, {}, refused=None)
