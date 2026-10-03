from __future__ import annotations

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from pdl_taskmaster.providers.fixtures import build_recorded_fixture_from_vendored
from pdl_taskmaster.providers.recorded import ReplayMissError
from pdl_taskmaster.verification.sandbox import PYTHON_VERSION, python_declaration

ROOT = Path(__file__).resolve().parents[1]
OTHER_PYTHON = "3.9" if PYTHON_VERSION != "3.9" else "3.8"


def _prompt(version: str) -> str:
    return f'{{"AVAILABLE_EXECUTION_TOOLS": [{{"name": "python", "description": "{python_declaration(version)}."}}]}}'


def _worker(tmp_path: Path, prompt_text: str, recorded_python: str | None):
    fixture = {
        "schema": 1,
        "entries": [
            {
                "operation": "EXECUTE",
                "prompt_sha256": hashlib.sha256(prompt_text.encode("utf-8")).hexdigest(),
                "prompt_text": prompt_text,
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
        _call(worker, _prompt(PYTHON_VERSION) + " ")


def test_fixture_without_recorded_interpreter_is_keyed_unchanged(tmp_path: Path) -> None:
    worker = _worker(tmp_path, _prompt(OTHER_PYTHON), None)
    with pytest.raises(ReplayMissError):
        _call(worker, _prompt(PYTHON_VERSION))
