"""macOS Seatbelt backend: ``/usr/bin/sandbox-exec`` with a deny-by-default profile.

The profile is built once per session, modeled on the Codex CLI and Chromium base
policies. Every path reaches it as a ``-D`` parameter (never interpolated into the
profile text), after realpath: ``/var/folders`` is ``/private/var/folders``.

- process-exec: the interpreter literal(s) only; no process-fork.
- file-read*: the policy's read roots (subpaths, or literals for files).
- file-read* file-write*: the session's work directory.
- file-read-metadata and sysctl-read everywhere; no network*.

sandbox-exec is deprecated but still supported (it is how Codex CLI, Chromium and
Bazel confine processes on macOS). macOS does not enforce RLIMIT_AS, so the memory
limit is not enforced on this backend; the wall-clock and CPU limits are.
"""
from __future__ import annotations

import hashlib
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from pdl_taskmaster.verification.confinement.backends import Backend, RunLimits, SandboxUnavailable
from pdl_taskmaster.verification.confinement.policy import SandboxPolicy

SANDBOX_EXEC = "/usr/bin/sandbox-exec"
_SELF_TEST_SECONDS = 15.0


def build_profile(policy: SandboxPolicy) -> tuple[str, dict[str, str]]:
    """The SBPL profile and its ``-D`` parameters for one session policy."""
    params: dict[str, str] = {}
    lines = [
        "(version 1)",
        "(deny default)",
        "(allow file-read-metadata)",
        "(allow sysctl-read)",
        "(allow signal (target self))",
        "(allow process-info* (target self))",
    ]

    def param(prefix: str, path: Path) -> str:
        key = f"{prefix}_{sum(1 for k in params if k.startswith(prefix + '_'))}"
        params[key] = str(path)
        return f'(param "{key}")'

    for path in policy.exec_paths:
        lines.append(f"(allow process-exec (literal {param('EXEC', path)}))")
    for path in policy.read_roots:
        kind = "subpath" if path.is_dir() else "literal"
        lines.append(f"(allow file-read* ({kind} {param('READ', path)}))")
    for path in policy.write_roots:
        lines.append(f"(allow file-read* file-write* (subpath {param('WRITE', path)}))")
    lines.append('(allow file-read* file-write-data file-ioctl (literal "/dev/null"))')
    if policy.processes:
        lines.append("(allow process-fork)")
    if policy.network:
        lines.append("(allow network*)")
    return "\n".join(lines) + "\n", params


def sandbox_exec_argv(profile: str, params: dict[str, str], argv: list[str]) -> list[str]:
    command = [SANDBOX_EXEC, "-p", profile]
    for key, value in params.items():
        command += ["-D", f"{key}={value}"]
    return command + list(argv)


class SeatbeltBackend(Backend):
    name = "seatbelt"

    def __init__(self) -> None:
        self.profile = ""
        self.params: dict[str, str] = {}

    def probe(self) -> str | None:
        if sys.platform != "darwin":
            return f"Seatbelt is macOS-only (platform {sys.platform})"
        if not os.access(SANDBOX_EXEC, os.X_OK):
            return f"{SANDBOX_EXEC} is not available"
        return None

    def prepare(self, policy: SandboxPolicy, session: Any) -> dict[str, Any]:
        self.policy = policy
        reason = self.probe()
        if reason is not None:
            raise SandboxUnavailable(reason)
        self.profile, self.params = build_profile(policy)
        # A no-op run under the profile: a profile the OS rejects, or one that keeps
        # the interpreter from starting, fails the session closed here, once.
        try:
            check = subprocess.run(
                sandbox_exec_argv(self.profile, self.params, [str(policy.interpreter), "-I", "-S", "-c", "pass"]),
                cwd=policy.write_roots[0],
                env={"PATH": "/usr/bin:/bin"},
                stdin=subprocess.DEVNULL,
                capture_output=True,
                timeout=_SELF_TEST_SECONDS,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise SandboxUnavailable(f"sandbox-exec self-test failed: {exc}") from exc
        if check.returncode != 0:
            detail = check.stderr.decode("utf-8", "replace").strip()[-300:]
            raise SandboxUnavailable(f"sandbox-exec self-test exited {check.returncode}: {detail}")
        return {
            "os": f"macOS {platform.mac_ver()[0]}",
            "profile_sha256": hashlib.sha256(self.profile.encode("utf-8")).hexdigest()[:16],
        }

    def command(self, argv: list[str], cwd: Path, limits: RunLimits) -> list[str]:
        return sandbox_exec_argv(self.profile, self.params, argv)
