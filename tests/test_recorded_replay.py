from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pdl_taskmaster.providers.fixtures import build_recorded_fixture_from_vendored, replay_request_builder
from pdl_taskmaster.providers.recorded import ReplayMissError, request_sha256
from pdl_taskmaster.verification.sandbox import PYTHON_VERSION, python_declaration

ROOT = Path(__file__).resolve().parents[1]
OTHER_PYTHON = "3.9" if PYTHON_VERSION != "3.9" else "3.8"


def _prompt(version: str) -> str:
    return f'{{"AVAILABLE_EXECUTION_TOOLS": [{{"name": "python", "description": "{python_declaration(version)}."}}]}}'


def _worker(tmp_path: Path, prompt_text: str, recorded_python: str | None):
    body = replay_request_builder(ROOT)(SimpleNamespace(operation="EXECUTE", prompt=prompt_text))
    fixture = {
        "schema": 1,
        "entries": [
            {
                "operation": "EXECUTE",
                "prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
                "prompt_text": prompt_text,
                "provider_request": body,
                "request_sha256": request_sha256(body),
                "response": "{}",
                "source": "G06:0006-execute",
            }
        ],
    }
    if recorded_python is not None:
        fixture["recorded_python"] = recorded_python
    path = tmp_path / "recorded-cases.json"
    path.write_text(json.dumps(fixture), encoding="utf-8")
    return build_recorded_fixture_from_vendored(ROOT, path)


def _call(worker, prompt: str):
    return worker.call(SimpleNamespace(operation="EXECUTE", prompt=prompt))


def test_recording_from_another_interpreter_replays_against_this_hosts_prompt(tmp_path: Path) -> None:
    worker = _worker(tmp_path, _prompt(OTHER_PYTHON), OTHER_PYTHON)
    result = _call(worker, _prompt(PYTHON_VERSION))
    assert result.metadata["recorded_python"] == OTHER_PYTHON
    with pytest.raises(ReplayMissError):
        _call(worker, _prompt(OTHER_PYTHON))  # this host never declares the recorded interpreter


def test_recording_from_this_interpreter_is_keyed_unchanged(tmp_path: Path) -> None:
    worker = _worker(tmp_path, _prompt(PYTHON_VERSION), PYTHON_VERSION)
    assert "recorded_python" not in _call(worker, _prompt(PYTHON_VERSION)).metadata


def test_only_the_interpreter_declaration_is_rekeyed(tmp_path: Path) -> None:
    worker = _worker(tmp_path, _prompt(OTHER_PYTHON), OTHER_PYTHON)
    with pytest.raises(ReplayMissError):
        # Any other byte the provider receives must still match. (A trailing space is not
        # one: the worker strips it before sending, and replay keys on what is sent, I-10.)
        _call(worker, _prompt(PYTHON_VERSION).replace('"python"', '"Python"'))


def test_fixture_without_recorded_interpreter_is_keyed_unchanged(tmp_path: Path) -> None:
    worker = _worker(tmp_path, _prompt(OTHER_PYTHON), None)
    with pytest.raises(ReplayMissError):
        _call(worker, _prompt(PYTHON_VERSION))


def test_a_change_to_the_provider_instructions_alone_is_a_replay_miss(tmp_path: Path) -> None:
    """Replay keys on the complete provider request (TARGET_ARCHITECTURE I-10): guidance the
    worker adds after the prompt is rendered (``instructions``) is part of the key."""
    worker = _worker(tmp_path, _prompt(PYTHON_VERSION), PYTHON_VERSION)
    request = SimpleNamespace(operation="EXECUTE", prompt=_prompt(PYTHON_VERSION))
    assert worker.call(request).text == "{}"  # the recorded request replays
    real = worker.request_builder
    worker.request_builder = lambda r: {**real(r), "instructions": real(r).get("instructions", "") + " changed"}
    with pytest.raises(ReplayMissError):
        worker.call(request)  # same prompt, different instructions: a miss


def test_the_vendored_fixture_is_keyed_by_complete_requests() -> None:
    fixture = json.loads((ROOT / "tests" / "fixtures" / "recorded-cases.json").read_text(encoding="utf-8"))
    keyed = [e for e in fixture["entries"] if "provider_request" in e]
    assert len(keyed) == 10 and fixture["request_settings"]["model"]
    assert all(request_sha256(e["provider_request"]) == e["request_sha256"] for e in keyed)
    assert all("instructions" in e["provider_request"] for e in keyed if e["operation"] != "BOOTSTRAP_ANALYSIS")
