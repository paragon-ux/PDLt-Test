"""Reading closed sessions (L117, L121 E-1): the turns under a sessions folder that closed with a published result,
their artifacts and their provenance. Read-only. The layout is the one the REPL writes:
``<root>/<session>/workspaces/<workspace>/turns/<turn>/``. The MCP server's resources are built on this."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from pdl_taskmaster.api.outcome import RESULT_STAGES

# artifact name -> (file in the result stage's output, media type, what it is)
ARTIFACTS: dict[str, tuple[str, str, str]] = {
    "response": ("current.md", "text/markdown", "the response as published"),
    "program-output": ("program-output.json", "application/json",
                       "the output of the programs the host ran for the response"),
}


def result_output(turn: Path) -> Path:
    return turn / "stages" / "50_execution" / "output"


def turn_provenance(turn: Path) -> dict[str, Any] | None:
    """The provenance the host recorded at closure, or one derived from the turn's events for a turn closed
    before it did (never claiming more than the records hold). None when neither can be read."""
    from pdl_taskmaster.runtime import provenance

    recorded = result_output(turn) / "provenance.json"
    if recorded.is_file():
        try:
            return json.loads(recorded.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
    return provenance.derive(turn)


@dataclass(frozen=True)
class ClosedTurn:
    session: str
    workspace: str
    turn: str
    status: str
    path: Path
    root: Path  # the sessions folder, resolved; nothing outside it is served

    def artifacts(self) -> dict[str, Path]:
        """The artifacts this turn has, by name, each a file inside the sessions folder."""
        output = result_output(self.path)
        return {name: output / file for name, (file, _, _) in ARTIFACTS.items()
                if (output / file).is_file() and (output / file).resolve().is_relative_to(self.root)}

    def provenance(self) -> dict[str, Any] | None:
        return turn_provenance(self.path)


def closed_turns(root: Path) -> list[ClosedTurn]:
    """Every turn under ``root`` that closed with a published result, in a stable order. Turns or files that resolve
    outside ``root`` are left out."""
    if not root.is_dir():
        return []
    base = root.resolve()
    found = []
    for marker in sorted(root.glob("*/workspaces/*/turns/*/turn.json")):
        try:
            status = json.loads(marker.read_text(encoding="utf-8")).get("status")
        except (OSError, ValueError):
            continue
        turn = marker.parent
        if status in RESULT_STAGES and turn.resolve().is_relative_to(base):
            found.append(ClosedTurn(turn.parents[3].name, turn.parents[1].name, turn.name, status, turn, base))
    return found
