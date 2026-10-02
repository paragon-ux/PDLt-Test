"""A minimal Popen-like launcher for Windows (ctypes, standard library only).

subprocess.Popen cannot pass security capabilities, so programs confined by an
AppContainer start through CreateProcessW with an extended attribute list:

- PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES: the AppContainer SID with no
  capabilities (no network, no loopback);
- PROC_THREAD_ATTRIBUTE_JOB_LIST: the process is created inside the caller's Job
  Object, so no instruction runs outside it (no suspend/resume needed);
- PROC_THREAD_ATTRIBUTE_HANDLE_LIST: only the three pipe ends are inherited;
- PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY: the process cannot create children.

Structures use fixed-width types (DWORD is 4 bytes, BOOL 4, HANDLE pointer-sized),
so their x64 layout is the same wherever this module is imported; every function
has an explicit prototype (without one ctypes truncates 64-bit handles).
"""
from __future__ import annotations

import ctypes
import os
import subprocess
import threading
import time
import weakref
from typing import Any

DWORD = ctypes.c_uint32
WORD = ctypes.c_uint16
BOOL = ctypes.c_int32
HANDLE = ctypes.c_void_p
LPWSTR = ctypes.c_wchar_p
SIZE_T = ctypes.c_size_t

EXTENDED_STARTUPINFO_PRESENT = 0x00080000
CREATE_UNICODE_ENVIRONMENT = 0x00000400
# No console at all: a console host (conhost.exe) would start as the program's child,
# which the child-process policy and a one-process job refuse (STATUS_DLL_INIT_FAILED).
# The program's standard streams are pipes, so it needs no console.
DETACHED_PROCESS = 0x00000008
STARTF_USESTDHANDLES = 0x00000100
HANDLE_FLAG_INHERIT = 0x00000001
INFINITE = 0xFFFFFFFF
WAIT_OBJECT_0 = 0x00000000
WAIT_TIMEOUT = 0x00000102
STILL_ACTIVE = 259


def proc_thread_attribute(number: int, *, thread: bool = False, input: bool = True, additive: bool = False) -> int:
    """ProcThreadAttributeValue() from WinBase.h."""
    return (number & 0x0000FFFF) | (0x00010000 if thread else 0) | (0x00020000 if input else 0) | (
        0x00040000 if additive else 0)


PROC_THREAD_ATTRIBUTE_HANDLE_LIST = proc_thread_attribute(2)  # 0x00020002
PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES = proc_thread_attribute(9)  # 0x00020009
PROC_THREAD_ATTRIBUTE_JOB_LIST = proc_thread_attribute(13)  # 0x0002000D
PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY = proc_thread_attribute(14)  # 0x0002000E
PROCESS_CREATION_CHILD_PROCESS_RESTRICTED = 0x01


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", DWORD), ("lpSecurityDescriptor", ctypes.c_void_p), ("bInheritHandle", BOOL)]


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [
        ("cb", DWORD),
        ("lpReserved", LPWSTR),
        ("lpDesktop", LPWSTR),
        ("lpTitle", LPWSTR),
        ("dwX", DWORD),
        ("dwY", DWORD),
        ("dwXSize", DWORD),
        ("dwYSize", DWORD),
        ("dwXCountChars", DWORD),
        ("dwYCountChars", DWORD),
        ("dwFillAttribute", DWORD),
        ("dwFlags", DWORD),
        ("wShowWindow", WORD),
        ("cbReserved2", WORD),
        ("lpReserved2", ctypes.c_void_p),
        ("hStdInput", HANDLE),
        ("hStdOutput", HANDLE),
        ("hStdError", HANDLE),
    ]


class STARTUPINFOEXW(ctypes.Structure):
    _fields_ = [("StartupInfo", STARTUPINFOW), ("lpAttributeList", ctypes.c_void_p)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", HANDLE), ("hThread", HANDLE), ("dwProcessId", DWORD), ("dwThreadId", DWORD)]


class SECURITY_CAPABILITIES(ctypes.Structure):
    _fields_ = [
        ("AppContainerSid", ctypes.c_void_p),
        ("Capabilities", ctypes.c_void_p),  # PSID_AND_ATTRIBUTES; none are granted
        ("CapabilityCount", DWORD),
        ("Reserved", DWORD),
    ]


_KERNEL32: Any = None


def kernel32() -> Any:
    global _KERNEL32
    if _KERNEL32 is None:
        k = ctypes.WinDLL("kernel32", use_last_error=True)
        k.CreatePipe.argtypes = (ctypes.POINTER(HANDLE), ctypes.POINTER(HANDLE), ctypes.POINTER(SECURITY_ATTRIBUTES),
                                 DWORD)
        k.CreatePipe.restype = BOOL
        k.SetHandleInformation.argtypes = (HANDLE, DWORD, DWORD)
        k.SetHandleInformation.restype = BOOL
        k.InitializeProcThreadAttributeList.argtypes = (ctypes.c_void_p, DWORD, DWORD, ctypes.POINTER(SIZE_T))
        k.InitializeProcThreadAttributeList.restype = BOOL
        k.UpdateProcThreadAttribute.argtypes = (ctypes.c_void_p, DWORD, ctypes.c_size_t, ctypes.c_void_p, SIZE_T,
                                                ctypes.c_void_p, ctypes.POINTER(SIZE_T))
        k.UpdateProcThreadAttribute.restype = BOOL
        k.DeleteProcThreadAttributeList.argtypes = (ctypes.c_void_p,)
        k.DeleteProcThreadAttributeList.restype = None
        k.CreateProcessW.argtypes = (LPWSTR, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, BOOL, DWORD,
                                     ctypes.c_void_p, LPWSTR, ctypes.POINTER(STARTUPINFOEXW),
                                     ctypes.POINTER(PROCESS_INFORMATION))
        k.CreateProcessW.restype = BOOL
        k.WaitForSingleObject.argtypes = (HANDLE, DWORD)
        k.WaitForSingleObject.restype = DWORD
        k.GetExitCodeProcess.argtypes = (HANDLE, ctypes.POINTER(DWORD))
        k.GetExitCodeProcess.restype = BOOL
        k.TerminateProcess.argtypes = (HANDLE, ctypes.c_uint)
        k.TerminateProcess.restype = BOOL
        k.CloseHandle.argtypes = (HANDLE,)
        k.CloseHandle.restype = BOOL
        _KERNEL32 = k
    return _KERNEL32


def _check(ok: Any, what: str) -> None:
    if not ok:
        raise ctypes.WinError(ctypes.get_last_error(), f"{what} failed")


def environment_block(env: dict[str, str]) -> str:
    """A CREATE_UNICODE_ENVIRONMENT block: NAME=value entries sorted by name
    (case-insensitively, as Windows expects), each NUL-terminated, then a final NUL."""
    for name in env:
        if not name or "=" in name[1:] or "\0" in name or "\0" in env[name]:
            raise ValueError(f"invalid environment variable name or value: {name!r}")
    entries = [f"{k}={env[k]}" for k in sorted(env, key=str.upper)]
    return "\0".join(entries) + "\0\0"


def _pipe() -> tuple[int, int]:
    """(read, write) handles, neither inheritable."""
    attrs = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, False)
    read, write = HANDLE(), HANDLE()
    _check(kernel32().CreatePipe(ctypes.byref(read), ctypes.byref(write), ctypes.byref(attrs), 0), "CreatePipe")
    return read.value, write.value


class WinProcess:
    """The Popen subset the sandbox uses: communicate, wait, kill, pid, returncode,
    and _handle (the process handle, as Popen exposes it)."""

    def __init__(self, args: list[str], pid: int, process: int, stdout: int, stderr: int) -> None:
        import msvcrt

        self.args = args
        self.pid = pid
        self._handle = process
        self.returncode: int | None = None
        self._chunks: dict[str, list[bytes]] = {"out": [], "err": []}
        self._readers = []
        for key, handle in (("out", stdout), ("err", stderr)):
            stream = open(msvcrt.open_osfhandle(handle, os.O_RDONLY), "rb", buffering=0)
            reader = threading.Thread(target=self._drain, args=(stream, self._chunks[key]), daemon=True)
            reader.start()
            self._readers.append(reader)
        self._finalizer = weakref.finalize(self, kernel32().CloseHandle, process)

    @staticmethod
    def _drain(stream: Any, sink: list[bytes]) -> None:
        with stream:
            while True:
                try:
                    chunk = stream.read(65536)
                except OSError:
                    return
                if not chunk:
                    return
                sink.append(chunk)

    def _poll_exit(self) -> int | None:
        code = DWORD()
        if kernel32().GetExitCodeProcess(self._handle, ctypes.byref(code)) and code.value != STILL_ACTIVE:
            self.returncode = code.value
        return self.returncode

    def wait(self, timeout: float | None = None) -> int:
        if self.returncode is not None:
            return self.returncode
        millis = INFINITE if timeout is None else max(0, int(timeout * 1000))
        result = kernel32().WaitForSingleObject(self._handle, millis)
        if result == WAIT_TIMEOUT:
            raise subprocess.TimeoutExpired(self.args, timeout)
        if result != WAIT_OBJECT_0:
            raise ctypes.WinError(ctypes.get_last_error(), "WaitForSingleObject failed")
        code = self._poll_exit()
        return code if code is not None else -1

    def communicate(self, timeout: float | None = None) -> tuple[bytes, bytes]:
        deadline = None if timeout is None else time.monotonic() + timeout
        self.wait(timeout)
        for reader in self._readers:
            reader.join(None if deadline is None else max(0.0, deadline - time.monotonic()))
            if reader.is_alive():
                raise subprocess.TimeoutExpired(self.args, timeout)
        return b"".join(self._chunks["out"]), b"".join(self._chunks["err"])

    def poll(self) -> int | None:
        return self.returncode if self.returncode is not None else self._poll_exit()

    def kill(self) -> None:
        if self.poll() is None:
            kernel32().TerminateProcess(self._handle, 1)


def spawn(
    argv: list[str],
    *,
    cwd: str,
    env: dict[str, str],
    appcontainer_sid: Any = None,
    job: Any = None,
    restrict_children: bool = True,
) -> WinProcess:
    """Start ``argv`` with empty standard input and piped output, inside ``job`` and
    the AppContainer when given. Raises OSError when the process cannot be created."""
    k32 = kernel32()
    stdin_r, stdin_w = _pipe()
    stdout_r, stdout_w = _pipe()
    stderr_r, stderr_w = _pipe()
    child_ends = (stdin_r, stdout_w, stderr_w)
    attribute_list = None
    initialized = False
    try:
        k32.CloseHandle(stdin_w)  # empty standard input: the program reads EOF
        for handle in child_ends:
            _check(k32.SetHandleInformation(handle, HANDLE_FLAG_INHERIT, HANDLE_FLAG_INHERIT), "SetHandleInformation")

        values: list[tuple[int, Any]] = [
            (PROC_THREAD_ATTRIBUTE_HANDLE_LIST, (HANDLE * 3)(*child_ends)),
        ]
        if appcontainer_sid is not None:
            values.append((PROC_THREAD_ATTRIBUTE_SECURITY_CAPABILITIES,
                           SECURITY_CAPABILITIES(AppContainerSid=appcontainer_sid)))
        if job:
            values.append((PROC_THREAD_ATTRIBUTE_JOB_LIST, (HANDLE * 1)(job)))
        if restrict_children:
            values.append((PROC_THREAD_ATTRIBUTE_CHILD_PROCESS_POLICY, DWORD(PROCESS_CREATION_CHILD_PROCESS_RESTRICTED)))

        size = SIZE_T(0)
        k32.InitializeProcThreadAttributeList(None, len(values), 0, ctypes.byref(size))  # sizing call fails by design
        attribute_list = ctypes.create_string_buffer(size.value)
        _check(k32.InitializeProcThreadAttributeList(attribute_list, len(values), 0, ctypes.byref(size)),
               "InitializeProcThreadAttributeList")
        initialized = True
        for attribute, value in values:
            _check(k32.UpdateProcThreadAttribute(attribute_list, 0, attribute, ctypes.byref(value),
                                                 ctypes.sizeof(value), None, None), "UpdateProcThreadAttribute")

        startup = STARTUPINFOEXW()
        startup.StartupInfo.cb = ctypes.sizeof(STARTUPINFOEXW)
        startup.StartupInfo.dwFlags = STARTF_USESTDHANDLES
        startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = child_ends
        startup.lpAttributeList = ctypes.cast(attribute_list, ctypes.c_void_p)
        info = PROCESS_INFORMATION()
        command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
        block = ctypes.create_unicode_buffer(environment_block(env))
        _check(k32.CreateProcessW(
            argv[0], command_line, None, None, True,
            EXTENDED_STARTUPINFO_PRESENT | CREATE_UNICODE_ENVIRONMENT | DETACHED_PROCESS,
            block, cwd, ctypes.byref(startup), ctypes.byref(info),
        ), "CreateProcessW")
        k32.CloseHandle(info.hThread)
    except BaseException:
        for handle in (stdout_r, stderr_r):
            k32.CloseHandle(handle)
        raise
    finally:
        for handle in child_ends:
            k32.CloseHandle(handle)  # the child holds its own copies
        if initialized:
            k32.DeleteProcThreadAttributeList(attribute_list)
    return WinProcess(argv, info.dwProcessId, info.hProcess, stdout_r, stderr_r)
