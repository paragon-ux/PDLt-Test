"""Keep the bundled contracts identical to the repository's and their manifest hashes
current (GUARD-05).

Copies every file listed in ``contracts/CONTRACT_MANIFEST.json`` from ``contracts/`` to
``src/pdl_taskmaster/contracts/``, then rewrites each ``sha256`` in both manifests
(LF-normalized, as ``tests/test_harness_anti_overfitting.py`` hashes them).

usage:
  python scripts/sync_contracts.py           # copy and rehash
  python scripts/sync_contracts.py --check   # report differences, change nothing
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLED = ROOT / "src" / "pdl_taskmaster"
TEXT = {".json", ".md", ".txt"}


def _bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    return raw.replace(b"\r\n", b"\n") if path.suffix in TEXT else raw


def _dump(data: dict) -> bytes:
    return (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def main(check: bool) -> int:
    manifest_path = ROOT / "contracts" / "CONTRACT_MANIFEST.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    differences = []
    for entry in manifest["files"]:
        source = ROOT / entry["path"]
        bundled = BUNDLED / entry["path"]
        if _bytes(source) != (_bytes(bundled) if bundled.is_file() else None):
            differences.append(f"copy {entry['path']}")
            if not check:
                bundled.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, bundled)
        digest = hashlib.sha256(_bytes(source)).hexdigest()
        if entry["sha256"] != digest:
            differences.append(f"hash {entry['path']}")
            entry["sha256"] = digest
    if not check:
        for target in (manifest_path, BUNDLED / "contracts" / "CONTRACT_MANIFEST.json"):
            target.write_bytes(_dump(manifest))
    print("\n".join(differences) or "contracts in sync")
    return 1 if (check and differences) else 0


if __name__ == "__main__":
    sys.exit(main("--check" in sys.argv[1:]))
