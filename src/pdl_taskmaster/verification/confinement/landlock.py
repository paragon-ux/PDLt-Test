"""Linux Landlock backend: unprivileged, kernel-enforced filesystem, TCP and scope
confinement (Linux 5.13+, ABI 1 to 7), through raw system calls via ctypes.

The ruleset is built once per session in the host. Each program's forked child
sets no_new_privs and restricts itself with that ruleset after its resource limits
and before exec, so the interpreter itself starts confined.

- Reads: the policy's read roots. Writes: the session's work directory only.
- Execute: the interpreter and its ELF loader only (exec of /bin/sh is denied).
- ABI 4+: TCP bind and connect are handled with no rule, so both are denied.
- ABI 6+: abstract UNIX sockets and signals are scoped to the program's domain.
"""
from __future__ import annotations

import ctypes
import os
import platform
import stat
import sys
from typing import Any, Callable

from pdl_taskmaster.verification.confinement.backends import Backend, SandboxUnavailable
from pdl_taskmaster.verification.confinement.policy import SandboxPolicy

SYS_LANDLOCK_CREATE_RULESET = 444  # the same number on every Linux architecture
SYS_LANDLOCK_ADD_RULE = 445
SYS_LANDLOCK_RESTRICT_SELF = 446
LANDLOCK_CREATE_RULESET_VERSION = 1 << 0
LANDLOCK_RULE_PATH_BENEATH = 1
PR_SET_NO_NEW_PRIVS = 38

ACCESS_FS_EXECUTE = 1 << 0
ACCESS_FS_WRITE_FILE = 1 << 1
ACCESS_FS_READ_FILE = 1 << 2
ACCESS_FS_READ_DIR = 1 << 3
ACCESS_FS_REMOVE_DIR = 1 << 4
ACCESS_FS_REMOVE_FILE = 1 << 5
ACCESS_FS_MAKE_CHAR = 1 << 6
ACCESS_FS_MAKE_DIR = 1 << 7
ACCESS_FS_MAKE_REG = 1 << 8
ACCESS_FS_MAKE_SOCK = 1 << 9
ACCESS_FS_MAKE_FIFO = 1 << 10
ACCESS_FS_MAKE_BLOCK = 1 << 11
ACCESS_FS_MAKE_SYM = 1 << 12
ACCESS_FS_REFER = 1 << 13  # ABI 2
ACCESS_FS_TRUNCATE = 1 << 14  # ABI 3
ACCESS_FS_IOCTL_DEV = 1 << 15  # ABI 5
ACCESS_NET_BIND_TCP = 1 << 0  # ABI 4
ACCESS_NET_CONNECT_TCP = 1 << 1  # ABI 4
SCOPE_ABSTRACT_UNIX_SOCKET = 1 << 0  # ABI 6
SCOPE_SIGNAL = 1 << 1  # ABI 6

# Rights that apply to a file (not a directory) rule; anything else is EINVAL there.
_FILE_RIGHTS = ACCESS_FS_EXECUTE | ACCESS_FS_WRITE_FILE | ACCESS_FS_READ_FILE | ACCESS_FS_TRUNCATE | ACCESS_FS_IOCTL_DEV
_READ_RIGHTS = ACCESS_FS_READ_FILE | ACCESS_FS_READ_DIR


def handled_fs_access(abi: int) -> int:
    """Every filesystem right the ABI knows: an unhandled right is not restricted."""
    rights = (1 << 13) - 1
    if abi >= 2:
        rights |= ACCESS_FS_REFER
    if abi >= 3:
        rights |= ACCESS_FS_TRUNCATE
    if abi >= 5:
        rights |= ACCESS_FS_IOCTL_DEV
    return rights


class RulesetAttr(ctypes.Structure):
    """struct landlock_ruleset_attr; its size grows with the ABI."""

    _fields_ = [
        ("handled_access_fs", ctypes.c_uint64),
        ("handled_access_net", ctypes.c_uint64),
        ("scoped", ctypes.c_uint64),
    ]


def ruleset_attr_size(abi: int) -> int:
    return 8 if abi < 4 else 16 if abi < 6 else 24


class PathBeneathAttr(ctypes.Structure):
    """struct landlock_path_beneath_attr (packed: 12 bytes)."""

    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


_LIBC: Any = None


def _libc() -> Any:
    global _LIBC
    if _LIBC is None:
        libc = ctypes.CDLL(None, use_errno=True)
        libc.syscall.restype = ctypes.c_long
        libc.prctl.restype = ctypes.c_int
        _LIBC = libc
    return _LIBC


def _syscall(number: int, *args: Any) -> int:
    ctypes.set_errno(0)
    return _libc().syscall(ctypes.c_long(number), *args)


def landlock_abi() -> tuple[int, str | None]:
    """(ABI version, None) when Landlock is usable, else (0, reason)."""
    if not sys.platform.startswith("linux"):
        return 0, f"Landlock is Linux-only (platform {sys.platform})"
    try:
        abi = _syscall(SYS_LANDLOCK_CREATE_RULESET, None, ctypes.c_size_t(0),
                       ctypes.c_uint32(LANDLOCK_CREATE_RULESET_VERSION))
    except (OSError, AttributeError) as exc:
        return 0, f"Landlock system call unavailable ({exc})"
    if abi < 1:
        err = ctypes.get_errno()
        detail = os.strerror(err) if err else "no ABI reported"
        return 0, (
            f"Landlock is not available on this kernel ({platform.release()}: {detail}); it needs Linux 5.13+ "
            "with Landlock enabled in the LSM list"
        )
    return int(abi), None


class LandlockBackend(Backend):
    name = "landlock"

    def __init__(self) -> None:
        self.abi = 0
        self.ruleset_fd: int | None = None

    def probe(self) -> str | None:
        abi, reason = landlock_abi()
        if reason is None:
            self.abi = abi
        return reason

    def prepare(self, policy: SandboxPolicy, session: Any) -> dict[str, Any]:
        self.policy = policy
        reason = self.probe()
        if reason is not None:
            raise SandboxUnavailable(reason)
        handled_fs = handled_fs_access(self.abi)
        attr = RulesetAttr(handled_access_fs=handled_fs)
        if self.abi >= 4 and not policy.network:
            attr.handled_access_net = ACCESS_NET_BIND_TCP | ACCESS_NET_CONNECT_TCP
        if self.abi >= 6:
            attr.scoped = SCOPE_ABSTRACT_UNIX_SOCKET | SCOPE_SIGNAL
        fd = _syscall(SYS_LANDLOCK_CREATE_RULESET, ctypes.byref(attr), ctypes.c_size_t(ruleset_attr_size(self.abi)),
                      ctypes.c_uint32(0))
        if fd < 0:
            raise SandboxUnavailable(f"landlock_create_ruleset failed: {os.strerror(ctypes.get_errno())}")
        self.ruleset_fd = int(fd)  # O_CLOEXEC: never leaks into a program
        try:
            write = handled_fs & ~ACCESS_FS_EXECUTE
            for path in policy.read_roots:
                self._add_rule(path, _READ_RIGHTS & handled_fs)
            for path in policy.write_roots:
                self._add_rule(path, write)
            for path in policy.exec_paths:
                self._add_rule(path, (ACCESS_FS_EXECUTE | ACCESS_FS_READ_FILE) & handled_fs)
            # The null device is writable (output discarded), as it is everywhere.
            self._add_rule(os.devnull, (ACCESS_FS_WRITE_FILE | ACCESS_FS_READ_FILE | ACCESS_FS_TRUNCATE
                                        | ACCESS_FS_IOCTL_DEV) & handled_fs)
        except SandboxUnavailable:
            self.close()
            raise
        self._restrict = self._child_restrict(self.ruleset_fd)
        return {"abi": self.abi, "kernel": platform.release()}

    def _add_rule(self, path: Any, access: int) -> None:
        try:
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
        except FileNotFoundError:
            return
        except OSError as exc:
            raise SandboxUnavailable(f"cannot open {path} for a Landlock rule: {exc}") from exc
        try:
            if not stat.S_ISDIR(os.fstat(fd).st_mode):
                access &= _FILE_RIGHTS
            rule = PathBeneathAttr(allowed_access=access, parent_fd=fd)
            if _syscall(SYS_LANDLOCK_ADD_RULE, ctypes.c_int(self.ruleset_fd), ctypes.c_int(LANDLOCK_RULE_PATH_BENEATH),
                        ctypes.byref(rule), ctypes.c_uint32(0)) != 0:
                raise SandboxUnavailable(
                    f"landlock_add_rule failed for {path}: {os.strerror(ctypes.get_errno())}"
                )
        finally:
            os.close(fd)

    @staticmethod
    def _child_restrict(ruleset_fd: int) -> Callable[[], None]:
        """The forked child's step. Everything it calls is resolved here, in the host,
        so the child only makes two foreign calls."""
        libc = _libc()
        prctl, syscall = libc.prctl, libc.syscall
        args_nnp = (ctypes.c_int(PR_SET_NO_NEW_PRIVS), ctypes.c_ulong(1), ctypes.c_ulong(0), ctypes.c_ulong(0),
                    ctypes.c_ulong(0))
        args_restrict = (ctypes.c_long(SYS_LANDLOCK_RESTRICT_SELF), ctypes.c_int(ruleset_fd), ctypes.c_uint32(0))

        def restrict() -> None:
            if prctl(*args_nnp) != 0:
                raise OSError(ctypes.get_errno(), "prctl(PR_SET_NO_NEW_PRIVS) failed")
            if syscall(*args_restrict) != 0:
                raise OSError(ctypes.get_errno(), "landlock_restrict_self failed")
        return restrict

    def child_setup(self) -> Callable[[], None] | None:
        return self._restrict

    def close(self) -> None:
        fd, self.ruleset_fd = self.ruleset_fd, None
        if fd is not None:
            try:
                os.close(fd)
            except OSError:
                pass
