"""PDLt as a library (L120, docs/api.md). The REPL, headless runs and the MCP server go through these: one session
object, one exit-status mapping, one provider registry, one closed-sessions reader and one sandbox factory."""
from pdl_taskmaster.api.closed_sessions import ClosedTurn, closed_turns
from pdl_taskmaster.extensions.profiles import ProfileViolation
from pdl_taskmaster.extensions.task_types import register_task_type
from pdl_taskmaster.extensions.verifiers import register_verifier
from pdl_taskmaster.api.outcome import (
    EXIT_CANCELLED,
    EXIT_HARNESS_ERROR,
    EXIT_INTERRUPTED,
    EXIT_SUCCESS,
    EXIT_UNCONFIRMED,
    EXIT_UNVERIFIED,
    EXIT_WAITING_INPUT,
    TurnResult,
    exit_status,
)
from pdl_taskmaster.api.providers import create_worker, provider_names, register_provider
from pdl_taskmaster.api.sandbox import SandboxNotConfined, create_sandbox
from pdl_taskmaster.api.session import Session

__all__ = [
    "ClosedTurn", "closed_turns",
    "EXIT_CANCELLED", "EXIT_HARNESS_ERROR", "EXIT_INTERRUPTED", "EXIT_SUCCESS", "EXIT_UNCONFIRMED", "EXIT_UNVERIFIED",
    "EXIT_WAITING_INPUT", "TurnResult", "exit_status",
    "create_worker", "provider_names", "register_provider",
    "SandboxNotConfined", "create_sandbox",
    "Session",
    "ProfileViolation", "register_task_type", "register_verifier",
]
