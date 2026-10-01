"""Windows AppContainer backend: reads and writes confined by the kernel.

Per session: an AppContainer profile ``PDLt.Sandbox.<sid>`` (userenv), with modify
rights on the session's work directory only (a new, empty directory, so the grant
is instant). Programs start in it through winproc with no capabilities (no network,
no loopback), inside the run's Job Object, unable to create child processes. An
AppContainer process reads only what grants ALL APPLICATION PACKAGES access (the
Windows and Program Files directories) plus what is granted to its own SID; it
cannot read the user's profile, the repository or other sessions.

A per-user Python install (%LOCALAPPDATA%\\Programs\\Python) is not readable by
AppContainers. When the self-test shows the base prefix unreadable, read and
execute are granted on it to ALL APPLICATION PACKAGES, matching the Program Files
default, once (a marker under ~/.pdlt/ records it). When that grant is impossible,
or Python is the Microsoft Store build (already packaged), the session fails closed.

The profile is deleted by close() and, for a host killed before close() ran, by the
stale-root sweep, from the name recorded in owner.json.
"""
from __future__ import annotations

import ctypes
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from pdl_taskmaster.verification.confinement import winproc
from pdl_taskmaster.verification.confinement.backends import Backend, LaunchError, RunLimits, SandboxUnavailable
from pdl_taskmaster.verification.confinement.policy import SandboxPolicy

DWORD = winproc.DWORD
PROFILE_PREFIX = "PDLt.Sandbox."
ALL_APPLICATION_PACKAGES = "S-1-15-2-1"
HRESULT_ALREADY_EXISTS = 0x800700B7  # HRESULT_FROM_WIN32(ERROR_ALREADY_EXISTS)
SE_FILE_OBJECT = 1
DACL_SECURITY_INFORMATION = 0x00000004
GRANT_ACCESS = 1
SUB_CONTAINERS_AND_OBJECTS_INHERIT = 0x3
TRUSTEE_IS_SID = 0
TRUSTEE_IS_UNKNOWN = 0
# "Modify": read, write, execute and delete (FILE_GENERIC_READ | FILE_GENERIC_WRITE |
# FILE_GENERIC_EXECUTE | DELETE); never WRITE_DAC or WRITE_OWNER.
FILE_MODIFY = 0x001301BF
FILE_READ_EXECUTE = 0x001200A9  # FILE_GENERIC_READ | FILE_GENERIC_EXECUTE
_SELF_TEST_SECONDS = 30.0


class TRUSTEE_W(ctypes.Structure):
    _fields_ = [
        ("pMultipleTrustee", ctypes.c_void_p),
        ("MultipleTrusteeOperation", ctypes.c_int),
        ("TrusteeForm", ctypes.c_int),
        ("TrusteeType", ctypes.c_int),
        ("ptstrName", ctypes.c_void_p),  # a PSID when TrusteeForm is TRUSTEE_IS_SID
    ]


class EXPLICIT_ACCESS_W(ctypes.Structure):
    _fields_ = [
        ("grfAccessPermissions", DWORD),
        ("grfAccessMode", ctypes.c_int),
        ("grfInheritance", DWORD),
        ("Trustee", TRUSTEE_W),
    ]


def profile_name(sid: str) -> str:
    """The AppContainer name for a session id: at most 64 characters of [A-Za-z0-9.-]."""
    cleaned = "".join(c if c.isalnum() or c in ".-" else "-" for c in sid)
    return (PROFILE_PREFIX + cleaned)[:64]


_USERENV: Any = None
_ADVAPI32: Any = None


def userenv() -> Any:
    global _USERENV
    if _USERENV is None:
        u = ctypes.WinDLL("userenv", use_last_error=True)
        u.CreateAppContainerProfile.argtypes = (ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_void_p,
                                                DWORD, ctypes.POINTER(ctypes.c_void_p))
        u.CreateAppContainerProfile.restype = ctypes.c_long  # HRESULT
        u.DeriveAppContainerSidFromAppContainerName.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p))
        u.DeriveAppContainerSidFromAppContainerName.restype = ctypes.c_long
        u.DeleteAppContainerProfile.argtypes = (ctypes.c_wchar_p,)
        u.DeleteAppContainerProfile.restype = ctypes.c_long
        _USERENV = u
    return _USERENV


def advapi32() -> Any:
    global _ADVAPI32
    if _ADVAPI32 is None:
        a = ctypes.WinDLL("advapi32", use_last_error=True)
        a.FreeSid.argtypes = (ctypes.c_void_p,)
        a.FreeSid.restype = ctypes.c_void_p
        a.ConvertSidToStringSidW.argtypes = (ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p))
        a.ConvertSidToStringSidW.restype = winproc.BOOL
        a.ConvertStringSidToSidW.argtypes = (ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p))
        a.ConvertStringSidToSidW.restype = winproc.BOOL
        a.GetNamedSecurityInfoW.argtypes = (ctypes.c_wchar_p, ctypes.c_int, DWORD, ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.POINTER(ctypes.c_void_p), ctypes.c_void_p,
                                            ctypes.POINTER(ctypes.c_void_p))
        a.GetNamedSecurityInfoW.restype = DWORD
        a.SetEntriesInAclW.argtypes = (ctypes.c_ulong, ctypes.POINTER(EXPLICIT_ACCESS_W), ctypes.c_void_p,
                                       ctypes.POINTER(ctypes.c_void_p))
        a.SetEntriesInAclW.restype = DWORD
        a.SetNamedSecurityInfoW.argtypes = (ctypes.c_wchar_p, ctypes.c_int, DWORD, ctypes.c_void_p, ctypes.c_void_p,
                                            ctypes.c_void_p, ctypes.c_void_p)
        a.SetNamedSecurityInfoW.restype = DWORD
        _ADVAPI32 = a
    return _ADVAPI32


def _local_free(pointer: Any) -> None:
    k = ctypes.WinDLL("kernel32", use_last_error=True)
    k.LocalFree.argtypes = (ctypes.c_void_p,)
    k.LocalFree.restype = ctypes.c_void_p
    if pointer:
        k.LocalFree(pointer)


def _hresult(value: int) -> int:
    return value & 0xFFFFFFFF


def sid_string(sid: Any) -> str:
    out = ctypes.c_void_p()
    if not advapi32().ConvertSidToStringSidW(sid, ctypes.byref(out)):
        return "?"
    try:
        return ctypes.wstring_at(out.value)
    finally:
        _local_free(out.value)


def grant(path: Path, sid: Any, access: int) -> None:
    """Add an inheritable allow entry for ``sid`` to ``path``'s DACL. Raises OSError."""
    api = advapi32()
    old_dacl, descriptor = ctypes.c_void_p(), ctypes.c_void_p()
    status = api.GetNamedSecurityInfoW(str(path), SE_FILE_OBJECT, DACL_SECURITY_INFORMATION, None, None,
                                       ctypes.byref(old_dacl), None, ctypes.byref(descriptor))
    if status:
        raise ctypes.WinError(status, f"GetNamedSecurityInfoW({path}) failed")
    new_dacl = ctypes.c_void_p()
    try:
        entry = EXPLICIT_ACCESS_W(
            grfAccessPermissions=access, grfAccessMode=GRANT_ACCESS, grfInheritance=SUB_CONTAINERS_AND_OBJECTS_INHERIT,
            Trustee=TRUSTEE_W(TrusteeForm=TRUSTEE_IS_SID, TrusteeType=TRUSTEE_IS_UNKNOWN, ptstrName=sid),
        )
        status = api.SetEntriesInAclW(1, ctypes.byref(entry), old_dacl, ctypes.byref(new_dacl))
        if status:
            raise ctypes.WinError(status, "SetEntriesInAclW failed")
        status = api.SetNamedSecurityInfoW(str(path), SE_FILE_OBJECT, DACL_SECURITY_INFORMATION, None, None,
                                           new_dacl, None)
        if status:
            raise ctypes.WinError(status, f"SetNamedSecurityInfoW({path}) failed")
    finally:
        _local_free(new_dacl.value)
        _local_free(descriptor.value)


def delete_profile(name: str) -> None:
    try:
        userenv().DeleteAppContainerProfile(name)
    except OSError:
        pass


def is_store_python() -> bool:
    """The Microsoft Store build runs packaged already; it cannot start another
    AppContainer for itself."""
    probes = (sys.base_prefix, getattr(sys, "_base_executable", "") or "", sys.executable)
    return any("windowsapps" in os.path.normcase(p) for p in probes)


def grant_marker(prefix: Path) -> Path:
    digest = hashlib.sha256(os.path.normcase(str(prefix)).encode("utf-8")).hexdigest()[:16]
    return Path.home() / ".pdlt" / f"appcontainer-read-grant-{digest}.json"


class AppContainerBackend(Backend):
    name = "appcontainer"
    job_active_process_limit = 1  # the Job Object admits the program and nothing else

    def __init__(self) -> None:
        self.profile = ""
        self.sid: Any = None

    def probe(self) -> str | None:
        if sys.platform != "win32":
            return f"AppContainer is Windows-only (platform {sys.platform})"
        if is_store_python():
            return ("the Microsoft Store Python is already packaged and cannot confine programs in an AppContainer; "
                    "install Python from python.org or use --sandbox container")
        try:
            userenv()
        except (OSError, AttributeError) as exc:
            return f"AppContainer API unavailable ({exc}); it needs Windows 8 or later"
        return None

    def prepare(self, policy: SandboxPolicy, session: Any) -> dict[str, Any]:
        self.policy = policy
        reason = self.probe()
        if reason is not None:
            raise SandboxUnavailable(reason)
        self.profile = profile_name(session.sid)
        session.write_owner(profile=self.profile)  # recorded first: a host killed now still gets it swept
        sid = ctypes.c_void_p()
        result = _hresult(userenv().CreateAppContainerProfile(
            self.profile, self.profile, "PDLt sandbox session", None, 0, ctypes.byref(sid)))
        if result == HRESULT_ALREADY_EXISTS:
            result = _hresult(userenv().DeriveAppContainerSidFromAppContainerName(self.profile, ctypes.byref(sid)))
        if result != 0 or not sid.value:
            raise SandboxUnavailable(f"CreateAppContainerProfile failed (HRESULT 0x{result:08X})")
        self.sid = sid.value
        try:
            for root in policy.write_roots:
                grant(root, self.sid, FILE_MODIFY)
            self._ensure_interpreter_readable(policy)
        except OSError as exc:
            self.close()
            raise SandboxUnavailable(f"AppContainer setup failed: {exc}") from exc
        except SandboxUnavailable:
            self.close()
            raise
        return {"os": f"Windows {platform.version()}", "profile": self.profile, "sid": sid_string(self.sid)}

    def owner_record(self) -> dict[str, Any]:
        return {"profile": self.profile}

    def _self_test(self, policy: SandboxPolicy) -> tuple[bool, str]:
        try:
            proc = winproc.spawn(
                [str(policy.interpreter), "-I", "-S", "-c", "pass"],
                cwd=str(policy.write_roots[0]),
                env={k: os.environ[k] for k in ("SYSTEMROOT", "WINDIR", "PATH") if k in os.environ},
                appcontainer_sid=self.sid,
            )
            _, err = proc.communicate(timeout=_SELF_TEST_SECONDS)
        except (OSError, subprocess.SubprocessError) as exc:
            return False, str(exc)
        return proc.returncode == 0, f"exit 0x{(proc.returncode or 0) & 0xFFFFFFFF:08X} {err.decode('utf-8', 'replace')[-200:]}"

    def _ensure_interpreter_readable(self, policy: SandboxPolicy) -> None:
        ok, detail = self._self_test(policy)
        if ok:
            return
        prefix = Path(os.path.realpath(sys.base_prefix))
        marker = grant_marker(prefix)
        if not marker.exists():
            # The Program Files default: every AppContainer may read and execute it.
            everyone = ctypes.c_void_p()
            if not advapi32().ConvertStringSidToSidW(ALL_APPLICATION_PACKAGES, ctypes.byref(everyone)):
                raise SandboxUnavailable("cannot resolve the ALL APPLICATION PACKAGES SID")
            try:
                grant(prefix, everyone.value, FILE_READ_EXECUTE)
            except OSError as exc:
                raise SandboxUnavailable(
                    f"the Python install at {prefix} is not readable from an AppContainer and read access could "
                    f"not be granted ({exc}); install Python from python.org for all users, or use --sandbox "
                    "container"
                ) from exc
            finally:
                _local_free(everyone.value)
            marker.parent.mkdir(parents=True, exist_ok=True)
            marker.write_text(json.dumps({"prefix": str(prefix), "sid": ALL_APPLICATION_PACKAGES}) + "\n",
                              encoding="utf-8")
            print(f"[sandbox] granted read and execute on {prefix} to ALL APPLICATION PACKAGES (as for Program "
                  f"Files), once; recorded in {marker}", file=sys.stderr, flush=True)
            ok, detail = self._self_test(policy)
        if not ok:
            raise SandboxUnavailable(f"the interpreter does not start in an AppContainer ({detail.strip()})")

    def launch(self, argv: list[str], *, cwd: Path, env: dict[str, str], limits: RunLimits) -> Any:
        if not limits.job:
            raise LaunchError("job_create_failed")  # never run outside the memory limit and kill-on-close
        try:
            return winproc.spawn(argv, cwd=str(cwd), env=env, appcontainer_sid=self.sid, job=limits.job)
        except OSError as exc:
            raise LaunchError(f"appcontainer_launch_failed: {exc}") from exc

    def close(self) -> None:
        sid, self.sid = self.sid, None
        if self.profile:
            delete_profile(self.profile)
        if sid:
            try:
                advapi32().FreeSid(sid)
            except OSError:
                pass

    @classmethod
    def sweep(cls, root: Path, owner: dict[str, Any]) -> None:
        name = profile_to_sweep(root, owner)
        if sys.platform == "win32" and name:
            delete_profile(name)


def profile_to_sweep(root: Path, owner: dict[str, Any]) -> str | None:
    """The profile a dead session's record names, only if it is the one the root's
    own name derives: a record naming any other profile is not trusted."""
    name = owner.get("profile")
    return name if isinstance(name, str) and name == profile_name(root.name) else None
