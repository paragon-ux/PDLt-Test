"""Who-said-what display for the REPL: per-role colors and turn spacing.

Colors are on when standard output is a terminal (``--color auto``, the default),
and off for pipes, files and ``NO_COLOR``. ``--color always|never`` or
``PDLT_COLOR`` overrides that; ``PDLT_COLORS`` picks the color of each role, for
example ``PDLT_COLORS="user=bright_cyan,assistant=green,note=none"``.
"""
from __future__ import annotations

import os
import sys
from typing import TextIO

ANSI_CODES = {
    "black": "30", "red": "31", "green": "32", "yellow": "33", "blue": "34", "magenta": "35", "cyan": "36",
    "white": "37", "bright_black": "90", "bright_red": "91", "bright_green": "92", "bright_yellow": "93",
    "bright_blue": "94", "bright_magenta": "95", "bright_cyan": "96", "bright_white": "97", "bold": "1",
    "dim": "2", "none": "",
}
ROLES = ("user", "assistant", "error", "note")
DEFAULT_COLORS = {"user": "bright_cyan", "assistant": "bright_green", "error": "bright_red", "note": "dim"}
COLOR_MODES = ("auto", "always", "never")

# The transcript's own line prefixes (written by the REPL), one per speaker.
_TURN_PREFIXES = (("USER> ", "user"), ("ASSISTANT> ", "assistant"), ("ERROR> ", "error"))
# Host bookkeeping lines in a transcript: shown dimmed, never as a speaker's words.
_NOTE_PREFIXES = ("WORKER: ", "REASONING: ", "FAST MODE: ")
_NOTE_LINES = ("PROTOCOL_CLOSED", "USER_INTERRUPTED")


def parse_colors(spec: str | None) -> dict[str, str]:
    """``role=color`` pairs over the defaults; an unknown role or color is an error."""
    colors = dict(DEFAULT_COLORS)
    for item in (spec or "").split(","):
        if not item.strip():
            continue
        role, sep, name = item.partition("=")
        role, name = role.strip().lower(), name.strip().lower()
        if not sep or role not in ROLES or name not in ANSI_CODES:
            raise ValueError(
                f"invalid color setting {item.strip()!r}: use role=color with role in {', '.join(ROLES)} "
                f"and color in {', '.join(ANSI_CODES)}"
            )
        colors[role] = name
    return colors


def color_scheme(mode: str | None = None, spec: str | None = None, *, stream: TextIO | None = None) -> dict[str, str] | None:
    """The colors to use, or None for plain text."""
    stream = stream or sys.stdout
    mode = (mode or os.environ.get("PDLT_COLOR") or "auto").strip().lower()
    if mode not in COLOR_MODES:
        raise ValueError(f"invalid color mode {mode!r}: use one of {', '.join(COLOR_MODES)}")
    colors = parse_colors(spec if spec is not None else os.environ.get("PDLT_COLORS"))
    if mode == "never":
        return None
    if mode == "auto":
        if os.environ.get("NO_COLOR") or not _is_terminal(stream) or not _enable_virtual_terminal(stream):
            return None
    else:
        _enable_virtual_terminal(stream)
    return colors


def paint(text: str, role: str, colors: dict[str, str] | None) -> str:
    code = ANSI_CODES.get((colors or {}).get(role, "none"), "")
    if not colors or not code or not text:
        return text
    return f"\x1b[{code}m{text}\x1b[0m"


def render_history(transcript: str, colors: dict[str, str] | None) -> list[str]:
    """A transcript as display lines: a blank line before each turn, the speaker's
    label in its color (a user's words in the user color), host bookkeeping dimmed."""
    lines: list[str] = []
    role: str | None = None
    for line in transcript.splitlines():
        turn = next(((prefix, r) for prefix, r in _TURN_PREFIXES if line.startswith(prefix)), None)
        if turn is not None:
            prefix, role = turn
            if lines and lines[-1] != "":
                lines.append("")
            label = paint(prefix.rstrip(), role, colors)
            body = line[len(prefix):]
            lines.append(f"{label} {paint(body, role, colors) if role != 'assistant' else body}")
            continue
        if (line.startswith("=== ") and line.endswith(" ===")) or line in _NOTE_LINES or (
            role is None and line.startswith(_NOTE_PREFIXES)
        ):
            role = None
            lines.append(paint(line, "note", colors))
            continue
        lines.append(paint(line, role, colors) if role in ("user", "error") else line)
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
