"""Replace-on-write for state files.

A state file is written to a temporary file beside it and moved into place with
``os.replace``, so an interruption (Ctrl+C, a crash) leaves either the old or the new
file, never a truncated one. There is no fsync: ADR-0011 keeps active-turn writes
fast; the guarantee is against partial files, not against power loss.
"""
from __future__ import annotations

import os
import tempfile
from pathlib import Path


def replace_text(path: str | Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
