"""Live check of the task-entity channel, both sides.

Each request runs in a real headless REPL session up to the prompt review. Then:

- identifier requests: every expected identifier is extracted as an entity and is
  spelled exactly so in the prompt pseudocode (fidelity kept);
- narrative requests: none of the story's or puzzle's figures is extracted as an
  entity, and the pseudocode carries no "verbatim" requirement (no padding).

    python run_entity_check.py

Writes catalogue-runs/entity-check-<ts>/results.json. Exit 0 when every case holds,
1 otherwise, 4 without OPENROUTER_API_KEY.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent

IDENTIFIER_CASES = [
    ("Write a Python function parse_invoice_line(line) that splits one line of invoices_2026.csv on ';' and "
     "returns a dict with the keys 'invoice_id' and 'amount_cents' (amount_cents as an int).",
     ["parse_invoice_line", "invoice_id", "amount_cents"]),
    ("Rename the configuration key max_retries to retry_limit in settings.yaml and update the function "
     "load_settings so it reads the new key.",
     ["max_retries", "retry_limit", "settings.yaml", "load_settings"]),
    ("Draft a short email to my landlord about the broken heater in apartment 4B. Quote the maintenance ticket "
     "number TCK-20931.",
     ["4B", "TCK-20931"]),
    ("Write a Python HTTP server that listens on port 8443 and closes a connection after a 750 ms read timeout.",
     ["8443"]),
]

NARRATIVE_CASES = [
    ((ROOT / "prompts" / "16_logic_and_reasoning" / "missing_dollar.txt").read_text(encoding="utf-8-sig").strip(),
     ["$30", "$10", "$25", "$5", "$1", "$2", "$9", "$27", "$29"]),
    ((ROOT / "prompts" / "16_logic_and_reasoning" / "elevator_riddle.txt").read_text(encoding="utf-8-sig").strip(),
     ["10th", "7th"]),
    ("A farmer has 17 sheep. All but 9 run away. How many sheep does the farmer have left? Explain briefly.",
     ["17", "9"]),
    ("Tom is twice as old as his sister was when Tom was as old as his sister is now. Tom is 24. How old is his "
     "sister?",
     ["24"]),
]


def run_session(prompt: str, workspace: Path) -> tuple[list[str], str, list[str]]:
    """(extracted entities, prompt pseudocode, entity events) for one request."""
    proc = subprocess.run(
        [sys.executable, "-m", "pdl_taskmaster.host.repl", "--worker", "api", "--dev", "--non-interactive",
         "--new-session", "--workspace-root", str(workspace), "--prompt", prompt],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600,
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    if proc.returncode != 2:  # 2: halted at the prompt review, as intended
        raise RuntimeError(f"session exit {proc.returncode}: {(proc.stdout + proc.stderr)[-600:]}")
    (turn,) = workspace.glob("W-*/turns/turn_001")
    raw = (turn / "stages/10_prompt/output/0001-bootstrap_analysis/model-response.txt").read_text(encoding="utf-8")
    match = re.search(r"\{.*\}", raw, re.S)
    entities = list(json.loads(match.group(0)).get("task_entities") or []) if match else []
    prompt_body = (turn / "stages/10_prompt/output/current.md").read_text(encoding="utf-8")
    events = [json.loads(line)["kind"] for line in (turn / "events/events.jsonl").read_text(encoding="utf-8").splitlines()]
    return entities, prompt_body, [e for e in events if "ENTITY" in e]


def main() -> int:
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 4
    out = ROOT / "catalogue-runs" / f"entity-check-{datetime.now():%Y%m%d-%H%M%S}"
    rows = []
    for side, cases in (("identifiers", IDENTIFIER_CASES), ("narrative", NARRATIVE_CASES)):
        for index, (prompt, tokens) in enumerate(cases, 1):
            try:
                entities, body, events = run_session(prompt, out / f"{side}-{index}")
            except Exception as exc:
                rows.append({"side": side, "case": index, "ok": False, "error": str(exc)})
                print(f"{side} {index}: ERROR {exc}", flush=True)
                continue
            if side == "identifiers":
                missing_entity = [t for t in tokens if not any(t in e for e in entities)]
                missing_body = [t for t in tokens if t not in body]
                ok = not missing_entity and not missing_body
                detail = {"missing_entity": missing_entity, "missing_in_prompt": missing_body}
            else:
                figures_as_entities = [t for t in tokens if any(t == e.strip() or t in e for e in entities)]
                verbatim = "verbatim" in body.lower()
                ok = not figures_as_entities and not verbatim
                detail = {"figures_as_entities": figures_as_entities, "verbatim_requirement": verbatim}
            rows.append({"side": side, "case": index, "ok": ok, "entities": entities, "events": events,
                         "prompt_body": body, **detail})
            print(f"{side} {index}: {'ok' if ok else 'FAIL'}  entities={entities}  {detail}", flush=True)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    passed = sum(r["ok"] for r in rows)
    print(f"\n{passed}/{len(rows)} cases hold; results: {out}")
    return 0 if passed == len(rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
