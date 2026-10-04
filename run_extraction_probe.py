"""Entity-extraction probe: what the bootstrap read and the prompt draft keep, per prompt.

Each catalogue prompt runs in a real headless REPL session up to the prompt review
(BOOTSTRAP_ANALYSIS, DRAFT_PROMPT and System 1 routing, nothing executed). The
session uses the harness source tree given by --root, so two trees (for example a
git worktree at an earlier commit) can be compared on the same prompts.

    python run_extraction_probe.py --label head
    python run_extraction_probe.py --root ../PDLt-armA --label original --workers 6
    python run_extraction_probe.py --compare catalogue-runs/extraction-probe-a catalogue-runs/extraction-probe-b

Measures, per prompt (the metrics never see harness code):
- literal_recall: of the request's literal tokens (numbers, quoted strings, code-like
  identifiers, file names), the share that reaches the prompt pseudocode;
- entity_count / entity_literal_recall: what the bootstrap listed as entities;
- padding: the pseudocode has a "verbatim" requirement or a line re-listing four or more
  literals that it already states elsewhere;
- gold: for prompts with hand-written critical items (GOLD), whether each item
  survives into the pseudocode.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl"

# Critical items a faithful prompt pseudocode must keep (a regex each, case-insensitive).
GOLD = {
    "01-01": [r"71\b.*97\b.*54\b", r"\b15\b", r"a_?i\s*\+\s*b_?i\s*=\s*c_?i|a\s*\+\s*b\s*=\s*c"],
    "16-01": [r"\bda\b", r"\bja\b", r"(?:not|un)\s*know|unknown|in some order|which (?:word )?means which", r"\bthree\b|\b3\b"],
    "16-02": [r"\$?25\b", r"\$?27\b", r"\$?2\b"],
    "16-03": [r"exactly one of us", r"a is a knave", r"different kinds"],
    "16-06": [r"\bB\b", r"\bS\b", r"both parents|share"],
    "16-07": [r"immediately to the left|immediately left", r"blue", r"middle", r"not live next door|not next", r"dog"],
}

_LITERALS = re.compile(
    r"\"[^\"\n]{1,60}\"|'[^'\n]{1,60}'|`[^`\n]{1,60}`"          # quoted strings
    r"|\b[A-Za-z_][A-Za-z0-9_]*\.[A-Za-z]{1,5}\b"                # file names
    r"|\b[a-z]+_[a-z0-9_]+\b|\b[a-z]+[A-Z][A-Za-z0-9]*\b"        # snake_case / camelCase
    r"|\b\d+(?:\.\d+)?\b"                                        # numbers
)


def literals(text: str) -> list[str]:
    seen: list[str] = []
    for match in _LITERALS.finditer(text):
        token = match.group(0).strip("\"'`")
        if token and token not in seen:
            seen.append(token)
    return seen


def run_one(root: Path, entry: dict, out: Path) -> dict:
    prompt_file = ROOT / "prompts" / entry["file"]
    workspace = out / "sessions" / entry["id"]
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONPATH": str(root / "src")}
    proc = subprocess.run(
        [sys.executable, "-m", "pdl_taskmaster.host.repl", "--candidate-repo", str(root), "--worker", "api",
         "--non-interactive", "--new-session", "--workspace-root", str(workspace), "--prompt-file", str(prompt_file)],
        cwd=root, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=900, env=env,
        stdin=subprocess.DEVNULL,
    )
    row = score(entry, workspace)
    row["exit"] = proc.returncode
    if proc.returncode != 2 and row["status"] == "ok":
        row["status"] = "no_prompt_review"
    if row["status"] != "ok":
        row["tail"] = (proc.stdout + proc.stderr)[-400:]
    return row


def score(entry: dict, workspace: Path) -> dict:
    """The metrics for one session folder (also used to rescore an interrupted probe)."""
    request = (ROOT / "prompts" / entry["file"]).read_text(encoding="utf-8-sig").strip()
    row: dict = {"id": entry["id"], "category": entry["category"]}
    turns = list(workspace.glob("W-*/turns/turn_001"))
    if not turns or not (turns[0] / "stages/10_prompt/output/current.md").is_file():
        row["status"] = "no_prompt_review"
        return row
    turn = turns[0]
    raw = (turn / "stages/10_prompt/output/0001-bootstrap_analysis/model-response.txt").read_text(encoding="utf-8")
    match = re.search(r"\{.*\}", raw, re.S)
    analysis = json.loads(match.group(0)) if match else {}
    entities = analysis.get("task_entities") or []
    surfaces = [e if isinstance(e, str) else str(e.get("surface", "")) for e in entities]
    body = (turn / "stages/10_prompt/output/current.md").read_text(encoding="utf-8")
    events = [json.loads(line)["kind"] for line in (turn / "events/events.jsonl").read_text(encoding="utf-8").splitlines()]
    request_literals = literals(request)
    kept = [t for t in request_literals if t in body]
    # Padding: a line that only re-lists four or more literals already stated elsewhere in the
    # pseudocode (an input-data line, stated once, is not padding).
    lines = body.splitlines()
    listing_lines = [
        line for i, line in enumerate(lines)
        if len(literals(line)) >= 4
        and all(t in "\n".join(lines[:i] + lines[i + 1:]) for t in literals(line))
    ]
    row.update(
        status="ok",
        entities=entities,
        entity_count=len(entities),
        request_literals=len(request_literals),
        literal_recall=round(len(kept) / len(request_literals), 3) if request_literals else None,
        entity_literal_recall=(round(sum(any(t in s for s in surfaces) for t in request_literals) / len(request_literals), 3)
                               if request_literals else None),
        padding=("verbatim" in body.lower()) or bool(listing_lines),
        coverage_retry="TASK_ENTITY_COVERAGE_RETRY" in events,
        prompt_body=body,
    )
    if entry["id"] in GOLD:
        hits = [bool(re.search(p, body, re.I | re.S)) for p in GOLD[entry["id"]]]
        row["gold"] = round(sum(hits) / len(hits), 3)
    return row


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if r.get("status") == "ok"]
    def mean(key):
        values = [r[key] for r in ok if r.get(key) is not None]
        return round(sum(values) / len(values), 3) if values else None
    return {
        "prompts": len(rows), "at_prompt_review": len(ok),
        "literal_recall": mean("literal_recall"), "entity_literal_recall": mean("entity_literal_recall"),
        "entities_per_prompt": mean("entity_count"), "padding": sum(bool(r.get("padding")) for r in ok),
        "coverage_retries": sum(bool(r.get("coverage_retry")) for r in ok), "gold": mean("gold"),
    }


def compare(a: Path, b: Path) -> int:
    ra = {r["id"]: r for r in json.loads((a / "results.json").read_text(encoding="utf-8"))["rows"]}
    rb = {r["id"]: r for r in json.loads((b / "results.json").read_text(encoding="utf-8"))["rows"]}
    print(f"{'metric':<24}{a.name:>34}{b.name:>34}")
    sa, sb = summarize(list(ra.values())), summarize(list(rb.values()))
    for key in sa:
        print(f"{key:<24}{str(sa[key]):>34}{str(sb[key]):>34}")
    print("\nper prompt, literal recall changes of 0.1 or more, and gold:")
    for pid in sorted(set(ra) & set(rb)):
        la, lb = ra[pid].get("literal_recall"), rb[pid].get("literal_recall")
        ga, gb = ra[pid].get("gold"), rb[pid].get("gold")
        if (la is not None and lb is not None and abs(la - lb) >= 0.1) or ga is not None or gb is not None:
            print(f"  {pid}: literal {la} -> {lb}   gold {ga} -> {gb}   padding {ra[pid].get('padding')} -> {rb[pid].get('padding')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT, help="harness tree to run (default: this repository)")
    parser.add_argument("--label", default="probe")
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--ids", default=None, help="comma-separated prompt ids (default: all)")
    parser.add_argument("--compare", nargs=2, type=Path, default=None)
    parser.add_argument("--rescore", type=Path, default=None,
                        help="recompute results.json from a probe folder's saved sessions (e.g. after an interruption)")
    args = parser.parse_args()
    if args.compare:
        return compare(*args.compare)
    if args.rescore:
        entries = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
        rows = [score(e, args.rescore / "sessions" / e["id"]) for e in entries
                if (args.rescore / "sessions" / e["id"]).is_dir()]
        (args.rescore / "results.json").write_text(json.dumps({"root": "rescored", "rows": rows}, indent=2,
                                                              ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(summarize(rows), indent=2))
        return 0
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("OPENROUTER_API_KEY is not set", file=sys.stderr)
        return 4
    entries = [json.loads(line) for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines() if line.strip()]
    if args.ids:
        wanted = set(args.ids.split(","))
        entries = [e for e in entries if e["id"] in wanted]
    out = ROOT / "catalogue-runs" / f"extraction-probe-{args.label}-{datetime.now():%Y%m%d-%H%M%S}"
    out.mkdir(parents=True)
    root = args.root.resolve()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        rows = list(pool.map(lambda e: run_one(root, e, out), entries))
    (out / "results.json").write_text(json.dumps({"root": str(root), "rows": rows}, indent=2, ensure_ascii=False) + "\n",
                                      encoding="utf-8")
    print(json.dumps(summarize(rows), indent=2))
    print(f"results: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
