"""How a session ended, as a number and as a result object (ADR-0019 exit codes, with its amendments). The one place
the stage-to-exit mapping lives: headless runs, the catalogue and library callers all use it."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EXIT_SUCCESS = 0  # CLOSED_SUCCESS, or a published boundary refusal
EXIT_CANCELLED = 1  # CLOSED_CANCELLED: failed closed
EXIT_UNCONFIRMED = 2  # stopped at a review gate or another non-terminal stage
EXIT_WAITING_INPUT = 3  # paused for input the task needs
EXIT_HARNESS_ERROR = 4  # a harness or provider error; never a protocol result
EXIT_UNVERIFIED = 5  # CLOSED_UNVERIFIED: published without the host establishing it (L116)
EXIT_INTERRUPTED = 130  # interrupted by the user

RESULT_STAGES = frozenset({"CLOSED_SUCCESS", "CLOSED_UNVERIFIED"})


def exit_status(stage: str | None, *, refused: bool = False, harness_error: bool = False) -> int:
    """The exit code for a session that ended at ``stage`` (None: no protocol instance was opened)."""
    if harness_error:
        return EXIT_HARNESS_ERROR
    if stage is None:
        return EXIT_SUCCESS  # a direct reply, or a published refusal (refused)
    return {"CLOSED_SUCCESS": EXIT_SUCCESS, "CLOSED_CANCELLED": EXIT_CANCELLED,
            "CLOSED_UNVERIFIED": EXIT_UNVERIFIED, "WAITING_INPUT": EXIT_WAITING_INPUT}.get(stage, EXIT_UNCONFIRMED)


@dataclass
class TurnResult:
    """What one message to a session produced."""

    text: str | None  # the reply shown to the user: a review artifact, the published result, or a direct reply
    stage: str | None  # the protocol stage after the message; None when no instance is open
    exit_status: int  # exit_status(stage, refused=...)
    closed: bool  # the instance closed with this message
    review: str | None = None  # the review gate left open: "prompt" or "plan"
    refused: bool = False  # System 1 refused the request at the boundary (ADR-0020)
    provenance: dict[str, Any] | None = None  # for a published result: what it rests on (runtime/provenance.py)
    workspace_path: str | None = None
    details: dict[str, Any] = field(default_factory=dict)
