"""The execution sandbox, made in one place (ADR-0021). The engine builds its own per session; the MCP server and
library callers that run programs outside a session use this factory."""
from __future__ import annotations

from typing import Any


class SandboxNotConfined(RuntimeError):
    """Confinement was required and the chosen mode runs programs without OS-native confinement."""


def create_sandbox(mode: str = "auto", *, label: str, require_confined: bool = False, **settings: Any) -> Any:
    """An ExecutionSandbox in ``mode``. ``require_confined`` refuses the audit-only opt-out (L121 E-4)."""
    from pdl_taskmaster.verification.sandbox import ExecutionSandbox

    sandbox = ExecutionSandbox(mode=mode, label=label, **settings)
    if require_confined and not sandbox.confined:
        raise SandboxNotConfined(f"programs run only under OS-native confinement; --sandbox {mode} is refused")
    return sandbox
