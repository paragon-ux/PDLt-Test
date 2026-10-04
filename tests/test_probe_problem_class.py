"""scripts/probe_problem_class.py: the classifier probe, on a fake System 1 client."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _probe():
    spec = importlib.util.spec_from_file_location("probe_problem_class", ROOT / "scripts" / "probe_problem_class.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeSys1:
    """Answers each request from a table keyed by request text; records every request."""

    is_configured, model = True, "fake-sys1"

    def __init__(self, answers: dict[str, tuple[str, float]], default=("STANDARD_EXECUTION", 0.97)):
        self.answers, self.default = answers, default
        self.requests: list = []

    def call(self, request):
        self.requests.append(request)
        (name, question), = request.questions.items()
        choice, p = self.answers.get(request.state["request"], self.default)
        other = next(c for c in question.choices if c != choice)
        return {"answers": {name: {"choice": choice, "confidence": p,
                                   "probabilities": {choice: p, other: round(1 - p, 4)}}}}, 2.0


def test_probe_reports_verdict_gating_and_routing_for_extra_questions(capsys):
    probe = _probe()
    client = FakeSys1({"confident question": ("VERIFIED_EXECUTION", 0.97),
                       "doubtful question": ("VERIFIED_EXECUTION", 0.87)})
    code = probe.main(["--no-catalogue", "--text", "confident question", "--text", "doubtful question",
                       "--text", "an essay"], client=client)
    out = capsys.readouterr().out
    assert code == 0
    assert [r.questions["problem_class"].choices for r in client.requests] == \
        [["VERIFIED_EXECUTION", "STANDARD_EXECUTION"]] * 3
    rows = {line.split()[0]: line.split() for line in out.splitlines() if line.startswith("text-")}
    assert rows["text-1"][1:2] + rows["text-1"][5:7] == ["VERIFIED_EXECUTION", "True", "True"]
    # Below the gate a VERIFIED verdict routes standard, as in the engine.
    assert rows["text-2"][1:3] + rows["text-2"][5:7] == ["VERIFIED_EXECUTION", "0.87", "False", "False"]
    assert rows["text-3"][1:2] + rows["text-3"][5:7] == ["STANDARD_EXECUTION", "True", "False"]
    assert "VERIFIED below the gate: 1" in out and "requires_verified_execution: 1" in out


def test_probe_reads_catalogue_prompts_filtered_by_category_and_ids(tmp_path, capsys):
    probe = _probe()
    client = FakeSys1({})
    extra = tmp_path / "question.txt"
    extra.write_text("a question from a file", encoding="utf-8")
    code = probe.main(["--category", "01", "--ids", "01-02,01-03", "--file", str(extra)], client=client)
    out = capsys.readouterr().out
    assert code == 0
    sent = [r.state["request"] for r in client.requests]
    assert len(sent) == 3 and sent[-1] == "a question from a file"
    assert all(text.strip() for text in sent)
    assert "01-02" in out and "01-03" in out and "01-01 " not in out
    # Both catalogue prompts expect VERIFIED and the fake routes them STANDARD.
    assert "routing matches manifest expected_routing: 0/2" in out


def test_probe_reports_a_failed_call_and_continues(capsys):
    probe = _probe()

    class Failing(FakeSys1):
        def call(self, request):
            if request.state["request"] == "boom":
                raise RuntimeError("Sys1 HTTP 503")
            return super().call(request)

    code = probe.main(["--no-catalogue", "--text", "boom", "--text", "fine"], client=Failing({}))
    out = capsys.readouterr().out
    assert code == 1
    assert "ERROR RuntimeError: Sys1 HTTP 503" in out and "errors: 1" in out and "answered: 1" in out


def test_probe_without_system_1_configuration_exits_with_a_clear_message(monkeypatch, capsys):
    probe = _probe()
    for name in ("SYS1_API_KEY", "OPENROUTER_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    assert probe.main(["--no-catalogue", "--text", "anything"]) == 2
    assert "System 1 is not configured" in capsys.readouterr().err
