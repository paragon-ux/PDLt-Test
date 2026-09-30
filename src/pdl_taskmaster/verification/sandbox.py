from __future__ import annotations

import ctypes
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional


# Windows Win32 Job Object Constants and Structures
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
NORMAL_PRIORITY_CLASS = 0x00000020
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
IDLE_PRIORITY_CLASS = 0x00000040
JobObjectExtendedLimitInformation = 9

_IS_WINDOWS = sys.platform == "win32" or os.name == "nt"

if _IS_WINDOWS:
    class IO_COUNTERS(ctypes.Structure):
        _fields_ = [
            ("ReadOperationCount", ctypes.c_uint64),
            ("WriteOperationCount", ctypes.c_uint64),
            ("OtherOperationCount", ctypes.c_uint64),
            ("ReadTransferCount", ctypes.c_uint64),
            ("WriteTransferCount", ctypes.c_uint64),
            ("OtherTransferCount", ctypes.c_uint64),
        ]

    class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("PerProcessUserTimeLimit", ctypes.c_int64),
            ("PerJobUserTimeLimit", ctypes.c_int64),
            ("LimitFlags", ctypes.c_uint32),
            ("MinimumWorkingSetSize", ctypes.c_size_t),
            ("MaximumWorkingSetSize", ctypes.c_size_t),
            ("ActiveProcessLimit", ctypes.c_uint32),
            ("Affinity", ctypes.c_size_t),
            ("PriorityClass", ctypes.c_uint32),
            ("SchedulingClass", ctypes.c_uint32),
        ]

    class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("BasicLimitInformation", JOBOBJECT_BASIC_LIMIT_INFORMATION),
            ("IoInfo", IO_COUNTERS),
            ("ProcessMemoryLimit", ctypes.c_size_t),
            ("JobMemoryLimit", ctypes.c_size_t),
            ("PeakProcessMemoryLimit", ctypes.c_size_t),
            ("PeakJobMemoryLimit", ctypes.c_size_t),
        ]


# Environment variables model-authored code may see. Everything else, including
# API keys and tokens, is withheld (GUARD-04 containment).
_ENV_ALLOWLIST = ("PATH", "SYSTEMROOT", "TEMP", "TMP")

# Defense in depth, not a VM boundary: an in-process audit hook denies outbound
# network and process creation. It cannot be removed once installed.
_NETWORK_BLOCK_PRELUDE = """
# Deterministic Sandbox Isolation Prelude
import sys as _sys
_DENIED_EVENTS = frozenset({
    "socket.connect", "socket.bind", "socket.getaddrinfo", "socket.gethostbyname",
    "socket.sendto", "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn",
    "os.spawn", "os.fork", "os.forkpty",
})
def _sandbox_audit(event, args):
    if event in _DENIED_EVENTS:
        raise PermissionError("Network access and process creation are strictly disabled inside ExecutionSandbox (" + event + ")")
_sys.addaudithook(_sandbox_audit)
"""


STEP_BUDGET_EXIT_CODE = 125
_STEP_BUDGET_MARKER = "PDLT_STEP_BUDGET_EXCEEDED"

# Deterministic complexity budget: one step is one executed bytecode instruction
# of the script's own code (including code it runs through exec and functions it
# hands to library calls), so loops written on one line and comprehensions are
# counted too. Code inside the standard library is not counted: importing a module
# is not the task's complexity. Built-ins and the standard library are bounded by
# the wall-clock limit instead. On the first step past the limit the process exits
# at once, so the program cannot catch it.
_STEP_BUDGET_PRELUDE = """
import sys as _sys, os as _os, threading as _threading
_STEP_LIMIT = {limit}
_STDLIB = _os.path.dirname(_os.__file__)
_steps = [0]
def _count(frame, event, arg):
    if event == "opcode":
        _steps[0] += 1
        if _steps[0] > _STEP_LIMIT:
            _sys.stdout.flush()
            _sys.stderr.write("{marker}: more than %d steps\\n" % _STEP_LIMIT)
            _sys.stderr.flush()
            _os._exit({exit_code})
    return _count
def _step_trace(frame, event, arg):
    filename = frame.f_code.co_filename
    if filename.startswith(_STDLIB) or filename.startswith("<frozen"):
        return None
    frame.f_trace_lines = False
    frame.f_trace_opcodes = True
    return _count
_sys.settrace(_step_trace)
_top = _sys._getframe()  # the script's own top-level frame
_top.f_trace_lines = False
_top.f_trace_opcodes = True
_top.f_trace = _count
del _top
_threading.settrace(_step_trace)
def _step_guard(event, args):
    if event in ("sys.settrace", "sys.setprofile"):
        caller = _sys._getframe(1)  # sys.settrace is C code: frame 1 is its Python caller
        if not (caller.f_code.co_name == "_bootstrap_inner" and caller.f_code.co_filename == _threading.__file__):
            raise PermissionError("The step counter cannot be changed inside ExecutionSandbox (" + event + ")")
_sys.addaudithook(_step_guard)
"""


@dataclass(frozen=True)
class ExecutionBudget:
    """Resources the sandbox grants one task tier; enforced and declared from one place."""

    tier: str
    step_limit: int
    timeout_seconds: float  # wall-clock safety limit behind the step budget
    memory_limit_bytes: int


_MB = 1024 * 1024

# Per-tier budgets routed by System 1 (ExecutionProfileRecipe predicts the step
# complexity). Generic and fixed: no task, prompt or problem class has its own entry.
# The wall-clock limit is only a safety net for work inside built-in functions.
EXECUTION_BUDGETS: dict[str, ExecutionBudget] = {
    "MINIMAL": ExecutionBudget("MINIMAL", 100_000, 30.0, 256 * _MB),
    "STANDARD": ExecutionBudget("STANDARD", 10_000_000, 30.0, 256 * _MB),
    "HEAVY_COMPUTE": ExecutionBudget("HEAVY_COMPUTE", 100_000_000, 120.0, 512 * _MB),
}
DEFAULT_BUDGET = EXECUTION_BUDGETS["STANDARD"]


@dataclass(frozen=True)
class SandboxResult:
    """Outcome of sandboxed script execution."""
    stdout: str
    stderr: str
    exit_code: int
    duration_ms: float
    timed_out: bool = False
    oom_killed: bool = False
    error: Optional[str] = None
    step_budget_exceeded: bool = False

    @property
    def success(self) -> bool:
        return (
            self.exit_code == 0 and not self.timed_out and not self.oom_killed
            and not self.step_budget_exceeded and self.error is None
        )



class ExecutionSandbox:
    """OS-native deterministic execution sandbox (P1).

    Conformant to ADR-0013:
    - Zero-dependency local process isolation (Windows Job Objects on Windows,
      setrlimit on POSIX).
    - Ephemeral scratchpad filesystem containment; standard library only (``-I -S``).
    - Deterministic wall-clock timeout and memory ceilings.
    - Withheld environment: only an allowlist of variables is passed (no secrets).
    - Outbound network and process creation denied by an audit hook (defense in depth,
      not a VM boundary).
    """

    DEFAULT_TIMEOUT_SECONDS: float = 5.0
    DEFAULT_MEMORY_LIMIT_BYTES: int = 256 * 1024 * 1024  # 256 MB

    def __init__(
        self,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        memory_limit_bytes: int = DEFAULT_MEMORY_LIMIT_BYTES,
        allow_network: bool = False,
    ) -> None:
        self.timeout_seconds = float(timeout_seconds)
        self.memory_limit_bytes = int(memory_limit_bytes)
        self.allow_network = allow_network

    def decision_state(self) -> dict[str, str]:
        """The sandbox as System 1 routing state: what the environment provides and
        what one step is, from the same source the sandbox enforces."""
        version = ".".join(str(part) for part in sys.version_info[:2])
        return {
            "execution_environment": (
                f"Python {version} interpreter with the standard library only; third-party packages are not "
                f"installed; network access is {'enabled' if self.allow_network else 'disabled'}; each program "
                "runs in an empty temporary directory with empty standard input."
            ),
            "step_definition": (
                "One step is one executed Python bytecode instruction of the program's own code, including every "
                "loop or comprehension iteration; work inside the standard library and built-in functions is not "
                "counted."
            ),
        }

    def describe(self, budget: ExecutionBudget | None = None) -> list[dict[str, str]]:
        """The execution environment exactly as model-authored code will see it.

        This is the AVAILABLE_EXECUTION_TOOLS declaration: factual capabilities of
        the session sandbox under the task's budget, never task guidance.
        """
        version = ".".join(str(part) for part in sys.version_info[:2])
        timeout = budget.timeout_seconds if budget else self.timeout_seconds
        megabytes = (budget.memory_limit_bytes if budget else self.memory_limit_bytes) // (1024 * 1024)
        steps = (
            f"Each script may execute at most {budget.step_limit:,} steps, where one step is one executed Python "
            "bytecode instruction of the script's own code, including every loop or comprehension iteration, code "
            "run through exec, and functions the script passes to library calls. Code inside the standard library "
            "and built-in functions is not counted in steps. A script that exceeds the step budget is stopped. "
            f"Everything, including uncounted work, is bounded by a {timeout:g}-second wall-clock limit. "
            if budget else f"Each script has a {timeout:g}-second time limit. "
        )
        return [
            {
                "name": "python",
                "description": (
                    f"Python {version} with the standard library only; third-party packages are not installed. "
                    "The host runs the deliverable as a script when the whole deliverable is Python source; otherwise it "
                    "runs every ```python fenced block as a separate script, in an empty temporary directory. "
                    + steps
                    + f"Memory is limited to {megabytes} MB. Standard input is empty. Standard output, standard error "
                    "and the exit status are captured by the host."
                ),
            }
        ]

    def _create_windows_job(self, memory_limit_bytes: int) -> int | None:
        """Create and configure a Windows Job Object with memory and process lifecycle limits."""
        if not _IS_WINDOWS:
            return None
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        h_job = kernel32.CreateJobObjectW(None, None)
        if not h_job:
            return None

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = (
            JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            | JOB_OBJECT_LIMIT_JOB_MEMORY
            | JOB_OBJECT_LIMIT_PROCESS_MEMORY
            | JOB_OBJECT_LIMIT_PRIORITY_CLASS
        )
        info.BasicLimitInformation.PriorityClass = BELOW_NORMAL_PRIORITY_CLASS
        info.JobMemoryLimit = memory_limit_bytes
        info.ProcessMemoryLimit = memory_limit_bytes

        success = kernel32.SetInformationJobObject(
            h_job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not success:
            kernel32.CloseHandle(h_job)
            return None
        return h_job

    def run_code(
        self,
        code: str,
        *,
        timeout: float | None = None,
        memory_limit: int | None = None,
        env: dict[str, str] | None = None,
        step_limit: int | None = None,
    ) -> SandboxResult:
        """Execute a Python snippet in an isolated ephemeral scratchpad with OS-native limits.

        ``step_limit`` enforces the deterministic step budget (executed Python lines)."""
        effective_timeout = timeout if timeout is not None else self.timeout_seconds
        effective_memory = memory_limit if memory_limit is not None else self.memory_limit_bytes

        with tempfile.TemporaryDirectory(prefix="pdl_sandbox_") as scratchpad:
            scratchpad_path = Path(scratchpad).resolve()
            entry_file = scratchpad_path / "_entry.py"

            content_parts: list[str] = []
            if not self.allow_network:
                content_parts.append(_NETWORK_BLOCK_PRELUDE)
            if step_limit is not None:
                content_parts.append(_STEP_BUDGET_PRELUDE.format(
                    limit=int(step_limit), marker=_STEP_BUDGET_MARKER, exit_code=STEP_BUDGET_EXIT_CODE,
                ))
            content_parts.append(code)
            entry_file.write_text("\n".join(content_parts), encoding="utf-8")

            result = self._execute_process(
                [sys.executable, "-I", "-S", "-X", "utf8", str(entry_file)],
                cwd=scratchpad_path,
                timeout=effective_timeout,
                memory_limit_bytes=effective_memory,
                env=env,
            )
            if result.exit_code == STEP_BUDGET_EXIT_CODE and _STEP_BUDGET_MARKER in result.stderr:
                from dataclasses import replace

                result = replace(result, step_budget_exceeded=True)
            return result

    def run_script(
        self,
        script_path: str | Path,
        args: list[str] | None = None,
        *,
        timeout: float | None = None,
        memory_limit: int | None = None,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        """Execute an existing script within the sandboxed environment."""
        effective_timeout = timeout if timeout is not None else self.timeout_seconds
        effective_memory = memory_limit if memory_limit is not None else self.memory_limit_bytes
        resolved_script = Path(script_path).resolve()

        with tempfile.TemporaryDirectory(prefix="pdl_sandbox_") as scratchpad:
            scratchpad_path = Path(scratchpad).resolve()
            cmd = [sys.executable, "-I", "-S", "-X", "utf8", str(resolved_script)]
            if args:
                cmd.extend(args)

            return self._execute_process(
                cmd,
                cwd=scratchpad_path,
                timeout=effective_timeout,
                memory_limit_bytes=effective_memory,
                env=env,
            )

    def _execute_process(
        self,
        cmd: list[str],
        *,
        cwd: Path,
        timeout: float,
        memory_limit_bytes: int,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        base_env = {k: os.environ[k] for k in _ENV_ALLOWLIST if k in os.environ}
        base_env["PYTHONIOENCODING"] = "utf-8"
        base_env["PYTHONUNBUFFERED"] = "1"
        if _IS_WINDOWS:
            base_env.setdefault("SYSTEMROOT", "C:\\Windows")
        if env:
            base_env.update(env)

        h_job = None
        kernel32 = None
        if _IS_WINDOWS:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            h_job = self._create_windows_job(memory_limit_bytes)

        preexec = None
        if not _IS_WINDOWS:
            def _preexec_posix():
                import resource
                os.setsid()
                try:
                    resource.setrlimit(resource.RLIMIT_AS, (memory_limit_bytes, memory_limit_bytes))
                except (ValueError, OSError):
                    pass
            preexec = _preexec_posix

        start_time = time.perf_counter()
        proc = None
        timed_out = False
        stdout_text = ""
        stderr_text = ""
        exit_code = -1

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=base_env,
                preexec_fn=preexec,
            )

            if _IS_WINDOWS and h_job and kernel32:
                # Assign process to Job Object immediately
                assign_ok = kernel32.AssignProcessToJobObject(h_job, proc._handle)
                if not assign_ok and proc.poll() is None:
                    # Process is still running but could not be assigned
                    err_code = ctypes.get_last_error()
                    kernel32.TerminateJobObject(h_job, 1)
                    proc.kill()
                    return SandboxResult(
                        stdout="",
                        stderr=f"Failed to assign process to JobObject (err={err_code})",
                        exit_code=-1,
                        duration_ms=(time.perf_counter() - start_time) * 1000.0,
                        error=f"job_assign_failed_{err_code}",
                    )

            raw_out, raw_err = proc.communicate(timeout=timeout)
            stdout_text = raw_out.decode("utf-8", errors="replace")
            stderr_text = raw_err.decode("utf-8", errors="replace")
            exit_code = proc.returncode

        except subprocess.TimeoutExpired:
            timed_out = True
            if _IS_WINDOWS and h_job and kernel32:
                kernel32.TerminateJobObject(h_job, 124)
            if proc is not None:
                try:
                    if not _IS_WINDOWS:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    else:
                        proc.kill()
                    raw_out, raw_err = proc.communicate()
                    stdout_text = raw_out.decode("utf-8", errors="replace")
                    stderr_text = raw_err.decode("utf-8", errors="replace")
                except Exception:
                    pass
            exit_code = 124

        except Exception as exc:
            if proc is not None:
                try:
                    proc.kill()
                except Exception:
                    pass
            return SandboxResult(
                stdout="",
                stderr=str(exc),
                exit_code=-1,
                duration_ms=(time.perf_counter() - start_time) * 1000.0,
                error=f"execution_exception: {exc}",
            )

        finally:
            if _IS_WINDOWS and h_job and kernel32:
                kernel32.CloseHandle(h_job)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Memory limit exhaustion detection
        oom_killed = False
        lower_err = stderr_text.lower()
        if "memoryerror" in lower_err or "out of memory" in lower_err or "cannot allocate memory" in lower_err:
            oom_killed = True
        elif exit_code in (-1073741545, 3221225751, -1073741801, 3221225495):  # Win32 STATUS_NO_MEMORY / STATUS_PAGEFILE_QUOTA
            oom_killed = True
        elif not _IS_WINDOWS and exit_code in (-9, 137, -11, 139) and not timed_out:
            # POSIX RLIMIT_AS SIGKILL (-9 / 137) or SIGSEGV (-11 / 139 on mmap/brk failure)
            oom_killed = True

        return SandboxResult(
            stdout=stdout_text,
            stderr=stderr_text,
            exit_code=exit_code,
            duration_ms=duration_ms,
            timed_out=timed_out,
            oom_killed=oom_killed,
        )
