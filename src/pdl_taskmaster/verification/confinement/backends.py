"""Confinement backends and fail-closed backend selection (ADR-0021).

A backend turns the session policy into OS-native confinement:

- ``probe()`` says whether it can work on this machine (cheap, no setup);
- ``prepare(policy, session)`` builds the session's native state once;
- ``launch(argv, cwd=, env=, limits=)`` starts one program under it;
- ``close()`` releases the session's native state.

Selection never degrades silently: when the requested backend cannot work, the
sandbox runs nothing (``sandbox_unavailable``). ``audit-only`` is the explicit
opt-out that runs programs under the in-process audit hook alone.
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

try:  # POSIX only; imported here, never inside a forked child (import locks)
    import resource
except ImportError:
    resource = None  # type: ignore[assignment]

from pdl_taskmaster.verification.confinement.policy import SandboxPolicy

MODE_ENV_VAR = "PDLT_SANDBOX"
MODES = ("auto", "native", "container", "audit-only")
_IS_WINDOWS = sys.platform == "win32" or os.name == "nt"
CREATE_SUSPENDED = 0x00000004


class SandboxUnavailable(Exception):
    """The requested confinement cannot be applied; nothing may run."""

    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


class LaunchError(Exception):
    """The program could not be started inside its containment; it never ran."""

    def __init__(self, failure: str) -> None:
        super().__init__(failure)
        self.failure = failure


@dataclass(frozen=True)
class RunLimits:
    timeout: float
    memory_limit_bytes: int
    cpu_seconds: int
    job: Any = None  # Windows Job Object handle owned by the caller, or None


def resolve_mode(mode: str | None = None) -> str:
    """The requested mode: the explicit value, else $PDLT_SANDBOX, else ``auto``.
    An unknown value is returned as given; selection then fails closed on it."""
    value = mode if mode is not None else os.environ.get(MODE_ENV_VAR, "")
    return (value or "auto").strip().lower()


class Backend:
    """Base backend: launches the program with subprocess.Popen under the POSIX
    resource limits (or the caller's Windows Job Object)."""

    name = "base"
    native = True  # False only for the audit-only opt-out
    job_active_process_limit = 0  # Windows: >0 caps the processes the run's Job Object admits

    def probe(self) -> str | None:
        """None when this backend can run on this machine, else the reason."""
        return None

    def prepare(self, policy: SandboxPolicy, session: Any) -> dict[str, Any]:
        """Build the session's native state. Returns facts for the SANDBOX_SESSION
        event; raises SandboxUnavailable when confinement cannot be applied."""
        self.policy = policy
        return {}

    def owner_record(self) -> dict[str, Any]:
        """What a stale-root sweep needs to release this session's native state."""
        return {}

    def command(self, argv: list[str], cwd: Path, limits: RunLimits) -> list[str]:
        return argv

    def child_setup(self) -> Callable[[], None] | None:
        """A callable run in the forked child after the resource limits, just before
        exec (POSIX only)."""
        return None

    def launch(self, argv: list[str], *, cwd: Path, env: dict[str, str], limits: RunLimits) -> Any:
        """Start the program. Returns a Popen-like object (communicate, kill, pid,
        returncode). Raises LaunchError when it could not start inside its
        containment."""
        preexec = None
        creationflags = 0
        if _IS_WINDOWS:
            if limits.job:
                # Start suspended and resume only once the process is in the job, so
                # no instruction of it runs outside the memory limit and kill-on-close.
                creationflags = CREATE_SUSPENDED
        else:
            setup = self.child_setup()
            memory, cpu = limits.memory_limit_bytes, limits.cpu_seconds

            def preexec() -> None:
                # CPU-time backstop: the wall-clock timeout is enforced by the host, so a
                # program orphaned by a killed host would otherwise run on unbounded (its
                # own session is outside the host's process group). The kernel stops it.
                for limit, value in ((resource.RLIMIT_AS, memory), (resource.RLIMIT_CPU, cpu)):
                    try:
                        resource.setrlimit(limit, (value, value + (1 if limit == resource.RLIMIT_CPU else 0)))
                    except (ValueError, OSError):
                        pass
                if setup is not None:
                    setup()  # an exception here fails the launch: the program never runs

        proc = subprocess.Popen(
            self.command(argv, cwd, limits),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            preexec_fn=preexec,
            start_new_session=not _IS_WINDOWS,
            creationflags=creationflags,
        )
        if _IS_WINDOWS and limits.job:
            import ctypes

            from pdl_taskmaster.verification import sandbox as _sb

            failure = None
            if not _sb.kernel32().AssignProcessToJobObject(limits.job, int(proc._handle)):
                failure = f"job_assign_failed_{ctypes.get_last_error()}"
            elif not _sb.resume_process(proc):
                failure = "process_resume_failed"
            if failure:
                # The process never ran outside the job: it is still suspended.
                proc.kill()
                proc.communicate()
                raise LaunchError(failure)
        return proc

    def terminate(self) -> None:
        """Stop whatever the backend runs beyond the launched process (called after
        the host kills a program's process tree). Never raises."""

    def close(self) -> None:
        """Release the session's native state. Idempotent; never raises."""

    @classmethod
    def sweep(cls, root: Path, owner: dict[str, Any]) -> None:
        """Release a dead owner's native state recorded in its owner.json."""


class AuditOnlyBackend(Backend):
    """The explicit opt-out: the in-process audit hook and resource limits only."""

    name = "audit-only"
    native = False


class UnavailableBackend(Backend):
    """Stands in for a backend that cannot exist here; probes as unavailable."""

    def __init__(self, name: str, reason: str) -> None:
        self.name = name
        self._reason = reason

    def probe(self) -> str | None:
        return self._reason

    def prepare(self, policy: SandboxPolicy, session: Any) -> dict[str, Any]:
        raise SandboxUnavailable(self._reason)


def _native_backend() -> Backend:
    if sys.platform.startswith("linux"):
        from pdl_taskmaster.verification.confinement.landlock import LandlockBackend

        return LandlockBackend()
    if sys.platform == "darwin":
        from pdl_taskmaster.verification.confinement.seatbelt import SeatbeltBackend

        return SeatbeltBackend()
    if sys.platform == "win32":
        from pdl_taskmaster.verification.confinement.appcontainer import AppContainerBackend

        return AppContainerBackend()
    return UnavailableBackend("native", f"no native confinement backend for platform {sys.platform}")


def select_backend(mode: str | None = None) -> Backend:
    """A fresh, unprepared backend for the mode (one per session)."""
    resolved = resolve_mode(mode)
    if resolved in ("auto", "native"):
        return _native_backend()
    if resolved == "audit-only":
        return AuditOnlyBackend()
    if resolved == "container":
        return UnavailableBackend("container", "the container backend is not available in this build")
    return UnavailableBackend(resolved, f"unknown sandbox mode {resolved!r} (expected one of {', '.join(MODES)})")


def sweep_owner(root: Path, owner: dict[str, Any]) -> None:
    """Release the native state a dead session's owner record names."""
    for cls in _sweepable_backends():
        if owner.get("backend") == cls.name:
            cls.sweep(root, owner)


def _sweepable_backends() -> list[type[Backend]]:
    from pdl_taskmaster.verification.confinement.appcontainer import AppContainerBackend

    return [AppContainerBackend]
