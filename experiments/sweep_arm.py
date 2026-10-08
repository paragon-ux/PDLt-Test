#!/usr/bin/env python3
"""Run one route of the five-route benchmark and record what it cost on the OpenRouter key.

    python experiments/sweep_arm.py <route> [extra run_catalogue.py arguments]

Routes: control, unconfirmed, unconfirmed-draft-execute, confirmed, confirmed-draft-execute.

It starts `run_catalogue.py` with the benchmark's fixed settings (`openai/gpt-oss-120b`, `--reasoning low`,
`--timeout 300`; Tier D1 at the shipped default), reads the key's usage counter before and after, and writes the
difference to `KEY_USAGE.json` in the run folder, where `experiments/five_arm_report.py` picks it up. The counter
includes the System 1 calls and moves a little after a run ends, so the figure is good to a few cents. Run the
routes one after another, never at the same time: a second sweep on the key would be counted in the first.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGS = ROOT / "catalogue-runs" / "sweep-logs"
MODEL = "openai/gpt-oss-120b"
ROUTES = {
    "control": ["--route", "control"],
    "unconfirmed": ["--route", "unconfirmed"],
    "unconfirmed-draft-execute": ["--route", "unconfirmed", "--draft-execute"],
    "confirmed": ["--route", "confirmed"],
    "confirmed-draft-execute": ["--route", "confirmed", "--draft-execute"],
}
MIN_REMAINING_USD = 1.0  # refuse to start a sweep the key may not be able to finish


def key_state() -> dict:
    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/key",
        headers={"Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}", "User-Agent": "pdlt-sweep/1.0"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        data = json.load(response)["data"]
    return {"usage": data["usage"], "remaining": data["limit_remaining"]}


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ROUTES:
        print(__doc__)
        return 2
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set")
        return 2
    route, extra = argv[0], argv[1:]
    before = key_state()
    if before["remaining"] is not None and before["remaining"] < MIN_REMAINING_USD:
        print(f"refusing to start {route}: only ${before['remaining']:.2f} left on the key")
        return 3

    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"{route}.log"
    if log.exists():  # a later sweep of the same route keeps the earlier log
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime(log.stat().st_mtime))
        log.rename(log.with_name(f"{route}.{stamp}.log"))
    command = [sys.executable, "-u", str(ROOT / "run_catalogue.py"), "--model", MODEL, "--reasoning", "low",
               "--timeout", "300", *ROUTES[route], *extra]
    started = time.time()
    with open(log, "w", encoding="utf-8") as handle:
        code = subprocess.run(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT,
                              env={**os.environ, "PYTHONIOENCODING": "utf-8"}).returncode
    wall = time.time() - started
    time.sleep(20)  # let the key's usage counter settle
    after = key_state()

    match = re.search(r"^Results: (.+)$", log.read_text(encoding="utf-8", errors="replace"), re.M)
    record = {
        "route": route,
        "args": command[3:],
        "exit": code,
        "wall_s": round(wall, 1),
        "run_dir": match.group(1).strip() if match else None,
        "usage_before": before["usage"],
        "usage_after": after["usage"],
        "cost_usd": round(after["usage"] - before["usage"], 4),
        "remaining_after": after["remaining"],
    }
    if record["run_dir"]:
        (Path(record["run_dir"]) / "KEY_USAGE.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    print(json.dumps(record))
    return 0  # run_catalogue exits 1 when any prompt fails; that is a result, not an error here


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
