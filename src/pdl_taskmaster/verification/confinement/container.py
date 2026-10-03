"""Container backend (opt-in, strict): docker or podman, one container per session.

The runtime is ``$PDLT_CONTAINER_RUNTIME`` or the first of docker, podman on PATH.
On the session's first run a long-lived container starts with no network, a
read-only root, no capabilities, no privilege gain and a process cap; only the
session's work directory is mounted (at /work). The image tag is the host's
Python minor version, so the standard library matches; its digest is recorded.

Each run is ``exec`` into that container, under ``timeout -s KILL`` as a backstop
to the host's own wall clock. The per-run memory limit is an RLIMIT_AS line at the
top of the program's entry file (the container's --memory caps the largest tier).
close() removes the container; containers whose owner process is dead are swept
by label. Expect ~0.5-2 s once per session and ~100-300 ms per run: this mode is
for CI and unattended catalogue runs.
"""
from __future__ import annotations

import math
import os
import shutil
import socket
import subprocess
import sys
from pathlib import Path
from typing import Any

from pdl_taskmaster.verification.confinement.backends import Backend, RunLimits, SandboxUnavailable
from pdl_taskmaster.verification.confinement.policy import SandboxPolicy

RUNTIME_ENV_VAR = "PDLT_CONTAINER_RUNTIME"
IMAGE_ENV_VAR = "PDLT_CONTAINER_IMAGE"
CONTAINER_WORK = "/work"
SANDBOX_LABEL = "pdlt.sandbox"
OWNER_LABEL = "pdlt.owner"
PIDS_LIMIT = 64
_START_SECONDS = 600.0  # the first session on a machine may pull the image
_CONTROL_SECONDS = 30.0
# Host-side variables that describe the host's own OS; the container has its own.
_HOST_ONLY_ENV = {"PATH", "PATHEXT", "COMSPEC", "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE"}


def find_runtime() -> str | None:
    configured = os.environ.get(RUNTIME_ENV_VAR, "").strip()
    if configured:
        return shutil.which(configured) or (configured if os.path.isfile(configured) else None)
    return shutil.which("docker") or shutil.which("podman")


def default_image() -> str:
    return os.environ.get(IMAGE_ENV_VAR, "").strip() or "python:{}.{}-slim".format(*sys.version_info[:2])


def container_user() -> str:
    """The host user on Linux (files in the mounted work directory stay the host
    user's); nobody elsewhere (Docker Desktop maps mount ownership itself)."""
    if sys.platform.startswith("linux"):
        return f"{os.getuid()}:{os.getgid()}"
    return "65534:65534"


def owner_label() -> str:
    return f"{socket.gethostname()}:{os.getpid()}"


def run_argv(runtime: str, *, sid: str, work: Path, image: str, memory_bytes: int) -> list[str]:
    return [
        runtime, "run", "-d", "--rm",
        "--network", "none",
        "--read-only", "--tmpfs", "/tmp",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--pids-limit", str(PIDS_LIMIT),
        "--memory", f"{max(1, memory_bytes // (1024 * 1024))}m",
        "--user", container_user(),
        "--label", f"{SANDBOX_LABEL}={sid}",
        "--label", f"{OWNER_LABEL}={owner_label()}",
        "-v", f"{work}:{CONTAINER_WORK}",
        image, "sleep", "infinity",
    ]


def exec_argv(runtime: str, container: str, *, work: Path, argv: list[str], cwd: Path, env: dict[str, str],
              timeout: float) -> list[str]:
    """``exec`` the program in the container: the host interpreter becomes the image's
    ``python``, and host paths under the work directory become /work paths."""
    def inside(value: str) -> str:
        return value.replace(str(work), CONTAINER_WORK).replace("\\", "/") if str(work) in value else value

    command = [runtime, "exec", "-w", inside(str(cwd))]
    for key, value in env.items():
        if key.upper() not in _HOST_ONLY_ENV:
            command += ["-e", f"{key}={inside(value)}"]
    return command + [container, "timeout", "-s", "KILL", str(int(math.ceil(timeout)) + 1), "python", *argv[1:]]


def _control(runtime: str, *args: str, timeout: float = _CONTROL_SECONDS) -> subprocess.CompletedProcess:
    return subprocess.run([runtime, *args], stdin=subprocess.DEVNULL, capture_output=True, text=True,
                          timeout=timeout)


def _pid_alive(pid: int) -> bool:
    from pdl_taskmaster.verification.sandbox import _pid_alive as alive

    return alive(pid)


def sweep_stale_containers(runtime: str) -> list[str]:
    """Remove this host's sandbox containers whose owner process is gone."""
    removed: list[str] = []
    try:
        listed = _control(runtime, "ps", "-aq", "--filter", f"label={SANDBOX_LABEL}")
        for container in listed.stdout.split():
            owner = _control(runtime, "inspect", "--format", "{{index .Config.Labels \"%s\"}}" % OWNER_LABEL,
                             container).stdout.strip()
            host, _, pid = owner.rpartition(":")
            if host == socket.gethostname() and pid.isdigit() and int(pid) != os.getpid() and not _pid_alive(int(pid)):
                _control(runtime, "rm", "-f", container)
                removed.append(container)
    except (OSError, subprocess.SubprocessError):
        pass
    return removed


class ContainerBackend(Backend):
    name = "container"
    entry_limits = True  # memory and CPU limits are set inside the program's own process

    def __init__(self) -> None:
        self.runtime: str | None = None
        self.container: str | None = None
        self.work: Path | None = None

    def probe(self) -> str | None:
        runtime = find_runtime()
        if runtime is None:
            return (f"no container runtime found (install docker or podman, or set {RUNTIME_ENV_VAR})")
        try:
            check = _control(runtime, "version", "--format", "{{.Server.Version}}", timeout=15.0)
        except (OSError, subprocess.SubprocessError) as exc:
            return f"container runtime {runtime} is not usable ({exc})"
        if check.returncode != 0:
            return f"container runtime {runtime} is not usable ({check.stderr.strip()[-200:]})"
        self.runtime = runtime
        return None

    def prepare(self, policy: SandboxPolicy, session: Any) -> dict[str, Any]:
        from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS

        self.policy = policy
        reason = self.probe()
        if reason is not None:
            raise SandboxUnavailable(reason)
        assert self.runtime is not None
        sweep_stale_containers(self.runtime)
        self.work = policy.write_roots[0]
        image = default_image()
        memory = max(budget.memory_limit_bytes for budget in EXECUTION_BUDGETS.values())
        try:
            started = _control(self.runtime, *run_argv(self.runtime, sid=session.sid, work=self.work, image=image,
                                                       memory_bytes=memory)[1:], timeout=_START_SECONDS)
        except (OSError, subprocess.SubprocessError) as exc:
            raise SandboxUnavailable(f"cannot start the sandbox container ({exc})") from exc
        if started.returncode != 0 or not started.stdout.strip():
            raise SandboxUnavailable(f"cannot start the sandbox container: {started.stderr.strip()[-300:]}")
        self.container = started.stdout.strip().splitlines()[-1]
        session.write_owner(container=self.container, runtime=self.runtime)
        facts: dict[str, Any] = {"runtime": os.path.basename(self.runtime), "image": image,
                                 "container": self.container[:12]}
        try:
            facts["image_id"] = _control(self.runtime, "inspect", "--format", "{{.Image}}",
                                         self.container).stdout.strip()
            facts["image_digest"] = _control(self.runtime, "image", "inspect", "--format",
                                             "{{join .RepoDigests \",\"}}", image).stdout.strip().split(",")[0]
        except (OSError, subprocess.SubprocessError):
            pass
        return facts

    def owner_record(self) -> dict[str, Any]:
        return {"container": self.container, "runtime": self.runtime}

    def launch(self, argv: list[str], *, cwd: Path, env: dict[str, str], limits: RunLimits) -> Any:
        # The runtime's client is the host's tool, not model code: it gets the host
        # environment and no memory limit (the program's limits are in the entry file).
        assert self.runtime and self.container and self.work
        return subprocess.Popen(
            exec_argv(self.runtime, self.container, work=self.work, argv=argv, cwd=cwd, env=env,
                      timeout=limits.timeout),
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=os.name != "nt",
        )

    def terminate(self) -> None:
        """Killing the client does not stop the program inside: kill every process in
        the container except its init (which kill(-1) never signals)."""
        if self.runtime and self.container:
            try:
                _control(self.runtime, "exec", self.container, "sh", "-c", "kill -9 -1 2>/dev/null; true")
            except (OSError, subprocess.SubprocessError):
                pass

    def close(self) -> None:
        container, self.container = self.container, None
        if self.runtime and container:
            try:
                _control(self.runtime, "rm", "-f", container)
            except (OSError, subprocess.SubprocessError):
                pass

    @classmethod
    def sweep(cls, root: Path, owner: dict[str, Any]) -> None:
        runtime, container = owner.get("runtime"), owner.get("container")
        if not (isinstance(runtime, str) and isinstance(container, str) and os.path.basename(runtime).split(".")[0]
                in ("docker", "podman")):
            return
        try:
            label = _control(runtime, "inspect", "--format", "{{index .Config.Labels \"%s\"}}" % SANDBOX_LABEL,
                             container).stdout.strip()
            if label == root.name:  # only the container this root started
                _control(runtime, "rm", "-f", container)
        except (OSError, subprocess.SubprocessError):
            pass
