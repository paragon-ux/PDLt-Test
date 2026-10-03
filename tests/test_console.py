from __future__ import annotations

import io

import pytest

from pdl_taskmaster.host.console import (
    COLOR_NAMES,
    MIN_CONTRAST,
    PALETTE,
    THEMES,
    Theme,
    color_enabled,
    contrast,
    paint,
    render_history,
    resolve_colors,
)

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

NO_ENV: dict[str, str] = {}


class _Tty(io.StringIO):
    def isatty(self) -> bool:
        return True


# ---------------------------------------------------------------- palette and themes

def test_supported_colors_include_orange_explicitly():
    assert COLOR_NAMES == ("white", "teal", "green", "blue", "purple", "yellow", "orange")


@pytest.mark.parametrize(
    "name, user, assistant",
    [("default", "teal", "white"), ("bright", "teal", "yellow"), ("classic", "green", "white"),
     ("bold", "green", "purple"), ("claude", "orange", "white")],
)
def test_each_predefined_theme(name, user, assistant):
    theme = THEMES[name]
    assert (theme.user, theme.assistant) == (user, assistant)
    colors = resolve_colors(name, environ=NO_ENV)
    assert (colors.user, colors.assistant, colors.warning) == (user, assistant, None)


def test_exactly_five_themes():
    assert list(THEMES) == ["default", "bright", "classic", "bold", "claude"]


@pytest.mark.parametrize("theme", list(THEMES.values()), ids=list(THEMES))
def test_every_theme_keeps_the_assistant_lighter_with_readable_contrast(theme):
    user, assistant = PALETTE[theme.user], PALETTE[theme.assistant]
    assert assistant.luminance > user.luminance
    assert contrast(assistant, user) >= MIN_CONTRAST


def test_a_theme_that_breaks_the_invariant_cannot_be_defined():
    with pytest.raises(ValueError, match="must be lighter"):
        Theme("inverted", user="white", assistant="teal")
    with pytest.raises(ValueError, match="contrast"):
        Theme("muddy", user="green", assistant="orange")  # lighter, but too close to read apart
    with pytest.raises(ValueError, match="not one of"):
        Theme("odd", user="teal", assistant="magenta")


# ---------------------------------------------------------------- selection and precedence

def test_default_colors():
    colors = resolve_colors(environ=NO_ENV)
    assert (colors.user, colors.assistant) == ("teal", "white")


def test_explicit_user_color():
    colors = resolve_colors(user="blue", environ=NO_ENV)
    assert (colors.user, colors.assistant) == ("blue", "white")


def test_explicit_assistant_color():
    colors = resolve_colors(assistant="yellow", environ=NO_ENV)
    assert (colors.user, colors.assistant) == ("teal", "yellow")


def test_individual_colors_override_the_theme():
    colors = resolve_colors("classic", user="blue", environ=NO_ENV)
    assert (colors.user, colors.assistant) == ("blue", "white")  # theme supplies the other role
    colors = resolve_colors("bold", assistant="yellow", environ=NO_ENV)
    assert (colors.user, colors.assistant) == ("green", "yellow")


def test_flags_override_environment_which_overrides_the_theme():
    env = {"PDLT_THEME": "bright", "PDLT_USER_COLOR": "blue"}
    assert (resolve_colors(environ=env).user, resolve_colors(environ=env).assistant) == ("blue", "yellow")
    assert resolve_colors(user="orange", environ=env).user == "orange"
    assert resolve_colors("classic", environ=env).assistant == "white"


def test_a_custom_pair_that_breaks_the_invariant_is_allowed_with_a_warning():
    colors = resolve_colors(user="white", assistant="teal", environ=NO_ENV)
    assert (colors.user, colors.assistant) == ("white", "teal")
    assert "must be lighter" in colors.warning


def test_unknown_names_are_rejected():
    with pytest.raises(ValueError, match="unknown theme"):
        resolve_colors("neon", environ=NO_ENV)
    with pytest.raises(ValueError, match="unknown user color"):
        resolve_colors(environ={"PDLT_USER_COLOR": "plaid"})


# ---------------------------------------------------------------- when colors show

def test_colors_are_on_for_a_terminal_and_off_for_pipes_and_no_color(monkeypatch):
    from pdl_taskmaster.host import console

    monkeypatch.setattr(console, "_enable_virtual_terminal", lambda stream: True)  # a real console handle
    assert color_enabled(_Tty(), environ=NO_ENV)
    assert not color_enabled(io.StringIO(), environ=NO_ENV)
    assert not color_enabled(_Tty(), environ={"NO_COLOR": "1"})


# ---------------------------------------------------------------- rendering

def test_turns_are_separated_by_a_blank_line_without_colors():
    lines = render_history(TRANSCRIPT, None)
    assert lines[3:7] == ["", "USER> Solve the riddle.", "", "ASSISTANT> Prompt Pseudocode"]
    assert lines[lines.index("USER> /confirm") - 1] == ""
    assert "\x1b[" not in "\n".join(lines)


def test_each_speaker_gets_its_theme_color():
    colors = resolve_colors(environ=NO_ENV)  # teal user, white assistant
    lines = render_history(TRANSCRIPT, colors)
    teal, white = PALETTE["teal"].ansi, PALETTE["white"].ansi
    assert f"\x1b[{teal}mUSER> Solve the riddle.\x1b[0m" in lines
    assert f"\x1b[{white}mASSISTANT> Prompt Pseudocode\x1b[0m" in lines
    assert f"\x1b[{white}mEXPLAIN the riddle.\x1b[0m" in lines  # the whole assistant turn
    assert "\x1b[2mPROTOCOL_CLOSED\x1b[0m" in lines  # host bookkeeping is dimmed


def test_paint_without_colors_is_plain():
    assert paint("x", "assistant", None) == "x"
