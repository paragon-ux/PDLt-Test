"""Who-said-what display for the REPL: color themes and turn spacing.

A theme gives the user one color and the assistant another. Theme invariant: the
assistant's color is the lighter, more prominent one and the user's the darker,
more subdued one, with at least MIN_CONTRAST between them. Every predefined theme
is built through ``Theme``, which enforces that, so a theme that breaks the rule
cannot be defined.

Selection, highest first: ``--user-color`` / ``--assistant-color``, then
``$PDLT_USER_COLOR`` / ``$PDLT_ASSISTANT_COLOR``, then the colors of ``--theme`` /
``$PDLT_THEME``, then the Default theme. Colors are on whenever standard output is a
terminal; output to a pipe or file stays plain, and ``NO_COLOR`` turns colors off.
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import TextIO


@dataclass(frozen=True)
class Color:
    name: str
    code: int  # xterm 256-color index
    rgb: tuple[int, int, int]

    @property
    def luminance(self) -> float:
        """WCAG relative luminance of the color."""
        def channel(value: int) -> float:
            c = value / 255
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = (channel(v) for v in self.rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    @property
    def ansi(self) -> str:
        return f"38;5;{self.code}"


def contrast(lighter: Color, darker: Color) -> float:
    """WCAG contrast ratio between two colors (1 = identical, 21 = black on white)."""
    return (lighter.luminance + 0.05) / (darker.luminance + 0.05)


# The supported colors for --user-color and --assistant-color (xterm 256-color palette).
PALETTE: dict[str, Color] = {
    color.name: color for color in (
        Color("white", 255, (238, 238, 238)),
        Color("teal", 37, (0, 175, 175)),
        Color("green", 34, (0, 175, 0)),
        Color("blue", 33, (0, 135, 255)),
        Color("purple", 183, (215, 175, 255)),
        Color("yellow", 228, (255, 255, 135)),
        Color("orange", 173, (215, 135, 95)),
    )
}
COLOR_NAMES = tuple(PALETTE)

# The assistant's color must be lighter than the user's by at least this contrast ratio.
MIN_CONTRAST = 1.5


@dataclass(frozen=True)
class Theme:
    """A user/assistant color pair that keeps the assistant lighter (the invariant)."""

    name: str
    user: str
    assistant: str

    def __post_init__(self) -> None:
        for role, color in (("user", self.user), ("assistant", self.assistant)):
            if color not in PALETTE:
                raise ValueError(f"theme {self.name!r}: {role} color {color!r} is not one of {', '.join(COLOR_NAMES)}")
        problem = ordering_problem(self.user, self.assistant)
        if problem:
            raise ValueError(f"theme {self.name!r}: {problem}")


def ordering_problem(user: str, assistant: str) -> str | None:
    """Why a user/assistant pair breaks the theme invariant, or None when it holds."""
    u, a = PALETTE[user], PALETTE[assistant]
    if a.luminance <= u.luminance:
        return f"the assistant color ({assistant}) must be lighter than the user color ({user})"
    if contrast(a, u) < MIN_CONTRAST:
        return (f"{assistant} on {user} has contrast {contrast(a, u):.2f}, "
                f"below the minimum of {MIN_CONTRAST} between assistant and user")
    return None


THEMES: dict[str, Theme] = {
    theme.name: theme for theme in (
        Theme("default", user="teal", assistant="white"),
        Theme("bright", user="teal", assistant="yellow"),
        Theme("classic", user="green", assistant="white"),
        Theme("bold", user="green", assistant="purple"),
        Theme("claude", user="orange", assistant="white"),
    )
}
THEME_NAMES = tuple(THEMES)
DEFAULT_THEME = "default"

# Fixed roles outside the theme: host bookkeeping dimmed, errors red.
_FIXED = {"note": "2", "error": "38;5;203"}


@dataclass(frozen=True)
class Colors:
    """The resolved display colors; ``warning`` explains a custom pair that breaks the invariant."""

    user: str
    assistant: str
    warning: str | None = None

    def code(self, role: str) -> str:
        if role in ("user", "assistant"):
            return PALETTE[getattr(self, role)].ansi
        return _FIXED.get(role, "")


def resolve_colors(theme: str | None = None, user: str | None = None, assistant: str | None = None,
                   *, environ: dict[str, str] | None = None) -> Colors:
    """Theme and per-role colors after precedence (flag > environment > theme > Default)."""
    env = os.environ if environ is None else environ
    theme_name = (theme or env.get("PDLT_THEME") or DEFAULT_THEME).strip().lower()
    if theme_name not in THEMES:
        raise ValueError(f"unknown theme {theme_name!r}: use one of {', '.join(THEME_NAMES)}")
    chosen = THEMES[theme_name]
    user_color = (user or env.get("PDLT_USER_COLOR") or chosen.user).strip().lower()
    assistant_color = (assistant or env.get("PDLT_ASSISTANT_COLOR") or chosen.assistant).strip().lower()
    for role, color in (("user", user_color), ("assistant", assistant_color)):
        if color not in PALETTE:
            raise ValueError(f"unknown {role} color {color!r}: use one of {', '.join(COLOR_NAMES)}")
    problem = ordering_problem(user_color, assistant_color)
    return Colors(user_color, assistant_color, f"{problem}; readability may suffer" if problem else None)


def color_enabled(stream: TextIO | None = None, *, environ: dict[str, str] | None = None) -> bool:
    """Colors are on for a terminal; a pipe or file stays plain, as does NO_COLOR."""
    env = os.environ if environ is None else environ
    stream = stream or sys.stdout
    return not env.get("NO_COLOR") and _is_terminal(stream) and _enable_virtual_terminal(stream)


def paint(text: str, role: str, colors: Colors | None) -> str:
    code = colors.code(role) if colors else ""
    if not code or not text:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def input_prompt(prompt: str, colors: Colors | None) -> str:
    """The input prompt, leaving the user's color on while they type (reset_input ends it)."""
    return f"\x1b[{colors.code('user')}m{prompt}" if colors else prompt


def reset_input(colors: Colors | None) -> None:
    if colors:
        sys.stdout.write("\x1b[0m")
        sys.stdout.flush()


# The transcript's own line prefixes (written by the REPL), one per speaker.
_TURN_PREFIXES = (("USER> ", "user"), ("ASSISTANT> ", "assistant"), ("ERROR> ", "error"))
# Host bookkeeping lines in a transcript: shown dimmed, never as a speaker's words.
_NOTE_PREFIXES = ("WORKER: ", "REASONING: ", "FAST MODE: ")
_NOTE_LINES = ("PROTOCOL_CLOSED", "USER_INTERRUPTED")


def render_history(transcript: str, colors: Colors | None) -> list[str]:
    """A transcript as display lines: a blank line before each turn, each speaker's
    words in its color, host bookkeeping dimmed."""
    lines: list[str] = []
    role: str | None = None
    for line in transcript.splitlines():
        turn = next(((prefix, r) for prefix, r in _TURN_PREFIXES if line.startswith(prefix)), None)
        if turn is not None:
            prefix, role = turn
            if lines and lines[-1] != "":
                lines.append("")
            lines.append(paint(line, role, colors))
            continue
        if (line.startswith("=== ") and line.endswith(" ===")) or line in _NOTE_LINES or (
            role is None and line.startswith(_NOTE_PREFIXES)
        ):
            role = None
            lines.append(paint(line, "note", colors))
            continue
        lines.append(paint(line, role, colors) if role else line)
    return lines


def _is_terminal(stream: TextIO) -> bool:
    try:
        return stream.isatty()
    except (AttributeError, ValueError):
        return False


def _enable_virtual_terminal(stream: TextIO) -> bool:
    """Windows consoles interpret color codes only with virtual terminal processing on."""
    if sys.platform != "win32":
        return True
    try:
        import ctypes
        import msvcrt

        kernel32 = ctypes.windll.kernel32
        handle = msvcrt.get_osfhandle(stream.fileno())
        mode = ctypes.c_uint32()
        if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
            return False
        return bool(kernel32.SetConsoleMode(handle, mode.value | 0x0004))  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
    except Exception:
        return False
