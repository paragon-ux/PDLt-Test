"""Lifecycle of each model call, for diagnosing interruptions and ambiguous failures.

One ``CallTrace`` per worker call (an operation), one ``AttemptTrace`` per HTTP
attempt. Each attempt records how far it got:

    prepared -> connecting -> request_sent -> acknowledged -> response_started -> response_complete

- connecting: the client opened a connection (``http.client.connect``);
- request_sent: the request body was handed to the socket (its ``http.client.send``);
- acknowledged: the API answered with a status line and headers, so it received the
  request (the API receipt);
- response_started / response_bytes: the response body began / how much of it arrived.

The phases come from Python's own ``http.client`` audit events through one
process-wide hook that only records while a trace is active on the current thread,
so the transport (``urllib.request.urlopen``) is used unchanged. An attempt ends
with an outcome (completed, interrupted, http_error, transport_error, timeout,
unreadable); an interruption is ``local`` (KeyboardInterrupt in this process) or
``remote`` (the server or network ended it).
"""
from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass, field
from typing import Any

PHASES = ("prepared", "connecting", "request_sent", "acknowledged", "response_started", "response_complete")

_local = threading.local()
_hook_installed = False
_hook_lock = threading.Lock()


@dataclass
class AttemptTrace:
    attempt: int
    request_bytes: int
    started: float = field(default_factory=time.monotonic)
    phases: dict[str, float] = field(default_factory=dict)  # phase -> ms since the attempt started
    status: int | None = None
    response_bytes: int = 0
    outcome: str | None = None
    interrupted_by: str | None = None  # "local" or "remote"
    error: str | None = None
    retried: bool = False
    body: bytes | None = field(default=None, repr=False)

    def mark(self, phase: str) -> None:
        self.phases.setdefault(phase, round((time.monotonic() - self.started) * 1000, 1))

    @property
    def reached(self) -> str:
        """The furthest phase this attempt reached."""
        return max(self.phases, key=PHASES.index) if self.phases else "prepared"

    def to_dict(self) -> dict[str, Any]:
        return {
            "attempt": self.attempt, "reached": self.reached, "phases_ms": dict(self.phases),
            "status": self.status, "request_bytes": self.request_bytes, "response_bytes": self.response_bytes,
            "outcome": self.outcome, "interrupted_by": self.interrupted_by, "error": self.error,
            "retried": self.retried,
        }


@dataclass
class CallTrace:
    operation: str
    attempts: list[AttemptTrace] = field(default_factory=list)
    final: str | None = None  # completed, interrupted, failed
    number: int = 1  # the n-th call of this operation in the session (a repair is call 2)
    error: str | None = None  # the failure category when final is "failed"
    # What the API reported for the reply: response id, status, finish reason,
    # output and reasoning tokens, whether the output schema constrained decoding.
    reply: dict[str, Any] = field(default_factory=dict)

    def new_attempt(self, body: bytes | None) -> AttemptTrace:
        if self.attempts:
            self.attempts[-1].retried = True
        attempt = AttemptTrace(len(self.attempts) + 1, len(body or b""), body=body)
        attempt.mark("prepared")
        self.attempts.append(attempt)
        return attempt

    @property
    def sent(self) -> bool:
        """At least one attempt handed the request to the network."""
        return any("request_sent" in a.phases for a in self.attempts)

    @property
    def acknowledged(self) -> bool:
        return any("acknowledged" in a.phases for a in self.attempts)

    def to_dict(self) -> dict[str, Any]:
        last = self.attempts[-1] if self.attempts else None
        return {
            "operation": self.operation, "number": self.number, "final": self.final, "error": self.error,
            "reply": dict(self.reply), "sent": self.sent,
            "acknowledged": self.acknowledged,
            "response_started": any("response_started" in a.phases for a in self.attempts),
            "reached": last.reached if last else "prepared",
            "interrupted_by": last.interrupted_by if last else None,
            "retries": max(len(self.attempts) - 1, 0),
            "attempts": [a.to_dict() for a in self.attempts],
        }

    def summary(self) -> str:
        """One line a developer can read: what was sent, acknowledged and received."""
        last = self.attempts[-1] if self.attempts else None
        if last is None:
            return f"{self.operation}: not sent (no attempt started)"
        parts = [f"{self.operation} call {self.number} (HTTP attempt {last.attempt})", f"reached {last.reached}"]
        if last.status is not None:
            parts.append(f"HTTP {last.status}")
        if "acknowledged" in last.phases:
            parts.append(f"ack {last.phases['acknowledged']:.0f}ms")
        if last.response_bytes:
            parts.append(f"{last.response_bytes} bytes received")
        parts.append(f"outcome {last.outcome or 'in progress'}")
        if last.interrupted_by:
            parts.append(f"interrupted ({last.interrupted_by})")
        if len(self.attempts) > 1:
            parts.append(f"{len(self.attempts) - 1} retr{'y' if len(self.attempts) == 2 else 'ies'}")
        if self.reply.get("output_tokens") is not None:
            tokens = f"{self.reply['output_tokens']} output tokens"
            if self.reply.get("reasoning_tokens") is not None:
                tokens += f" ({self.reply['reasoning_tokens']} reasoning)"
            parts.append(tokens)
        if self.final == "failed":
            parts.append(f"call failed: {self.error or 'error'}")
        if self.reply.get("whitespace_stall"):
            parts.append(f"reply stalled in whitespace ({self.reply.get('trailing_whitespace')} chars)")
        return ", ".join(parts)


def describe_interruption(calls: list[CallTrace]) -> str:
    """Where a local interruption stopped, in plain words, from this turn's calls."""
    if not calls:
        return "nothing was sent: the interruption came before any model call"
    call = calls[-1]
    last = call.attempts[-1] if call.attempts else None
    if call.final != "interrupted" or last is None:
        return f"between model calls: {call.operation} had {call.final or 'not finished'}; no call was in flight"
    reached = last.reached
    if reached in ("prepared", "connecting"):
        where = "the request was not sent"
    elif reached == "request_sent":
        where = "the request was sent but the API had not acknowledged it yet"
    elif reached == "acknowledged":
        where = "the API had received the request; no response had arrived"
    elif reached == "response_started":
        where = f"the response was partly received ({last.response_bytes} bytes) and discarded"
    else:
        where = "the response had been received; it was discarded before the host used it"
    retries = f" after {len(call.attempts) - 1} retr{'y' if len(call.attempts) == 2 else 'ies'}" if len(call.attempts) > 1 else ""
    return f"during {call.operation}{retries}: {where}"


def _audit_hook(event: str, args: tuple) -> None:
    if not event.startswith("http.client."):
        return
    attempt: AttemptTrace | None = getattr(_local, "attempt", None)
    if attempt is None:
        return
    if event == "http.client.connect":
        attempt.mark("connecting")
    elif event == "http.client.send":
        data = args[1] if len(args) > 1 else None
        # http.client sends the headers, then the body; the body's send completes the request.
        if attempt.body is None or data is attempt.body or data == attempt.body:
            attempt.mark("request_sent")


def _install_hook() -> None:
    global _hook_installed
    with _hook_lock:
        if not _hook_installed:
            sys.addaudithook(_audit_hook)
            _hook_installed = True


class tracking:
    """Context manager: route this thread's http.client events to ``attempt``."""

    def __init__(self, attempt: AttemptTrace):
        _install_hook()
        self.attempt = attempt

    def __enter__(self) -> AttemptTrace:
        self.previous = getattr(_local, "attempt", None)
        _local.attempt = self.attempt
        return self.attempt

    def __exit__(self, *exc: Any) -> None:
        _local.attempt = self.previous
