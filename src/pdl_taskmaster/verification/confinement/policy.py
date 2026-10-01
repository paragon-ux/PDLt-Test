"""The session confinement policy: what a sandboxed program may read, write and run.

Built once per session from facts about this machine (the base interpreter, its
standard library, the shared libraries the OS loader needs) and the session's own
work directory. Every backend enforces the same policy in its own native terms.
"""
from __future__ import annotations

import os
import struct
import sys
import sysconfig
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SandboxPolicy:
    """One session's confinement policy.

    ``write_roots`` are read-write; ``read_roots`` are read-only; ``exec_paths``
    are the only files that may be executed (the interpreter, and on Linux the ELF
    loader it names). Network and process creation are denied unless allowed.
    """

    session_root: Path
    write_roots: tuple[Path, ...]
    read_roots: tuple[Path, ...]
    exec_paths: tuple[Path, ...]
    network: bool = False
    processes: bool = False

    @property
    def interpreter(self) -> Path:
        return self.exec_paths[0]


def base_interpreter() -> Path:
    """The base installation's interpreter, never a virtual-environment shim: the read
    set is then only the base install, and on Windows no launcher process sits
    between the host and the program."""
    return Path(os.path.realpath(getattr(sys, "_base_executable", None) or sys.executable))


def stdlib_dirs() -> tuple[Path, ...]:
    """The base installation's standard library: pure modules and extension modules."""
    paths = sysconfig.get_paths(vars={"base": sys.base_prefix, "platbase": sys.base_exec_prefix})
    found: list[Path] = []
    for candidate in (
        os.path.dirname(os.__file__),
        paths.get("stdlib"),
        paths.get("platstdlib"),
        os.path.join(paths.get("platstdlib") or "", "lib-dynload"),
        os.path.join(sys.base_prefix, "DLLs"),
    ):
        if candidate and os.path.isdir(candidate):
            found.append(Path(os.path.realpath(candidate)))
    return _dedupe(found)


def elf_interpreter(executable: Path) -> Path | None:
    """The program interpreter (PT_INTERP) an ELF executable names, e.g. the dynamic
    loader. The kernel opens it for execution, so it needs the execute right too."""
    try:
        with open(executable, "rb") as handle:
            ident = handle.read(16)
            if ident[:4] != b"\x7fELF":
                return None
            is64, endian = ident[4] == 2, "<" if ident[5] == 1 else ">"
            header = handle.read(48 if is64 else 36)  # the header after e_ident
            phoff = struct.unpack_from(endian + ("Q" if is64 else "I"), header, 16 if is64 else 12)[0]
            phentsize, phnum = struct.unpack_from(endian + "HH", header, 38 if is64 else 26)
            for index in range(phnum):
                handle.seek(phoff + index * phentsize)
                entry = handle.read(phentsize)
                if struct.unpack(endian + "I", entry[:4])[0] != 3:  # PT_INTERP
                    continue
                if is64:
                    offset, size = struct.unpack(endian + "8xQ16xQ", entry[:40])
                else:
                    offset, size = struct.unpack(endian + "4xI8xI", entry[:20])
                handle.seek(offset)
                name = handle.read(size).split(b"\0", 1)[0].decode()
                return Path(os.path.realpath(name))
    except (OSError, struct.error, UnicodeDecodeError):
        return None
    return None


def shared_python_library() -> Path | None:
    """libpython when the interpreter links it dynamically."""
    if not sysconfig.get_config_var("Py_ENABLE_SHARED"):
        return None
    libdir, name = sysconfig.get_config_var("LIBDIR"), sysconfig.get_config_var("LDLIBRARY")
    if libdir and name:
        path = Path(libdir) / name
        if path.exists():
            return Path(os.path.realpath(path))
    return None


def system_read_roots(platform: str = sys.platform) -> tuple[Path, ...]:
    """What the OS loader and the C library read on this platform. Never the home
    directory, the repository or /proc."""
    if platform.startswith("linux"):
        candidates = [
            "/usr", "/lib", "/lib32", "/lib64", "/libx32", "/etc/ld.so.cache", "/etc/localtime",
            "/dev/null", "/dev/urandom",
        ]
    elif platform == "darwin":
        candidates = [
            "/usr/lib", "/System/Library", "/System/Volumes/Preboot/Cryptexes/OS", "/private/etc/localtime",
            "/private/var/db/timezone", "/dev/null", "/dev/urandom", "/dev/random",
        ]
    elif platform == "win32":
        # AppContainer processes read the system directories through the default
        # ALL APPLICATION PACKAGES grant; nothing is granted here.
        candidates = []
    else:
        candidates = []
    return _dedupe(Path(os.path.realpath(c)) for c in candidates if os.path.exists(c))


def build_policy(
    session_root: Path, write_root: Path, *, network: bool = False, processes: bool = False,
) -> SandboxPolicy:
    interpreter = base_interpreter()
    exec_paths = [interpreter]
    if sys.platform.startswith("linux"):
        loader = elf_interpreter(interpreter)
        if loader is not None:
            exec_paths.append(loader)
    elif sys.platform == "darwin":
        # A framework build's bin/python re-executes the application bundle's binary.
        bundled = Path(sys.base_prefix) / "Resources" / "Python.app" / "Contents" / "MacOS" / "Python"
        if bundled.exists():
            exec_paths.append(Path(os.path.realpath(bundled)))
    write_root = Path(os.path.realpath(write_root))
    read = [write_root, *stdlib_dirs(), *system_read_roots()]
    library = shared_python_library()
    if library is not None:
        read.append(library)
    read += exec_paths
    return SandboxPolicy(
        session_root=Path(os.path.realpath(session_root)),
        write_roots=(write_root,),
        read_roots=_dedupe(p for p in read if p.exists()),
        exec_paths=_dedupe(exec_paths),
        network=network,
        processes=processes,
    )


def _dedupe(paths) -> tuple[Path, ...]:
    seen: list[Path] = []
    for path in paths:
        if path not in seen:
            seen.append(path)
    return tuple(seen)
