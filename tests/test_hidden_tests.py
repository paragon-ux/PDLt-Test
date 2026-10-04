"""Evaluation plane: the hidden-test runner (hidden_tests.py).

The prompts' own test files are checked by `python hidden_tests.py --validate`
(see test_graders.test_hidden_test_validation_is_current). These tests cover the
runner: candidate selection, and resuming after a candidate hangs.
"""
from __future__ import annotations

import json

import hidden_tests

_TESTS = """
TEST_SECONDS = 2


def CANDIDATES():
    return functions_named("hang", "wrong", "right")


def test_returns_one(f):
    assert f() == 1


TESTS = [test_returns_one]
"""


def _with_tests(monkeypatch, tmp_path, source: str) -> None:
    (tmp_path / "X-01.py").write_text(source, encoding="utf-8")
    monkeypatch.setattr(hidden_tests, "TESTS_DIR", tmp_path)


def test_a_hung_candidate_does_not_block_the_next(monkeypatch, tmp_path):
    """A timed-out test's thread can't be stopped inside the sandbox, so the run
    ends there and the next candidate is tried in a fresh sandbox run."""
    _with_tests(monkeypatch, tmp_path, _TESTS)
    deliverable = (
        "```python\n"
        "def hang():\n    while True:\n        pass\n\n"
        "def wrong():\n    return 2\n\n"
        "def right():\n    return 1\n"
        "```"
    )
    report = hidden_tests.run("X-01", deliverable)
    assert report["passed"]
    assert [c["name"] for c in report["candidates"]] == ["hang", "wrong", "right"]
    assert "timed out" in report["candidates"][0]["failures"][0]
    assert report["sandbox_runs"] == 2


def test_no_candidate_fails_with_a_reason(monkeypatch, tmp_path):
    _with_tests(monkeypatch, tmp_path, _TESTS)
    report = hidden_tests.run("X-01", "```python\ndef unrelated():\n    return 1\n```")
    assert not report["passed"]
    assert report["reason"] == "no candidate implements the stated operations"


def test_no_code_fails():
    report = hidden_tests.run("05-03", "The answer is [[1, 5]].")
    assert not report["passed"] and "no Python code" in report["reason"]


def test_progress_lines_name_the_candidate_that_was_running():
    out = "\n".join([
        hidden_tests.PROGRESS_PREFIX + json.dumps({"start": 0, "name": "a", "total": 2}),
        hidden_tests.PROGRESS_PREFIX + json.dumps({"start": 1, "name": "b", "total": 2}),
    ])
    final, started = hidden_tests._parse_output(out)
    assert final is None and started == {"start": 1, "name": "b", "total": 2}


def test_deliverable_body_drops_the_result_ir_and_host_notes():
    text = "Code:\n```python\nx = 1\n```\n[host] note\n\n```json\n{\"witness\": {}}\n```"
    body = hidden_tests.deliverable_body(text)
    assert "[host]" not in body and "witness" not in body and "x = 1" in body
