"""The run settings a session's engine reads (L124 D7): one typed, validated object the REPL, headless runs and
library callers build, instead of attributes copied off the worker.

``from_worker`` reads the settings a worker carries as attributes (the API worker does; a recorded replay and the
codex worker carry none, so they run with the defaults their recordings were made with). It is kept for library
callers that configure a worker that way.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, replace
from typing import Any

from pdl_taskmaster.runtime.representation import REPRESENTATIONS

# L153: protocol (the default); direct, answered behind SECURE_GATEWAY; saver, the protocol only for what System 1
# classifies VERIFIED_EXECUTION. A mode is chosen when a session opens: changing it opens a new session.
MODES = ("protocol", "direct", "saver")
DEFAULT_MODE = "saver"  # ADR-0031 (L158, L159): saver is the default; protocol, direct and saver are chosen explicitly


def default_mode(worker: Any = None, *, review: bool = False) -> str:
    """ADR-0031: saver for a worker that carries run settings (the API worker); a worker that carries none (a recorded
    replay, the codex worker) runs in protocol mode, as its recordings were made. Review (L165) is the confirmed route,
    which runs in protocol mode."""
    if review:
        return "protocol"
    return DEFAULT_MODE if worker is None or hasattr(worker, "agent_tools") else "protocol"


def default_agent_tools(mode: str, no_review: bool) -> bool:
    """L166: in-call tools are on, except on the unconfirmed route in protocol mode (protocol, no review), where they
    measured no better and cost 49% more (L157). Saver's protocol branch and the confirmed route keep them."""
    return not (mode == "protocol" and no_review)


def check_review_mode(mode: str, no_review: bool) -> None:
    """L165: no review is the default everywhere; review is the confirmed route, in protocol mode. Direct and saver
    have no review, so asking for review in either is refused rather than ignored."""
    if not no_review and mode != "protocol":
        raise ValueError(f"review runs the confirmed route, in protocol mode; {mode} mode has no review")


@dataclass(frozen=True)
class RunSettings:
    max_repairs: int | None = None  # None: the routed tier's repairs; 0: stop at the first failed EXECUTE
    draft_execute: bool = False  # DRAFT_EXECUTE brief before EXECUTE (ADR-0013 P6)
    confirmed_execute_tools: bool = False  # L168: the confirmed route's EXECUTE in-call tools (L163), off by default
    agent_tools: bool | None = None  # None: resolve from the worker and effective mode (L166)
    agent_tools_exclude: tuple[str, ...] = ()  # tools withheld from agent_tools, for ablations (L145)
    representation: str = "pdl"  # the confirmed route's artifacts: "pdl", or natural language "nl" (L97)
    tier_d1: bool | None = None  # feed back the model's own test failures in standard mode; None: the engine's default
    no_review: bool = True  # L165: no prompt or plan review by default; False is the confirmed route (protocol mode)
    sandbox_mode: str | None = None  # None: $PDLT_SANDBOX, else auto; the sandbox resolves and announces it
    task_type: str | None = None  # a registered task type pinned for every request; None: System 1 classifies
    withhold_execution_context: bool = False  # L148 A/B: earlier stages without EXECUTE's instructions
    ablate_unconfirmed: tuple[str, ...] = ()  # L149 ablation: parts of what EXECUTE_UNCONFIRMED receives
    mode: str | None = None  # None: stored session mode, else the worker/review default

    def __post_init__(self) -> None:
        problems = []
        if self.max_repairs is not None and (not isinstance(self.max_repairs, int) or self.max_repairs < 0):
            problems.append(f"max_repairs: None or a non-negative integer, got {self.max_repairs!r}")
        if self.mode is not None and self.mode not in MODES:
            problems.append(f"mode: one of {list(MODES)}, got {self.mode!r}")
        if self.representation not in REPRESENTATIONS:
            problems.append(f"representation: one of {list(REPRESENTATIONS)}, got {self.representation!r}")
        if self.sandbox_mode is not None and not isinstance(self.sandbox_mode, str):
            problems.append(f"sandbox_mode: None or a mode name, got {self.sandbox_mode!r}")
        try:
            from pdl_taskmaster.runtime.agent_tools import parse_exclusions

            parse_exclusions(self.agent_tools_exclude)
        except (ValueError, TypeError) as exc:
            problems.append(f"agent_tools_exclude: {exc}")
        from pdl_taskmaster.runtime.output_contracts import ABLATIONS

        if not isinstance(self.ablate_unconfirmed, tuple) or set(self.ablate_unconfirmed) - set(ABLATIONS):
            problems.append(f"ablate_unconfirmed: a tuple of {sorted(ABLATIONS)}, got {self.ablate_unconfirmed!r}")
        if self.agent_tools is not None and not isinstance(self.agent_tools, bool):
            problems.append(f"agent_tools: a bool or None, got {self.agent_tools!r}")
        for name in ("draft_execute", "confirmed_execute_tools", "no_review",
                     "withhold_execution_context"):
            if not isinstance(getattr(self, name), bool):
                problems.append(f"{name}: a bool, got {getattr(self, name)!r}")
        if problems:
            raise ValueError("invalid run settings: " + "; ".join(problems))

    @classmethod
    def from_worker(cls, worker: Any, **settings: Any) -> "RunSettings":
        """The settings a worker carries as attributes, with ``settings`` given explicitly."""
        carried = {
            "max_repairs": getattr(worker, "max_repairs", None),
            "draft_execute": bool(getattr(worker, "draft_execute", False)),
            "agent_tools": getattr(worker, "agent_tools", False),  # None: the session's default (L166)
            "representation": getattr(worker, "representation", None) or "pdl",
            "tier_d1": (bool(worker.tier_d1) if getattr(worker, "tier_d1", None) is not None else None),
        }
        return cls(**{**carried, **settings}).resolved(worker)

    def resolved(self, worker: Any = None, *, stored_mode: str | None = None) -> "RunSettings":
        """Resolve dependent settings; no worker means the standalone settings defaults, not a replay worker."""
        mode = self.mode or stored_mode or default_mode(worker, review=not self.no_review)
        tools = self.agent_tools if self.agent_tools is not None else getattr(
            worker, "agent_tools", None if worker is None else False)
        if tools is None:
            tools = default_agent_tools(mode, self.no_review)
        return replace(self, mode=mode, agent_tools=tools)

    def apply(self, engine: Any) -> None:
        """Set the engine's run settings (no_review and sandbox_mode are given when the engine is built)."""
        if self.mode is None or self.agent_tools is None:
            self.resolved().apply(engine)
            return
        engine.max_repairs = self.max_repairs
        engine.draft_execute = self.draft_execute
        engine.confirmed_execute_tools = self.confirmed_execute_tools
        engine.agent_tools = self.agent_tools
        from pdl_taskmaster.runtime.agent_tools import parse_exclusions

        engine.agent_tools_exclude = parse_exclusions(self.agent_tools_exclude)
        engine.representation = self.representation
        if self.tier_d1 is not None:
            engine.tier_d1 = self.tier_d1
        engine.pinned_task_type = self.task_type
        engine.withhold_execution_context = self.withhold_execution_context
        engine.ablate_unconfirmed = self.ablate_unconfirmed
        engine.mode = self.mode

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}
