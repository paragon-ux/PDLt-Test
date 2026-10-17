#!/usr/bin/env python3
"""Task 1 of the PDL pilot (ledger L97): the fixed test suite for every ``reconcile.py``.

    py -3.11 experiments/pdl_format/grade_t1.py [EXECUTION_DIR ...]   # default: every Task 1 execution

Frozen before any pilot output was read (PLAN.md section 3). For each execution it takes the
published deliverable, picks the program that defines the CLI (the Python block that mentions
``--events``, the longest if several, else the longest Python block), and runs it in the grader
sandbox on five scenarios: the attached fixture, the fixture in reverse order, a timezone
fixture, a credit and rounding fixture, and the fixture run twice. The published deliverable is graded whatever the session's
closure (RESULT or VERIFICATION_FAILED), and the closure is reported beside it. Criteria T1-01..T1-15 of
``scoring/acceptance-criteria.csv`` are scored pass or fail; nothing is partial.

Amended after the outputs were read (ledger L97), in the extraction only, the same for both arms:
both arms wrote ``reconcile.py`` unfenced with a prose README after it, and a cancelled session
publishes the harness's UNVERIFIED banner before the model's body. The program is now the longest
run of lines in the model's body that parses as a module and mentions ``--events``. The frozen
rule's grades stay in ``grades-t1-frozen.json``. ``--first-attempt`` grades each execution's first
EXECUTE reply instead of the published one (exploratory: it leaves out the repair loop).
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))  # catalogue_runs.py lives at the repository root
from catalogue_runs import RUNS_DIR  # noqa: E402  (runs live outside the repository)
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

FIXTURES = HERE / "tasks" / "fixtures" / "task-01"
SESSIONS = RUNS_DIR / "pdl-format-pilot" / "sessions"
HEADER = "account_id,usage_date_utc,net_units,unit_price_usd,amount_usd"
NETWORK_MODULES = {"socket", "ssl", "http", "urllib", "ftplib", "smtplib", "poplib", "imaplib", "telnetlib",
                   "xmlrpc", "requests", "httpx", "aiohttp", "asyncio"}
SECRET_WORDS = ("secret", "token", "api_key", "apikey", "api-key", "password")

ACCOUNTS = (FIXTURES / "accounts.csv").read_text(encoding="utf-8")
PRICING = (FIXTURES / "pricing.json").read_text(encoding="utf-8")
EVENTS = (FIXTURES / "events.jsonl").read_text(encoding="utf-8")


def _event(event_id: str, account: str, occurred: str, kind: str, units: int) -> str:
    return json.dumps({"event_id": event_id, "account_id": account, "occurred_at": occurred,
                       "event_type": kind, "units": units})


SCENARIOS = {
    "fixture": EVENTS,
    "reversed": "\n".join(reversed(EVENTS.rstrip("\n").split("\n"))) + "\n",
    # 22:30-05:00 is the next UTC day; 01:00+02:00 is the previous one; a timestamp with no offset is rejected.
    "timezone": "\n".join([
        _event("tz-1", "acct_A", "2026-10-09T22:30:00-05:00", "usage", 10),
        _event("tz-2", "acct_A", "2026-10-10T01:00:00+02:00", "usage", 20),
        _event("tz-3", "acct_A", "2026-10-09T12:00:00", "usage", 7),
    ]) + "\n",
    # A credit applies only to its own account and UTC day; 3 units at 0.015 is 0.045, which is 0.05 half-up
    # (0.04 half-even, and 0.04 with binary floating point).
    "credits": "\n".join([
        _event("cr-1", "acct_A", "2026-10-09T10:00:00Z", "usage", 100),
        _event("cr-2", "acct_A", "2026-10-10T09:00:00Z", "usage", 50),
        _event("cr-3", "acct_A", "2026-10-10T10:00:00Z", "credit", -30),
        _event("cr-4", "acct_D", "2026-10-09T10:00:00Z", "usage", 8),
        _event("cr-5", "acct_D", "2026-10-09T11:00:00Z", "credit", -5),
    ]) + "\n",
}

# The program below runs inside the sandbox: it writes each scenario's inputs, runs the candidate as
# ``python reconcile.py --events ... --excluded ...`` in-process, and prints every output file as JSON.
DRIVER = r'''
import hashlib, json, os, runpy, sys, traceback
CANDIDATE = {candidate!r}
ACCOUNTS = {accounts!r}
PRICING = {pricing!r}
SCENARIOS = {scenarios!r}
ARGS = ["--events", "events.jsonl", "--accounts", "accounts.csv", "--pricing", "pricing.json",
        "--summary", "summary.csv", "--rejects", "rejects.jsonl", "--excluded", "excluded.jsonl"]
INPUTS = ("events.jsonl", "accounts.csv", "pricing.json")
OUTPUTS = ("summary.csv", "rejects.jsonl", "excluded.jsonl")
base = os.getcwd()
with open(os.path.join(base, "reconcile.py"), "w", encoding="utf-8", newline="") as f:
    f.write(CANDIDATE)
report = {{}}
def run_once(folder):
    old = os.getcwd(); os.chdir(folder); sys.argv = ["reconcile.py"] + ARGS
    error = None; code = 0
    try:
        runpy.run_path(os.path.join(base, "reconcile.py"), run_name="__main__")
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else (0 if exc.code is None else 1)
    except BaseException:
        error = traceback.format_exc()[-600:]; code = 1
    outputs = {{}}
    for name in OUTPUTS:
        path = os.path.join(folder, name)
        outputs[name] = open(path, "rb").read().decode("utf-8", "replace") if os.path.exists(path) else None
    os.chdir(old)
    return {{"exit": code, "error": error, "outputs": outputs}}
def digest(folder):
    return {{n: hashlib.sha256(open(os.path.join(folder, n), "rb").read()).hexdigest() for n in INPUTS}}
for name, events in SCENARIOS.items():
    folder = os.path.join(base, name); os.makedirs(folder)
    for fname, text in (("events.jsonl", events), ("accounts.csv", ACCOUNTS), ("pricing.json", PRICING)):
        with open(os.path.join(folder, fname), "w", encoding="utf-8", newline="") as f:
            f.write(text)
    before = digest(folder)
    report[name] = run_once(folder)
    if name == "fixture":
        report["fixture_again"] = run_once(folder)
        report["inputs_unchanged"] = digest(folder) == before
print("@@REPORT@@" + json.dumps(report))
'''


CANDIDATE_MARK = "\n\nCandidate deliverable:\n"  # session_engine's UNVERIFIED banner ends here


def model_body(deliverable: str) -> str:
    """The model's own body: the published text without the harness's UNVERIFIED banner."""
    text = deliverable or ""
    return text.split(CANDIDATE_MARK, 1)[1] if text.startswith("UNVERIFIED ANSWER:") and CANDIDATE_MARK in text else text


def _syntax_error_line(lines: list[str]) -> int | None:
    try:
        ast.parse("\n".join(lines))
    except SyntaxError as error:
        return error.lineno or 1
    except (ValueError, MemoryError, RecursionError):
        return 1
    return None


def code_runs(text: str) -> list[str]:
    """Maximal runs of lines that parse as a module: each run ends where the next line breaks the parse."""
    lines, runs, start = text.splitlines(), [], 0
    while start < len(lines):
        end = len(lines)
        while end > start:
            bad = _syntax_error_line(lines[start:end])
            if bad is None:
                break
            end = start + bad - 1
        if end > start:
            runs.append("\n".join(lines[start:end]).strip("\n") + "\n")
            start = end
        else:
            start += 1
    return [run for run in runs if any(not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant))
                                       for node in ast.parse(run).body)]


def candidate_program(deliverable: str) -> str | None:
    """The program that defines the CLI: the longest code run that mentions ``--events``, else the longest run."""
    runs = code_runs(model_body(deliverable))
    if not runs:
        return None
    cli = [run for run in runs if "--events" in run]
    return max(cli or runs, key=len)


def first_reply(execution_dir: Path) -> str | None:
    """The body of the execution's first EXECUTE reply, before any repair."""
    replies = sorted(execution_dir.rglob("stages/50_execution/output/*/model-response.txt"), key=lambda p: p.parent.name)
    for reply in replies:
        try:
            body = json.loads(reply.read_text(encoding="utf-8")).get("body")
        except (ValueError, AttributeError):
            continue
        if isinstance(body, str):
            return body
    return None


def imports(program: str) -> set[str] | None:
    try:
        tree = ast.parse(program)
    except SyntaxError:
        return None
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split(".")[0])
    return names


def _rows(csv_text: str | None) -> tuple[str | None, list[list[str]]]:
    if not csv_text:
        return None, []
    lines = [line for line in csv_text.replace("\r\n", "\n").split("\n") if line.strip()]
    return (lines[0] if lines else None), [line.split(",") for line in lines[1:]]


def _records(jsonl: str | None) -> list[dict]:
    out = []
    for line in (jsonl or "").replace("\r\n", "\n").split("\n"):
        if line.strip():
            try:
                value = json.loads(line)
            except ValueError:
                value = {"_unparsed": line}
            out.append(value if isinstance(value, dict) else {"_value": value})
    return out


def _event_id(record: dict) -> str | None:
    inner = record.get("record") if isinstance(record.get("record"), dict) else {}
    return record.get("event_id") or inner.get("event_id")


def _line(record: dict) -> int | None:
    try:
        return int(record.get("line_number"))
    except (TypeError, ValueError):
        return None


def score(report: dict, program: str | None) -> dict[str, bool]:
    """Criterion id -> pass, from the sandbox report."""
    fixture, again, reversed_ = report.get("fixture") or {}, report.get("fixture_again") or {}, report.get("reversed") or {}
    tz, credits = report.get("timezone") or {}, report.get("credits") or {}
    outputs = fixture.get("outputs") or {}
    header, rows = _rows(outputs.get("summary.csv"))
    rejects, excluded = _records(outputs.get("rejects.jsonl")), _records(outputs.get("excluded.jsonl"))
    summary = {(r[0], r[1]): r for r in rows if len(r) >= 5}

    def row(table: dict, account: str, day: str) -> list[str] | None:
        return table.get((account, day))

    def table_of(run: dict) -> tuple[str | None, list[list[str]], dict]:
        h, rs = _rows((run.get("outputs") or {}).get("summary.csv"))
        return h, rs, {(r[0], r[1]): r for r in rs if len(r) >= 5}

    tz_header, tz_rows, tz_table = table_of(tz)
    cr_header, cr_rows, cr_table = table_of(credits)
    rv_header, rv_rows, _ = table_of(reversed_)
    tz_rejects = _records((tz.get("outputs") or {}).get("rejects.jsonl"))
    rv_rejects = _records((reversed_.get("outputs") or {}).get("rejects.jsonl"))
    names = imports(program) if program else None

    def conflict_quarantined(reject_records: list[dict]) -> bool:
        hits = [r for r in reject_records if r.get("reason_code") == "CONFLICTING_DUPLICATE_ID"
                and _event_id(r) == "evt-conflict"]
        counted = sum(int(r.get("record_count") or 1) if isinstance(r.get("record_count"), int) else 1 for r in hits)
        return counted >= 2

    acct_a = row(summary, "acct_A", "2026-10-09")
    acct_d = row(summary, "acct_D", "2026-10-09")
    golden_a = ["acct_A", "2026-10-09", "140", "0.02", "2.80"]
    golden_d = ["acct_D", "2026-10-09", "200", "0.015", "3.00"]
    sorted_ok = all(rs == sorted(rs, key=lambda r: (r[0], r[1])) for rs in (rows, tz_rows, cr_rows) if rs)
    excluded_ok = {(_event_id(r), r.get("reason_code")) for r in excluded} >= {
        ("evt-004", "TRIAL_ACCOUNT"), ("evt-005", "INACTIVE_ACCOUNT")} and all(
        all(k in r for k in ("line_number", "event_id", "account_id", "reason_code")) for r in excluded)
    all_text = json.dumps(outputs).lower()
    secret_free = header == HEADER and not any(word in all_text for word in SECRET_WORDS)
    ran = fixture.get("exit") == 0 and not fixture.get("error") and all(
        outputs.get(n) is not None for n in ("summary.csv", "rejects.jsonl", "excluded.jsonl"))
    return {
        "T1-01": bool(ran),
        "T1-02": names is not None and all(n in sys.stdlib_module_names for n in names)
                 and not names & NETWORK_MODULES,
        "T1-03": row(tz_table, "acct_A", "2026-10-09") is not None and row(tz_table, "acct_A", "2026-10-09")[2] == "20"
                 and row(tz_table, "acct_A", "2026-10-10") is not None and row(tz_table, "acct_A", "2026-10-10")[2] == "10"
                 and any(_event_id(r) == "tz-3" for r in tz_rejects),
        "T1-04": acct_a is not None and acct_a[2] == "140" and rv_header == header and rv_rows == rows,
        "T1-05": acct_a is not None and acct_a[2] == "140" and conflict_quarantined(rejects)
                 and conflict_quarantined(rv_rejects),
        "T1-06": [r[2] if r else None for r in (row(cr_table, "acct_A", "2026-10-09"), row(cr_table, "acct_A", "2026-10-10"),
                                                row(cr_table, "acct_D", "2026-10-09"))] == ["100", "20", "3"],
        "T1-07": excluded_ok and not any(r[0] in ("acct_B", "acct_C") for r in rows),
        "T1-08": any(r.get("reason_code") == "UNKNOWN_ACCOUNT" and _line(r) == 8 for r in rejects),
        "T1-09": any(r.get("reason_code") == "INVALID_JSON" and _line(r) == 11 and ("raw_line" in r or "record" in r)
                     for r in rejects) and acct_d is not None,
        "T1-10": acct_a is not None and acct_a[4] == "2.80" and acct_d is not None and acct_d[4] == "3.00"
                 and (row(cr_table, "acct_D", "2026-10-09") or [None] * 5)[4] == "0.05",
        "T1-11": header == HEADER and tz_header == HEADER and cr_header == HEADER and sorted_ok and bool(rows),
        "T1-12": rows == [golden_a, golden_d],
        "T1-13": bool(excluded) and not ({_event_id(r) for r in rejects} & {"evt-004", "evt-005"})
                 and not ({_event_id(r) for r in excluded} - {"evt-004", "evt-005"}),
        "T1-14": bool(ran) and again.get("outputs") == outputs and report.get("inputs_unchanged") is True,
        "T1-15": bool(ran) and secret_free,
    }


def run_program(program: str) -> tuple[dict, str | None]:
    """The sandbox report of ``program`` on every scenario, and a note when the driver itself failed."""
    from pdl_taskmaster.verification.sandbox import ExecutionSandbox

    code = DRIVER.format(candidate=program, accounts=ACCOUNTS, pricing=PRICING, scenarios=SCENARIOS)
    with ExecutionSandbox(timeout_seconds=60, label="grader") as sandbox:
        out = sandbox.run_code(code)
    marker = (out.stdout or "").rfind("@@REPORT@@")
    if marker < 0:
        return {}, f"driver exit {out.exit_code}: {(out.stderr or '')[-400:]}"
    return json.loads(out.stdout[marker + len("@@REPORT@@"):].strip().splitlines()[0]), None


def grade(execution_dir: Path, first_attempt: bool = False) -> dict:
    import graders

    # Graded whatever the closure: a cancelled session publishes its failed deliverable (VERIFICATION_FAILED),
    # and the closure is reported beside the marks.
    closure, deliverable = graders.published_outcome(execution_dir)
    if first_attempt:
        deliverable = first_reply(execution_dir)
    program = candidate_program(deliverable) if deliverable else None
    report: dict = {}
    if program is None:
        note = "no deliverable" if deliverable is None else "no program"
    else:
        report, note = run_program(program)
    marks = score(report, program)
    return {"execution": str(execution_dir.relative_to(ROOT)) if execution_dir.is_relative_to(ROOT) else str(execution_dir),
            "closure": closure, "criteria": marks, "note": note,
            "errors": {k: (v or {}).get("error") for k, v in report.items() if isinstance(v, dict) and v.get("error")}}


def main(argv: list[str]) -> int:
    first_attempt = "--first-attempt" in argv
    argv = [a for a in argv if a != "--first-attempt"]
    targets = [Path(a).resolve() for a in argv] or sorted(p for p in SESSIONS.glob("T1-*/exec*") if p.is_dir())
    rows = [grade(t, first_attempt) for t in targets]
    out = SESSIONS.parent / ("grades-t1-first-attempt.json" if first_attempt else "grades-t1.json")
    out.write_text(json.dumps(rows, indent=2), encoding="utf-8")
    for r in rows:
        passed = sum(r["criteria"].values())
        print(f"{r['execution']}: {passed}/{len(r['criteria'])}" + (f" ({r['note']})" if r["note"] else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
