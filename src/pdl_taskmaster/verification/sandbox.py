from __future__ import annotations

import ctypes
import json
import math
import os
import secrets
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import weakref
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from pdl_taskmaster.verification.confinement.backends import (
    LaunchError,
    RunLimits,
    SandboxUnavailable,
    resolve_mode,
    select_backend,
    sweep_owner,
)
from pdl_taskmaster.verification.confinement.policy import build_policy


# Windows Win32 Job Object Constants and Structures
JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
JOB_OBJECT_LIMIT_JOB_MEMORY = 0x00000200
JOB_OBJECT_LIMIT_PROCESS_MEMORY = 0x00000100
JOB_OBJECT_LIMIT_PRIORITY_CLASS = 0x00000020
JOB_OBJECT_LIMIT_ACTIVE_PROCESS = 0x00000008
NORMAL_PRIORITY_CLASS = 0x00000020
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000
IDLE_PRIORITY_CLASS = 0x00000040
JobObjectExtendedLimitInformation = 9
CREATE_SUSPENDED = 0x00000004

_IS_WINDOWS = sys.platform == "win32" or os.name == "nt"

if _IS_WINDOWS:
    from ctypes import wintypes

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
            ("PeakProcessMemoryUsed", ctypes.c_size_t),
            ("PeakJobMemoryUsed", ctypes.c_size_t),
        ]

    _KERNEL32 = None
    _NTDLL = None

    def kernel32():
        """kernel32 with explicit prototypes. Without them ctypes passes and returns
        C ints, which truncates HANDLE values on 64-bit Windows."""
        global _KERNEL32
        if _KERNEL32 is None:
            k = ctypes.WinDLL("kernel32", use_last_error=True)
            k.CreateJobObjectW.argtypes = (ctypes.c_void_p, wintypes.LPCWSTR)
            k.CreateJobObjectW.restype = wintypes.HANDLE
            k.SetInformationJobObject.argtypes = (wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD)
            k.SetInformationJobObject.restype = wintypes.BOOL
            k.QueryInformationJobObject.argtypes = (
                wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.POINTER(wintypes.DWORD),
            )
            k.QueryInformationJobObject.restype = wintypes.BOOL
            k.AssignProcessToJobObject.argtypes = (wintypes.HANDLE, wintypes.HANDLE)
            k.AssignProcessToJobObject.restype = wintypes.BOOL
            k.TerminateJobObject.argtypes = (wintypes.HANDLE, wintypes.UINT)
            k.TerminateJobObject.restype = wintypes.BOOL
            k.CloseHandle.argtypes = (wintypes.HANDLE,)
            k.CloseHandle.restype = wintypes.BOOL
            k.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
            k.OpenProcess.restype = wintypes.HANDLE
            k.GetExitCodeProcess.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD))
            k.GetExitCodeProcess.restype = wintypes.BOOL
            _KERNEL32 = k
        return _KERNEL32

    def resume_process(proc: subprocess.Popen) -> bool:
        """Resume a process started with CREATE_SUSPENDED. Popen closes the primary
        thread's handle, so the whole process is resumed (ntdll NtResumeProcess)."""
        global _NTDLL
        if _NTDLL is None:
            _NTDLL = ctypes.WinDLL("ntdll")
            _NTDLL.NtResumeProcess.argtypes = (wintypes.HANDLE,)
            _NTDLL.NtResumeProcess.restype = ctypes.c_long  # NTSTATUS
        return _NTDLL.NtResumeProcess(int(proc._handle)) == 0


# Environment variables model-authored code may see. Everything else, including
# API keys and tokens, is withheld (GUARD-04 containment). The Windows entries are
# what the interpreter and the standard library need there (DLL and crypto loading,
# temporary files, executable lookup); variable names are case-insensitive there.
_ENV_ALLOWLIST = ("PATH", "TEMP", "TMP", "TMPDIR", "SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT")

# Windows exit statuses for an allocation failure (GetExitCodeProcess: unsigned).
_WINDOWS_OOM_EXIT_CODES = (
    0xC0000017,  # STATUS_NO_MEMORY
    0xC000012D,  # STATUS_COMMITMENT_LIMIT
    0xC0000007,  # STATUS_PAGEFILE_QUOTA
)

# Defense in depth, not a VM boundary: an in-process audit hook enforces the session
# policy inside the program's own interpreter. It cannot be removed once installed,
# but native code can step around it, so loading native code is denied too; the
# OS-native backend is the boundary that holds on its own.
_NETWORK_EVENTS = (
    "socket.connect", "socket.bind", "socket.getaddrinfo", "socket.gethostbyname",
    "socket.sendto", "socket.sendmsg",
)
_PROCESS_EVENTS = (
    "subprocess.Popen", "os.system", "os.exec", "os.posix_spawn", "os.spawn", "os.fork", "os.forkpty",
    "os.startfile", "_winapi.CreateProcess",
)
_SIGNAL_EVENTS = ("os.kill", "os.killpg")
_NATIVE_CODE_MODULES = ("ctypes", "_ctypes", "cffi", "_cffi_backend")
_NATIVE_CODE_EVENTS = ("sqlite3.enable_load_extension", "sqlite3.load_extension")

# Paths: writes stay inside the run directory; reads inside the run directory or the
# interpreter's standard library (its import path at startup). Each path is resolved
# with realpath and compared by commonpath, never by string prefix. An integer path
# is a descriptor that an already-checked open returned (os.open's dir_fd is not in
# its audit event; the native backend covers that case). A symbolic link may only
# point inside the run directory, by an absolute path or a relative one without
# "..", so moving it within the run directory never makes it point outside.
_POLICY_PRELUDE = r"""
import sys as _sys, os as _os
def _sandbox_policy(denied, native_modules, native_events):
    path_mod = _os.path
    def _resolve(path):
        return path_mod.normcase(path_mod.realpath(path))
    run_dir = _resolve(_os.getcwd())
    devices = [_os.devnull] + (["/dev/urandom"] if _os.name == "posix" else [])
    writable = [run_dir] + [_resolve(p) for p in devices[:1]]
    readable = [run_dir] + [_resolve(p) for p in _sys.path if p] + [_resolve(p) for p in devices]
    write_flags = _os.O_WRONLY | _os.O_RDWR | _os.O_APPEND | _os.O_CREAT | _os.O_TRUNC
    try:
        import fcntl as _fcntl
    except ImportError:
        _fcntl = None
    def descriptor_path(fd):
        if _sys.platform.startswith("linux"):
            return _os.readlink("/proc/self/fd/%d" % fd)
        if _fcntl is not None and hasattr(_fcntl, "F_GETPATH"):
            return _fcntl.fcntl(fd, _fcntl.F_GETPATH, bytes(1024)).split(b"\0", 1)[0].decode()
        raise OSError("descriptor path unavailable")
    def within(path, roots):
        for root in roots:
            try:
                if path_mod.commonpath((path, root)) == root:
                    return True
            except ValueError:  # another drive
                pass
        return False
    def check(event, path, write, dir_fd=None):
        if path is None or isinstance(path, int):
            return
        try:
            path = _os.fsdecode(_os.fspath(path))
            if dir_fd is not None and dir_fd >= 0 and not path_mod.isabs(path):  # -1: no dir_fd
                path = path_mod.join(descriptor_path(dir_fd), path)
            resolved = _resolve(path)
        except (OSError, TypeError, ValueError):
            resolved = None
        if resolved is None or not within(resolved, writable if write else readable):
            raise PermissionError(
                "File access outside the run directory is denied inside ExecutionSandbox (" + event + ": "
                + str(path) + ")"
            )
    def check_link_target(event, target, link, dir_fd):
        target = _os.fsdecode(_os.fspath(target))
        relative = not path_mod.isabs(target)
        if relative and ".." in target.replace("\\", "/").split("/"):
            raise PermissionError("Links that leave their directory are denied inside ExecutionSandbox (" + event + ")")
        link = _os.fsdecode(_os.fspath(link))
        base = path_mod.dirname(link)
        if dir_fd is not None and dir_fd >= 0 and not path_mod.isabs(link):
            base = path_mod.join(descriptor_path(dir_fd), base)
        check(event, path_mod.join(base, target) if relative else target, True)
    def hook(event, args):
        if event in denied:
            if event.startswith("socket."):
                kind = "Network access"
            elif event.startswith("os.kill"):
                kind = "Signalling other processes"
            else:
                kind = "Process creation"
            raise PermissionError(kind + " is strictly disabled inside ExecutionSandbox (" + event + ")")
        if event.startswith("ctypes.") or event in native_events or (
            event == "import" and (args[0] in native_modules or args[0].startswith("ctypes."))
        ):
            raise PermissionError("Loading native code is denied inside ExecutionSandbox (" + event + ")")
        if event == "open":
            path, mode, flags = args
            write = bool((flags or 0) & write_flags) or any(c in (mode or "") for c in "wax+")
            check(event, path, write)
        elif event in ("os.listdir", "os.scandir", "os.chdir", "os.listxattr", "os.getxattr"):
            check(event, args[0], False)
        elif event in ("os.remove", "os.rmdir", "shutil.rmtree"):
            check(event, args[0], True, args[1])
        elif event in ("os.mkdir", "os.chmod", "os.utime", "os.chown"):
            check(event, args[0], True, args[-1])
        elif event in ("os.truncate", "os.chflags", "os.lchflags", "os.setxattr", "os.removexattr",
                       "shutil.chown"):
            check(event, args[0], True)
        elif event in ("os.rename", "os.link"):
            check(event, args[0], True, args[2])
            check(event, args[1], True, args[3])
        elif event == "os.symlink":
            check(event, args[1], True, args[2])
            check_link_target(event, args[0], args[1], args[2])
        elif event in ("shutil.copyfile", "shutil.copymode", "shutil.copystat", "shutil.copytree"):
            check(event, args[0], False)
            check(event, args[1], True)
        elif event == "shutil.move":
            check(event, args[0], True)
            check(event, args[1], True)
        elif event == "shutil.make_archive":
            check(event, args[0], True)
            check(event, args[2] or ".", False)
        elif event == "shutil.unpack_archive":
            check(event, args[0], False)
            check(event, args[1] or ".", True)
        elif event == "sqlite3.connect":
            database = args[0]
            if isinstance(database, bytes):
                database = _os.fsdecode(database)
            if database in ("", ":memory:"):
                return
            check(event, database, True)
            if isinstance(database, str) and database.startswith("file:"):  # the URI form names a path too
                path = database[5:].split("?", 1)[0].split("#", 1)[0]
                if path.startswith("//"):
                    path = "/" + path[2:].partition("/")[2]
                if path not in ("", ":memory:"):
                    check(event, path, True)
    return hook
_sys.addaudithook(_sandbox_policy(frozenset(__DENIED__), frozenset(__NATIVE__), frozenset(__NATIVE_EVENTS__)))
del _sandbox_policy
"""


def _policy_prelude(*, allow_network: bool, allow_processes: bool) -> str:
    """The audit-hook prelude for one session policy."""
    denied = list(_SIGNAL_EVENTS)
    if not allow_network:
        denied += _NETWORK_EVENTS
    if not allow_processes:
        denied += _PROCESS_EVENTS
    source = (
        _POLICY_PRELUDE.replace("__DENIED__", repr(tuple(sorted(denied))))
        .replace("__NATIVE_EVENTS__", repr(_NATIVE_CODE_EVENTS))
        .replace("__NATIVE__", repr(_NATIVE_CODE_MODULES))
    )
    # Compiled under a "<frozen" name: the step counter skips it, and a denial's
    # traceback names the policy instead of quoting its source.
    return f"exec(compile({source!r}, '<frozen pdl_sandbox_policy>', 'exec'))"


# Resource limits set by the program's own interpreter first thing, for a backend
# whose launcher is not the program's parent (a container runtime's exec).
_ENTRY_LIMITS_PRELUDE = """
import resource as _resource
for _limit, _value in ((_resource.RLIMIT_AS, {memory}), (_resource.RLIMIT_CPU, {cpu})):
    try:
        _resource.setrlimit(_limit, (_value, _value + (1 if _limit == _resource.RLIMIT_CPU else 0)))
    except (ValueError, OSError):
        pass
del _resource, _limit, _value
"""


STEP_BUDGET_EXIT_CODE = 125
_STEP_BUDGET_MARKER = "PDLT_STEP_BUDGET_EXCEEDED"
_STEPS_USED_MARKER = "PDLT_STEPS_USED"
PROGRAM_FILENAME = "program.py"

# -I implies -E, so PYTHONIOENCODING / PYTHONUNBUFFERED in the environment are
# ignored: UTF-8 standard streams (not the Windows ANSI code page) and unbuffered
# output (kept when a timeout kills the program) are set on the command line.
_INTERPRETER_FLAGS = ("-I", "-S", "-X", "utf8", "-u")
# Seconds the host waits for the pipes to close after killing a timed-out program.
_KILL_GRACE_SECONDS = 5.0

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
# Steps used, reported at exit for telemetry. The reporter is compiled under a
# "<frozen" filename so the counter skips it; the host strips the line from stderr.
exec(compile(
    "import atexit\\n"
    "def _report_steps():\\n"
    "    _sys.stderr.write('{steps_marker}: %d\\\\n' % _steps[0])\\n"
    "    _sys.stderr.flush()\\n"
    "atexit.register(_report_steps)\\n",
    "<frozen pdl_step_report>", "exec",
))
"""


@dataclass(frozen=True)
class ExecutionBudget:
    """Resources the sandbox grants one task tier; enforced and declared from one place."""

    tier: str
    step_limit: int
    timeout_seconds: float  # wall-clock safety limit behind the step budget
    memory_limit_bytes: int
    repairs: int = 1  # verification repairs after the first EXECUTE (factual findings only)


_MB = 1024 * 1024

# Per-tier budgets routed by System 1 (ExecutionProfileRecipe predicts the step
# complexity). Generic and fixed: no task, prompt or problem class has its own entry.
# The wall-clock limit is only a safety net for work inside built-in functions.
EXECUTION_BUDGETS: dict[str, ExecutionBudget] = {
    "MINIMAL": ExecutionBudget("MINIMAL", 100_000, 30.0, 256 * _MB),
    "STANDARD": ExecutionBudget("STANDARD", 10_000_000, 30.0, 256 * _MB),
    "HEAVY_COMPUTE": ExecutionBudget("HEAVY_COMPUTE", 100_000_000, 120.0, 512 * _MB, repairs=2),
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
    steps_used: Optional[int] = None  # the program's own steps, when a step budget was set

    @property
    def success(self) -> bool:
        return (
            self.exit_code == 0 and not self.timed_out and not self.oom_killed
            and not self.step_budget_exceeded and self.error is None
        )


# Session roots live under the system temporary directory, outside every tree the
# referee reads (sessions, workspaces, results): a program can never plant a file
# where a deliverable or evidence is looked for.
SANDBOX_ROOT_DIRNAME = "pdlt-sandboxes"
OWNER_FILENAME = "owner.json"
# A root without a readable owner record is left alone this long (it may be one
# another process is creating right now).
_ORPHAN_GRACE_SECONDS = 24 * 3600
_STILL_ACTIVE = 259
_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def sandbox_base_dir() -> Path:
    return Path(tempfile.gettempdir()) / SANDBOX_ROOT_DIRNAME


def _pid_alive(pid: int) -> bool:
    """Whether a process with this id exists. Unknown counts as alive (never sweep
    what might still be in use)."""
    if pid <= 0:
        return False
    if _IS_WINDOWS:
        k32 = kernel32()
        handle = k32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return ctypes.get_last_error() != 87  # ERROR_INVALID_PARAMETER: no such process
        try:
            code = wintypes.DWORD()
            if not k32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return True
            return code.value == _STILL_ACTIVE
        finally:
            k32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        return True  # exists, owned by someone else
    return True


def _private_base_dir() -> Path:
    """The per-user sandbox base directory: created private, and refused when it is a
    link or another user's directory (a shared /tmp)."""
    base = sandbox_base_dir()
    base.mkdir(mode=0o700, exist_ok=True)
    if not _IS_WINDOWS:
        info = os.lstat(base)
        if os.path.islink(base) or info.st_uid != os.geteuid():
            raise OSError(f"{base} is not a directory owned by this user")
        if info.st_mode & 0o077:
            os.chmod(base, 0o700)
    return base


def _remove_tree(path: Path) -> None:
    shutil.rmtree(path, ignore_errors=True)


def _clear_directory(path: Path) -> None:
    """Delete everything inside ``path``, never following links. Never raises."""
    try:
        entries = list(os.scandir(path))
    except OSError:
        return
    for entry in entries:
        try:
            if entry.is_dir(follow_symlinks=False):
                shutil.rmtree(entry.path, ignore_errors=True)
            else:
                os.unlink(entry.path)
        except OSError:
            pass


def sweep_stale_roots(base: Path | None = None, *, cleanup: Any = None) -> list[Path]:
    """Remove session roots whose owner process is gone (a host killed before
    ``close()`` ran). ``cleanup(root, owner)`` releases what the owner record names beyond
    the directory. Returns the roots removed. Never raises."""
    base = base if base is not None else sandbox_base_dir()
    removed: list[Path] = []
    try:
        candidates = [Path(entry.path) for entry in os.scandir(base) if entry.is_dir(follow_symlinks=False)]
    except OSError:
        return removed
    now = time.time()
    for root in candidates:
        try:
            owner = json.loads((root / OWNER_FILENAME).read_text(encoding="utf-8"))
            pid = int(owner["pid"])
        except (OSError, ValueError, KeyError, TypeError):
            try:
                if now - root.stat().st_mtime < _ORPHAN_GRACE_SECONDS:
                    continue
            except OSError:
                continue
            owner, pid = {}, 0
        if pid == os.getpid() or (pid and owner.get("host") not in (None, socket.gethostname())):
            continue
        if pid and _pid_alive(pid):
            continue
        if cleanup is not None and owner:
            try:
                cleanup(root, owner)
            except Exception:
                pass
        _remove_tree(root)
        removed.append(root)
    return removed


class _SandboxSession:
    """One sandbox session on disk: ``<base>/<sid>/`` with ``owner.json`` and
    ``work/``, where each run gets a fresh directory that is deleted afterwards.
    Holds no reference to the ExecutionSandbox, so it can be its finalizer."""

    def __init__(self, label: str, backend_name: str) -> None:
        base = _private_base_dir()
        self.root = Path(tempfile.mkdtemp(prefix=f"{label}-", dir=base)).resolve()
        self.sid = self.root.name
        self.work = self.root / "work"
        self.work.mkdir(mode=0o700)
        self.owner: dict[str, Any] = {
            "pid": os.getpid(),
            "host": socket.gethostname(),
            "created": datetime.now(timezone.utc).isoformat(),
            "backend": backend_name,
        }
        self.backend: Any = None
        self.policy: Any = None
        self._runs = 0
        self.closed = False
        self.write_owner()

    def write_owner(self, **extra: Any) -> None:
        self.owner.update(extra)
        (self.root / OWNER_FILENAME).write_text(json.dumps(self.owner, indent=2) + "\n", encoding="utf-8")

    def new_run_dir(self) -> Path:
        self._runs += 1
        run_dir = self.work / f"run-{self._runs:04d}-{secrets.token_hex(3)}"
        run_dir.mkdir(mode=0o700)
        (run_dir / "tmp").mkdir(mode=0o700)
        return run_dir

    def clear_work(self) -> None:
        """After a run: nothing it wrote survives into the next run."""
        _clear_directory(self.work)

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        backend, self.backend = self.backend, None
        if backend is not None:
            try:
                backend.close()
            except Exception:
                pass
        _remove_tree(self.root)


def _session_label(label: str | None) -> str:
    cleaned = "".join(c if c.isalnum() else "-" for c in (label or "session").lower()).strip("-")
    return (cleaned or "session")[:16]



class ExecutionSandbox:
    """OS-native deterministic execution sandbox (P1), one per session (ADR-0021).

    - Zero-dependency local process isolation (Windows Job Objects on Windows,
      setrlimit on POSIX).
    - Session-scoped OS-native confinement (Landlock, Seatbelt, AppContainer, or an
      opt-in container): each program may read and write only its own fresh run
      directory, read the interpreter and what the OS loader needs, and start no
      process and open no network connection. When the backend cannot be applied,
      nothing runs (``sandbox_unavailable``); ``audit-only`` is the explicit opt-out.
    - Standard library only (``-I -S``) from the base interpreter; UTF-8, unbuffered
      standard streams (``-X utf8 -u``) on every OS.
    - Deterministic wall-clock timeout and memory ceilings.
    - Withheld environment: only an allowlist of variables is passed (no secrets).
    - An in-process audit hook enforces the same policy as defense in depth.
    """

    DEFAULT_TIMEOUT_SECONDS: float = 5.0
    DEFAULT_MEMORY_LIMIT_BYTES: int = 256 * 1024 * 1024  # 256 MB
    # Test-only switch: False omits the audit-hook prelude, so a test can show that
    # the OS-native backend holds on its own. Production code never changes it.
    _policy_hooks: bool = True

    def __init__(
        self,
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        memory_limit_bytes: int = DEFAULT_MEMORY_LIMIT_BYTES,
        allow_network: bool = False,
        allow_processes: bool = False,
        mode: str | None = None,
        label: str | None = None,
    ) -> None:
        self.timeout_seconds = float(timeout_seconds)
        self.memory_limit_bytes = int(memory_limit_bytes)
        self.allow_network = allow_network
        self.allow_processes = allow_processes
        self.mode = resolve_mode(mode)
        self.label = _session_label(label)
        self.backend_name = select_backend(self.mode).name
        self.unavailable_reason: str | None = None
        self._probed = False
        self._session: _SandboxSession | None = None
        self._session_facts: dict[str, Any] = {}
        self._finalizer: Any = None

    # -- session lifecycle -------------------------------------------------------

    @property
    def confined(self) -> bool:
        """Whether programs run under an OS-native backend (not the audit-only opt-out)."""
        return self.backend_name != "audit-only"

    def probe(self) -> bool:
        """Whether the chosen backend can run programs on this machine. Cheap: no
        session is built. A backend that failed to prepare stays unavailable."""
        if not self._probed:
            self._probed = True
            if self.unavailable_reason is None:
                self.unavailable_reason = select_backend(self.mode).probe()
        return self.unavailable_reason is None

    @property
    def session_info(self) -> dict[str, Any] | None:
        """Facts about the session (backend, mode, root, backend facts), or about why
        no session can be built; None before the first run."""
        if self._session is not None:
            return {"backend": self.backend_name, "mode": self.mode, "available": True,
                    "root": str(self._session.root), **self._session_facts}
        if self._probed and self.unavailable_reason is not None:
            return {"backend": self.backend_name, "mode": self.mode, "available": False,
                    "reason": self.unavailable_reason}
        return None

    def _ensure_session(self) -> _SandboxSession:
        """Build the session on the first run: its root, its owner record, the
        backend's native state, and a sweep of roots left by hosts that were killed
        before ``close()`` ran (``atexit`` is not used: it does not run for a killed
        process either). Raises SandboxUnavailable when confinement cannot apply."""
        if self._session is not None and not self._session.closed:
            return self._session
        if not self.probe():
            raise SandboxUnavailable(self.unavailable_reason or "unavailable")
        sweep_stale_roots(cleanup=sweep_owner)
        backend = select_backend(self.mode)
        try:
            session = _SandboxSession(self.label, backend.name)
        except OSError as exc:
            self.unavailable_reason = f"cannot create the sandbox session root: {exc}"
            raise SandboxUnavailable(self.unavailable_reason) from exc
        try:
            policy = build_policy(
                session.root, session.work, network=self.allow_network, processes=self.allow_processes,
            )
            facts = backend.prepare(policy, session)
        except Exception as exc:
            backend.close()
            session.close()
            self.unavailable_reason = exc.reason if isinstance(exc, SandboxUnavailable) else (
                f"{backend.name} setup failed: {exc}"
            )
            raise SandboxUnavailable(self.unavailable_reason) from exc
        session.backend = backend
        session.policy = policy
        session.write_owner(**backend.owner_record())
        self._session = session
        self._session_facts = dict(facts)
        # Released when the sandbox is garbage-collected without close(); not at
        # interpreter exit (the sweep covers hosts that never get there).
        self._finalizer = weakref.finalize(self, session.close)
        self._finalizer.atexit = False
        return session

    def close(self) -> None:
        """Release the session: its root directory and every backend resource."""
        session, self._session = self._session, None
        if session is not None:
            session.close()
        if self._finalizer is not None:
            self._finalizer.detach()
            self._finalizer = None

    def __enter__(self) -> "ExecutionSandbox":
        return self

    def __exit__(self, *exc_info: Any) -> None:
        self.close()

    def decision_state(self) -> dict[str, str]:
        """The sandbox as System 1 routing state: what the environment provides and
        what one step is, from the same source the sandbox enforces."""
        version = ".".join(str(part) for part in sys.version_info[:2])
        if not self.probe():
            return {
                "execution_environment": (
                    "No program execution is available in this session: the host cannot confine programs on this "
                    f"machine ({self.unavailable_reason}), so it runs none; network access is disabled."
                ),
                "step_definition": "No program is run in this session, so no steps are counted.",
            }
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
        if not self.probe():
            return [
                {
                    "name": "python",
                    "description": (
                        f"Unavailable in this session: the host cannot confine programs on this machine "
                        f"({self.unavailable_reason}), so it runs no program from the deliverable. Python {version} "
                        "source in the deliverable is not executed and produces no output."
                    ),
                }
            ]
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

    def _create_windows_job(self, memory_limit_bytes: int, active_process_limit: int = 0) -> int | None:
        """Create and configure a Windows Job Object with memory and process lifecycle limits
        (and, when ``active_process_limit`` is set, a cap on the processes it admits)."""
        if not _IS_WINDOWS:
            return None
        k32 = kernel32()
        h_job = k32.CreateJobObjectW(None, None)
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
        if active_process_limit:
            info.BasicLimitInformation.LimitFlags |= JOB_OBJECT_LIMIT_ACTIVE_PROCESS
            info.BasicLimitInformation.ActiveProcessLimit = active_process_limit
        info.JobMemoryLimit = memory_limit_bytes
        info.ProcessMemoryLimit = memory_limit_bytes

        success = k32.SetInformationJobObject(
            h_job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not success:
            k32.CloseHandle(h_job)
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

        try:
            session = self._ensure_session()
        except SandboxUnavailable as exc:
            # Fail closed: no confinement, no run.
            return SandboxResult(
                stdout="",
                stderr=f"Code execution is unavailable: {exc.reason}",
                exit_code=-1,
                duration_ms=0.0,
                error=f"sandbox_unavailable:{exc.reason}",
            )
        run_dir = session.new_run_dir()
        try:
            entry_file = run_dir / "_entry.py"

            content_parts: list[str] = []
            if session.backend.entry_limits:
                content_parts.append(_ENTRY_LIMITS_PRELUDE.format(
                    memory=int(effective_memory), cpu=int(math.ceil(effective_timeout * 2)) + 1,
                ))
            if self._policy_hooks:
                content_parts.append(_policy_prelude(
                    allow_network=self.allow_network, allow_processes=self.allow_processes,
                ))
            if step_limit is not None:
                content_parts.append(_STEP_BUDGET_PRELUDE.format(
                    limit=int(step_limit), marker=_STEP_BUDGET_MARKER, exit_code=STEP_BUDGET_EXIT_CODE,
                    steps_marker=_STEPS_USED_MARKER,
                ))
            # The program runs from its own file, so tracebacks and syntax errors cite
            # the program's own line numbers, not lines shifted by the preludes.
            program_file = run_dir / PROGRAM_FILENAME
            program_file.write_text(code, encoding="utf-8")
            content_parts.append(
                f"exec(compile(open({PROGRAM_FILENAME!r}, encoding='utf-8').read(), {PROGRAM_FILENAME!r}, 'exec'), "
                f"{{'__name__': '__main__', '__file__': {PROGRAM_FILENAME!r}}})"
            )
            entry_file.write_text("\n".join(content_parts), encoding="utf-8")

            # Temporary files land in the run's own directory (deleted with it).
            run_tmp = str(run_dir / "tmp")
            run_env = {"TMPDIR": run_tmp, "TEMP": run_tmp, "TMP": run_tmp, **(env or {})}
            result = self._execute_process(
                [str(session.policy.interpreter), *_INTERPRETER_FLAGS, entry_file.name],
                cwd=run_dir,
                timeout=effective_timeout,
                memory_limit_bytes=effective_memory,
                env=run_env,
                backend=session.backend,
            )
        finally:
            # A just-killed Windows process can still hold a file (WinError 32): what
            # cannot be deleted now is deleted after the next run or at close().
            session.clear_work()
        from dataclasses import replace

        if step_limit is not None:
            steps_used, kept = None, []
            for line in (result.stderr or "").splitlines(keepends=True):
                if line.startswith(_STEPS_USED_MARKER + ": "):
                    steps_used = int(line.split(": ", 1)[1])
                else:
                    kept.append(line)
            result = replace(result, stderr="".join(kept), steps_used=steps_used)
        if result.exit_code == STEP_BUDGET_EXIT_CODE and _STEP_BUDGET_MARKER in result.stderr:
            result = replace(result, step_budget_exceeded=True, steps_used=int(step_limit) + 1)
        return result

    def _execute_process(
        self,
        cmd: list[str],
        *,
        cwd: Path,
        timeout: float,
        memory_limit_bytes: int,
        backend: Any,
        env: dict[str, str] | None = None,
    ) -> SandboxResult:
        base_env = {k: os.environ[k] for k in _ENV_ALLOWLIST if k in os.environ}
        if _IS_WINDOWS:
            base_env.setdefault("SYSTEMROOT", "C:\\Windows")
        if env:
            base_env.update(env)

        h_job = None
        k32 = None
        if _IS_WINDOWS:
            k32 = kernel32()
            h_job = self._create_windows_job(memory_limit_bytes, backend.job_active_process_limit)
        limits = RunLimits(
            timeout=timeout,
            memory_limit_bytes=memory_limit_bytes,
            cpu_seconds=int(math.ceil(timeout * 2)) + 1,
            job=h_job,
        )

        start_time = time.perf_counter()
        proc = None
        timed_out = False
        stdout_text = ""
        stderr_text = ""
        exit_code = -1

        try:
            try:
                proc = backend.launch(cmd, cwd=cwd, env=base_env, limits=limits)
            except LaunchError as exc:
                return SandboxResult(
                    stdout="",
                    stderr=f"Failed to start the process in its containment ({exc.failure})",
                    exit_code=-1,
                    duration_ms=(time.perf_counter() - start_time) * 1000.0,
                    error=exc.failure,
                )

            raw_out, raw_err = proc.communicate(timeout=timeout)
            stdout_text = _decode_stream(raw_out)
            stderr_text = _decode_stream(raw_err)
            exit_code = proc.returncode

        except subprocess.TimeoutExpired:
            timed_out = True
            if proc is not None:
                self._kill_tree(proc, h_job, k32, backend)
                # Collect what the program printed before the kill. Bounded, so a
                # descendant that escaped the kill and still holds a pipe cannot hang
                # the host.
                try:
                    raw_out, raw_err = proc.communicate(timeout=_KILL_GRACE_SECONDS)
                    stdout_text = _decode_stream(raw_out)
                    stderr_text = _decode_stream(raw_err)
                except Exception:
                    pass
            exit_code = 124

        except Exception as exc:
            if proc is not None:
                self._kill_tree(proc, h_job, k32, backend)
                try:
                    proc.communicate(timeout=_KILL_GRACE_SECONDS)
                except Exception:
                    pass
            return SandboxResult(
                stdout="",
                stderr=str(exc),
                exit_code=-1,
                duration_ms=(time.perf_counter() - start_time) * 1000.0,
                error=f"execution_exception: {exc}",
            )

        except BaseException:
            # Ctrl-C or SystemExit in the host: the program runs in its own session
            # (or job), so it would be orphaned and keep running. Kill it first.
            if proc is not None:
                self._kill_tree(proc, h_job, k32, backend)
            raise

        finally:
            if _IS_WINDOWS and h_job and k32:
                k32.CloseHandle(h_job)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        if not _IS_WINDOWS and exit_code in (-signal.SIGXCPU, 128 + signal.SIGXCPU):
            timed_out = True  # the CPU-time backstop stopped it before the wall clock did

        # Memory limit exhaustion detection
        oom_killed = False
        lower_err = stderr_text.lower()
        if "memoryerror" in lower_err or "out of memory" in lower_err or "cannot allocate memory" in lower_err:
            oom_killed = True
        elif _IS_WINDOWS and exit_code in _WINDOWS_OOM_EXIT_CODES:
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

    @staticmethod
    def _kill_tree(proc: Any, h_job: Any, k32: Any, backend: Any = None) -> None:
        """Kill the program and every process it started: the job on Windows, the
        process group (its own session) on POSIX, and whatever the backend runs
        beyond it. Never raises."""
        try:
            if _IS_WINDOWS and h_job and k32:
                k32.TerminateJobObject(h_job, 124)
            elif not _IS_WINDOWS:
                os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass  # already gone
        try:
            proc.kill()
        except OSError:
            pass
        if backend is not None:
            backend.terminate()


def _decode_stream(raw: bytes | None) -> str:
    text = (raw or b"").decode("utf-8", errors="replace")
    # Python on Windows writes "\n" to its standard streams as "\r\n"; undo exactly
    # that, so a program's output is the same text on every OS.
    return text.replace("\r\n", "\n") if _IS_WINDOWS else text
