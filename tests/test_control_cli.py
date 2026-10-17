"""The control sends the harness's provider order (otherwise OpenRouter serves it from any provider)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

from pdl_taskmaster.host import control_cli
from pdl_taskmaster.providers.api_worker import ApiWorker, DEFAULT_PROVIDER_PINNING


@pytest.fixture
def sent(monkeypatch: pytest.MonkeyPatch) -> list[dict]:
    """Every request body the control sends; the reply is a canned Responses-API object."""
    bodies: list[dict] = []

    def fake_send(self, request, deadline):
        bodies.append(json.loads(request.data.decode("utf-8")))
        return {"id": "gen-test-1",
                "output": [{"type": "message", "content": [{"type": "output_text", "text": "the answer"}]}],
                "usage": {"input_tokens": 12, "output_tokens": 34,
                          "input_tokens_details": {"cached_tokens": 8},
                          "output_tokens_details": {"reasoning_tokens": 5}}}

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key-not-real")
    return bodies


def _run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *extra: str) -> None:
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("What is 2 + 2?", encoding="utf-8")
    argv = ["control_cli", "--prompt-file", str(prompt), "--workspace-root", str(tmp_path / "ws"),
            "--non-interactive", "--api-reasoning-effort", "low", *extra]
    monkeypatch.setattr(sys, "argv", argv)
    assert control_cli.main() == 0


def test_the_control_sends_the_harness_default_provider_order(tmp_path, monkeypatch, sent) -> None:
    _run(tmp_path, monkeypatch)
    assert len(sent) == 1
    assert sent[0]["provider"] == DEFAULT_PROVIDER_PINNING
    assert sent[0]["reasoning"] == {"effort": "low"}
    assert sent[0]["input"] == "What is 2 + 2?"


def test_explicit_providers_are_sent_without_fallbacks(tmp_path, monkeypatch, sent) -> None:
    _run(tmp_path, monkeypatch, "--api-providers", "Baseten,Crusoe")
    assert sent[0]["provider"] == {"order": ["Baseten", "Crusoe"], "allow_fallbacks": False}


def test_the_event_records_the_tokens_and_the_generation_id(tmp_path, monkeypatch, sent) -> None:
    _run(tmp_path, monkeypatch)
    line = (tmp_path / "ws" / "turns" / "turn_001" / "events.jsonl").read_text(encoding="utf-8").splitlines()[0]
    payload = json.loads(line)["payload"]
    assert payload["operation"] == "CONTROL_EXECUTE"
    assert (payload["input_tokens"], payload["output_tokens"], payload["reasoning_tokens"]) == (12, 34, 5)
    assert payload["cached_tokens"] == 8
    assert payload["response_id"] == "gen-test-1"
    assert (tmp_path / "ws" / "stages" / "50_execution" / "output" / "current.md").read_text(encoding="utf-8") == "the answer"
