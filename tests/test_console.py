from __future__ import annotations

import io

import pytest

from pdl_taskmaster.host.console import DEFAULT_COLORS, color_scheme, paint, parse_colors, render_history

TRANSCRIPT = """=== PDLt session started ===
WORKER: DEVELOPMENT / LIVE DEMONSTRATION; NOT A QUALIFIED R2S MEASUREMENT CONDITION
REASONING: default=low
USER> Solve the riddle.
ASSISTANT> Prompt Pseudocode

EXPLAIN the riddle.

Confirm or correct this interpretation.
USER> /confirm
ASSISTANT> The answer.
PROTOCOL_CLOSED
=== PDLt session ended ==="""


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


def test_turns_are_separated_by_a_blank_line_without_colors():
    lines = render_history(TRANSCRIPT, None)
    assert lines[3:7] == ["", "USER> Solve the riddle.", "", "ASSISTANT> Prompt Pseudocode"]
    assert lines[lines.index("USER> /confirm") - 1] == ""
    assert lines[lines.index("ASSISTANT> The answer.") - 1] == ""
    assert "\x1b[" not in "\n".join(lines)
    assert "EXPLAIN the riddle." in lines  # the assistant's words are kept verbatim


def test_each_speaker_gets_its_color():
    colors = parse_colors("user=cyan,assistant=green")
    lines = render_history(TRANSCRIPT, colors)
    assert "\x1b[36mUSER>\x1b[0m \x1b[36mSolve the riddle.\x1b[0m" in lines
    assert "\x1b[32mASSISTANT>\x1b[0m Prompt Pseudocode" in lines
    assert "\x1b[2mPROTOCOL_CLOSED\x1b[0m" in lines  # host bookkeeping is dimmed
    assert "EXPLAIN the riddle." in lines  # assistant body is not recolored


def test_a_role_can_be_uncolored():
    assert paint("x", "note", parse_colors("note=none")) == "x"


def test_color_settings_are_validated():
    assert parse_colors(None) == DEFAULT_COLORS
    with pytest.raises(ValueError):
        parse_colors("speaker=red")
    with pytest.raises(ValueError):
        parse_colors("user=plaid")
    with pytest.raises(ValueError):
        color_scheme("sometimes", stream=_Tty())


def test_auto_colors_only_a_terminal(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("PDLT_COLOR", raising=False)
    monkeypatch.delenv("PDLT_COLORS", raising=False)
    assert color_scheme("auto", stream=io.StringIO()) is None  # pipe or file: plain text
    assert color_scheme("always", stream=io.StringIO()) == DEFAULT_COLORS
    assert color_scheme("never", stream=_Tty()) is None
    monkeypatch.setenv("NO_COLOR", "1")
    assert color_scheme("auto", stream=_Tty()) is None


def test_environment_sets_mode_and_colors(monkeypatch):
    monkeypatch.setenv("PDLT_COLOR", "always")
    monkeypatch.setenv("PDLT_COLORS", "assistant=yellow")
    assert color_scheme(stream=io.StringIO())["assistant"] == "yellow"
