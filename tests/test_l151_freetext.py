"""L151 step 2 (the user, 2026-10-22): the freetext part, a measurement that ships nothing. EXECUTE_UNCONFIRMED is
asked for the same fields as headed plain-text sections instead of a JSON object: the worker instructions' format
lines are replaced, the JSON-only suffix and the output format are left out, and the guidance names the headings.
The host turns the reply into the outcome object, which is validated as any reply is. Without the part every request
is unchanged (the parity goldens hold). Offline; the worker, the transport and System 1 are scripted."""
from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from pdl_taskmaster.providers import api_worker
from pdl_taskmaster.providers.api_worker import ApiWorker, freetext_outcome
from pdl_taskmaster.runtime.run_settings import RunSettings
from pdl_taskmaster.runtime.wire_payloads import UnconfirmedExecutionRequestInputData, UnconfirmedExecutionResultData
from test_l149_ablation import MODEL, ROOT, _body, _requests

REPLY = ("INTERPRETATION:\nDETERMINE x FROM the two equations\n\nAPPROACH:\nADD the equations\nSOLVE for x\n\n"
         "KIND: RESULT\n\nBODY:\nAdding gives 2x = 12, so x = 6.\nAPPROACH: a line in the body stays in the body.")


@pytest.fixture(scope="module")
def calls(tmp_path_factory):
    return (_requests(tmp_path_factory.mktemp("base")),
            _requests(tmp_path_factory.mktemp("freetext"), ("freetext",)))


def test_only_the_format_of_execute_unconfirmed_changes(calls):
    base, free = calls
    assert free["BOOTSTRAP_ANALYSIS"].prompt == base["BOOTSTRAP_ANALYSIS"].prompt
    assert _body(free["BOOTSTRAP_ANALYSIS"]) == _body(base["BOOTSTRAP_ANALYSIS"])
    assert free["EXECUTE_UNCONFIRMED"].prompt == base["EXECUTE_UNCONFIRMED"].prompt  # what is asked is unchanged


def test_the_request_asks_for_plain_text(calls):
    base, free = (_body(c["EXECUTE_UNCONFIRMED"]) for c in calls)
    assert base["text"] == {"format": {"type": "json_object"}} and "text" not in free
    assert base["input"].endswith(api_worker._JSON_ONLY_SUFFIX) and "JSON" not in free["input"][-200:]
    assert base["input"].startswith(free["input"])
    assert api_worker._BOOTSTRAP_JSON_LINES in base["instructions"]
    assert api_worker._BOOTSTRAP_JSON_LINES not in free["instructions"]
    assert api_worker._BOOTSTRAP_FREETEXT_LINES in free["instructions"]
    assert free["instructions"].endswith(api_worker._UNCONFIRMED_FREETEXT)
    assert free["instructions"].replace(api_worker._BOOTSTRAP_FREETEXT_LINES, api_worker._BOOTSTRAP_JSON_LINES) \
        == base["instructions"] + "\n" + api_worker._UNCONFIRMED_FREETEXT
    assert {k: v for k, v in free.items() if k not in ("input", "instructions")} \
        == {k: v for k, v in base.items() if k not in ("input", "instructions", "text")}


def test_a_sectioned_reply_becomes_a_valid_outcome():
    text, read = freetext_outcome(REPLY)
    outcome = json.loads(text)
    assert read == "sections"
    assert outcome == {"kind": "RESULT", "interpretation": "DETERMINE x FROM the two equations",
                       "approach": "ADD the equations\nSOLVE for x",
                       "body": "Adding gives 2x = 12, so x = 6.\nAPPROACH: a line in the body stays in the body."}
    UnconfirmedExecutionResultData.model_validate(outcome)


def test_markdown_headings_and_same_line_values_are_read():
    reply = "**INTERPRETATION:** read it\n## APPROACH:\nplan it\n**KIND:** `RESULT`\n**BODY:**\n\nThe answer."
    outcome = json.loads(freetext_outcome(reply)[0])
    assert outcome == {"kind": "RESULT", "interpretation": "read it", "approach": "plan it", "body": "The answer."}


def test_a_request_for_input_carries_its_expected_type():
    reply = "INTERPRETATION: i\nAPPROACH: a\nKIND: REQUEST_INPUT\nEXPECTED_TYPE: a CSV file\nBODY:\nPlease supply it."
    outcome = json.loads(freetext_outcome(reply)[0])
    assert outcome["kind"] == "REQUEST_INPUT" and outcome["expected_type"] == "a CSV file"
    UnconfirmedExecutionRequestInputData.model_validate(outcome)


def test_without_a_body_heading_the_whole_reply_is_the_body():
    text, read = freetext_outcome("The answer is 6.")
    assert read == "no_body_heading"
    assert json.loads(text) == {"kind": "RESULT", "interpretation": "", "approach": "", "body": "The answer is 6."}


def test_an_unknown_kind_is_left_for_the_verifier_to_reject():
    outcome = json.loads(freetext_outcome("KIND: MAYBE\nBODY:\nx")[0])
    assert outcome["kind"] == "MAYBE"
    with pytest.raises(ValueError):
        UnconfirmedExecutionResultData.model_validate(outcome)


def test_the_worker_returns_the_outcome_object(calls, monkeypatch):
    sent = []

    def fake_send(self, request, deadline):
        sent.append(json.loads(request.data.decode("utf-8")))
        return {"id": "gen-1", "model": "m", "usage": {"input_tokens": 10, "output_tokens": 5},
                "output": [{"type": "message", "content": [{"type": "output_text", "text": REPLY}]}]}

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    result = ApiWorker(repo_root=ROOT, model=MODEL)._call(calls[1]["EXECUTE_UNCONFIRMED"])
    assert "text" not in sent[0]
    assert json.loads(result.text)["body"].startswith("Adding gives 2x = 12")
    assert result.metadata["freetext_read"] == "sections"


def test_freetext_does_not_combine_with_the_result_ir(calls):
    request = calls[1]["EXECUTE_UNCONFIRMED"]
    manifest = {**request.projection.manifest, "modes": [*request.projection.manifest["modes"], "result_ir"]}
    changed = dataclasses.replace(request, projection=dataclasses.replace(request.projection, manifest=manifest))
    with pytest.raises(ValueError, match="result IR"):
        _body(changed)


def test_run_settings_accept_the_part():
    assert RunSettings(ablate_unconfirmed=("freetext",)).ablate_unconfirmed == ("freetext",)
