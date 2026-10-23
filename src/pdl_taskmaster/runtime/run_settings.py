"""The run settings a session's engine reads (L124 D7): one typed, validated object the REPL, headless runs and
library callers build, instead of attributes copied off the worker.

``from_worker`` reads the settings a worker carries as attributes (the API worker does; a recorded replay and the
codex worker carry none, so they run with the defaults their recordings were made with). It is kept for library
callers that configure a worker that way.
"""
from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any

from pdl_taskmaster.runtime.representation import REPRESENTATIONS

# L153: protocol (the default); direct, answered behind SECURE_GATEWAY; saver, the protocol only for what System 1
# classifies VERIFIED_EXECUTION. A mode is chosen when a session opens: changing it opens a new session.
MODES = ("protocol", "direct", "saver")


@dataclass(frozen=True)
class RunSettings:
    max_repairs: int | None = None  # None: the routed tier's repairs; 0: stop at the first failed EXECUTE
    draft_execute: bool = False  # DRAFT_EXECUTE brief before EXECUTE (ADR-0013 P6)
    agent_tools: bool = False  # in-call tools and checked submissions (ADR-0029)
    agent_tools_exclude: tuple[str, ...] = ()  # tools withheld from agent_tools, for ablations (L145)
    representation: str = "pdl"  # the confirmed route's artifacts: "pdl", or natural language "nl" (L97)
    tier_d1: bool | None = None  # feed back the model's own test failures in standard mode; None: the engine's default
    no_review: bool = False  # the unconfirmed route: no prompt or plan review
    sandbox_mode: str | None = None  # None: $PDLT_SANDBOX, else auto; the sandbox resolves and announces it
    task_type: str | None = None  # a registered task type pinned for every request; None: System 1 classifies
    withhold_execution_context: bool = False  # L148 A/B: earlier stages without EXECUTE's instructions
    ablate_unconfirmed: tuple[str, ...] = ()  # L149 ablation: parts of what EXECUTE_UNCONFIRMED receives
    mode: str = "protocol"  # L153: one of MODES
    gateway: bool = False  # L155: SECURE_GATEWAY's poisoned-input check in protocol mode too (direct and saver always)

    def __post_init__(self) -> None:
        problems = []
        if self.max_repairs is not None and (not isinstance(self.max_repairs, int) or self.max_repairs < 0):
            problems.append(f"max_repairs: None or a non-negative integer, got {self.max_repairs!r}")
        if self.mode not in MODES:
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
        for name in ("draft_execute", "agent_tools", "no_review", "withhold_execution_context", "gateway"):
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
            "agent_tools": bool(getattr(worker, "agent_tools", False)),
            "representation": getattr(worker, "representation", None) or "pdl",
            "tier_d1": (bool(worker.tier_d1) if getattr(worker, "tier_d1", None) is not None else None),
        }
        return cls(**{**carried, **settings})

    def apply(self, engine: Any) -> None:
        """Set the engine's run settings (no_review and sandbox_mode are given when the engine is built)."""
        engine.max_repairs = self.max_repairs
        engine.draft_execute = self.draft_execute
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
        engine.gateway = self.gateway

    def as_dict(self) -> dict[str, Any]:
        return {f.name: getattr(self, f.name) for f in fields(self)}
