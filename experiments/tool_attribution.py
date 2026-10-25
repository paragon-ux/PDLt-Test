"""Tool attribution for paired catalogue runs (ledger L143): per-arm outcomes, in-call tool use, silent false positives
and paired tests, read only from the runs' own records, so the report can be regenerated and checked.

    python experiments/tool_attribution.py RUN [RUN ...] [--md report.md] [--trace ID:REPEAT ...] [--allow-missing]

RUN is a run folder name under the runs folder (catalogue_runs.py) or a path; the first run is the reference arm that
the others are paired against, by prompt ID and repeat. Rules:

- outcome: ``result.json``'s ``verdict``, its ground-truth grade (``ground_truth_grade.grade``: PASS, FAIL, MANUAL,
  N/A) and the catalogue's own outcome class (``run_catalogue.outcome_class``: one definition of a pass);
- provenance level: ``verification.level`` of the ``provenance.json`` under the result's session folder (none for
  Control, which publishes none);
- tool use: the ``AGENT_TOOL_CALL`` events of every ``events.jsonl`` under the session folder; a call's tool is
  ``payload.tool``; a submission is accepted when ``payload.accepted`` is true and rejected when false, with the
  error codes of ``payload.envelope.errors``; work tools (``run_python``, ``read_attempt``) carry no acceptance and
  are counted as calls; attempts are ``payload.attempt``;
- a silent false positive is a CLOSED_SUCCESS whose ground truth is FAIL; its denominator is the runs with a
  decided ground truth (PASS or FAIL); MANUAL and N/A are undecided and counted apart, never as passes;
- paired tests: exact two-sided McNemar over runs (an undecided grade counts as not passed; the doubly decided
  subset beside it) and a two-sided sign test over prompts (each prompt's passes summed over its repeats). Repeats of
  a prompt are not independent, so the run-level test overstates the evidence; the prompt-level test is the
  conservative one.

Everything here is correlational: which runs used a tool and how they ended. A causal statement needs a run's own
event trace (``--trace``), and even then it explains that run, not an effect size. Missing or malformed records are
listed under "Data problems"; with any, the exit status is 1 unless ``--allow-missing``."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalogue_runs import RUNS_DIR  # noqa: E402  (runs live outside the repository)
from experiments.five_arm_report import exact_mcnemar  # noqa: E402
import run_catalogue  # noqa: E402  (one definition of a pass, shared with the scoreboards)

WORK_TOOLS = ("read_attempt", "run_python")
# The host's own events a trace shows beside the tool calls: what it concluded after each attempt.
TRACE_EVENTS = {"VERIFICATION_NOT_APPLICABLE": "reason", "WITNESS_LITERAL_IN_PROGRAM": "block",
                "EXECUTE_WIRE_FAILURE": "reason", "POSITIVE_RESULT_ARGUED": None, "NEGATIVE_CLAIM_UNCHECKED": "basis",
                "VERIFICATION_PASSED": "sandbox_reproduced", "CLOSED_UNVERIFIED": "reason",
                "OPERATION_MATERIALIZED": "invocation_id"}


def _resolve(name: str) -> Path:
    path = Path(name)
    return path if path.is_dir() else RUNS_DIR / name


def _jsonl(path: Path, problems: list[str], where: str) -> list[dict]:
    records = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            problems.append(f"{where}: {path.name} line {number} is not JSON")
    return records


def load_run(run_dir: Path, problems: list[str]) -> dict:
    """One arm: its RUN_META and one record per result folder, keyed by (prompt ID, repeat)."""
    meta: dict = {}
    try:
        meta = json.loads((run_dir / "RUN_META.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        problems.append(f"{run_dir.name}: RUN_META.json unreadable ({exc.__class__.__name__})")
    results: dict[tuple[str, int], dict] = {}
    folders = sorted(p for p in (run_dir / "results").glob("*") if p.is_dir()) if (run_dir / "results").is_dir() else []
    if not folders:
        problems.append(f"{run_dir.name}: no result folders")
    agent_tools = bool((meta.get("run_settings") or {}).get("agent_tools"))
    for folder in folders:
        where = f"{run_dir.name}/{folder.name}"
        try:
            result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            problems.append(f"{where}: result.json missing or unreadable ({exc.__class__.__name__})")
            continue
        if "ground_truth_grade" not in result:
            problems.append(f"{where}: no ground_truth_grade recorded")
        key = (str(result.get("id")), int(result.get("repeat") or 1))
        if key in results:
            problems.append(f"{where}: a second result for {key[0]} r{key[1]}")
        events_files = sorted(folder.glob("session/**/events.jsonl"))
        events = [e for f in events_files for e in _jsonl(f, problems, where)]
        events.sort(key=lambda e: e.get("at_utc") or "")
        if agent_tools and not events_files:
            problems.append(f"{where}: an --agent-tools run with no events.jsonl")
        levels = []
        for prov in sorted(folder.glob("session/**/provenance.json")):
            try:
                levels.append(json.loads(prov.read_text(encoding="utf-8"))["verification"]["level"])
            except (OSError, ValueError, KeyError, TypeError):
                problems.append(f"{where}: {prov.name} unreadable")
        results[key] = {
            "id": key[0], "repeat": key[1], "verdict": result.get("verdict"),
            "grade": run_catalogue.gt_grade(result), "outcome": run_catalogue.outcome_class(result),
            "level": levels[-1] if levels else None,
            "tools": [e["payload"] for e in events if e.get("kind") == "AGENT_TOOL_CALL"],
            "timeline": [e for e in events if e.get("kind") == "AGENT_TOOL_CALL" or e.get("kind") in TRACE_EVENTS],
            "elapsed": result.get("elapsed_seconds"),
        }
    return {"name": run_dir.name, "dir": run_dir, "meta": meta, "agent_tools": agent_tools, "results": results}


def _rate(num: int, den: int) -> str:
    return f"{num}/{den} ({100 * num / den:.1f}%)" if den else f"{num}/0"


def silent_false_positive(r: dict) -> bool:
    return r["verdict"] == "CLOSED_SUCCESS" and r["grade"] == "FAIL"


def arm_summary(arm: dict) -> dict:
    rs = list(arm["results"].values())
    grades = Counter(r["grade"] for r in rs)
    outcomes = Counter(r["outcome"] for r in rs)
    decided = grades["PASS"] + grades["FAIL"]
    tools: dict[str, Counter] = defaultdict(Counter)
    codes: Counter = Counter()
    for r in rs:
        for name in {c["tool"] for c in r["tools"]}:
            tools[name]["runs"] += 1
        for call in r["tools"]:
            tools[call["tool"]]["calls"] += 1
            if call.get("accepted") is True:
                tools[call["tool"]]["accepted"] += 1
            elif call.get("accepted") is False:
                tools[call["tool"]]["rejected"] += 1
                codes.update(e.get("code") for e in (call.get("envelope") or {}).get("errors") or [])
    return {"runs": len(rs), "grades": grades, "outcomes": outcomes, "decided": decided,
            "verdicts": Counter(r["verdict"] for r in rs), "levels": Counter(r["level"] for r in rs),
            "false_positives": sorted(f"{r['id']} r{r['repeat']}" for r in rs if silent_false_positive(r)),
            "tools": tools, "rejection_codes": codes}


def paired(reference: dict, other: dict, problems: list[str]) -> dict:
    keys = sorted(set(reference["results"]) & set(other["results"]))
    for key in sorted(set(reference["results"]) ^ set(other["results"])):
        problems.append(f"{key[0]} r{key[1]} is not in both {reference['name']} and {other['name']}")
    a = [reference["results"][k] for k in keys]
    b = [other["results"][k] for k in keys]
    passed = [(x["grade"] == "PASS", y["grade"] == "PASS") for x, y in zip(a, b)]
    both = [(x["grade"] == "PASS", y["grade"] == "PASS") for x, y in zip(a, b)
            if x["grade"] in ("PASS", "FAIL") and y["grade"] in ("PASS", "FAIL")]
    fps = [(silent_false_positive(x), silent_false_positive(y)) for x, y in zip(a, b)]
    per_prompt: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for (x, y), k in zip(passed, keys):
        per_prompt[k[0]][0] += x
        per_prompt[k[0]][1] += y
    wins = sum(p[0] > p[1] for p in per_prompt.values())
    losses = sum(p[0] < p[1] for p in per_prompt.values())

    def discordant(pairs):
        only_a = sum(x and not y for x, y in pairs)
        only_b = sum(y and not x for x, y in pairs)
        return {"n": len(pairs), "a": sum(x for x, _ in pairs), "b": sum(y for _, y in pairs), "only_a": only_a,
                "only_b": only_b, "p": exact_mcnemar(only_a, only_b)}

    return {"other": other["name"], "passes": discordant(passed), "decided": discordant(both),
            "false_positives": discordant(fps), "prompts": len(per_prompt), "wins": wins, "losses": losses,
            "ties": len(per_prompt) - wins - losses, "sign_p": exact_mcnemar(wins, losses)}


def _tool_cell(r: dict) -> str:
    if not r["tools"]:
        return ""
    count = Counter(c["tool"] for c in r["tools"])
    parts = [f"{t.replace('submit_', 's:').replace('run_python', 'rp').replace('read_attempt', 'ra')}"
             f" {count[t]}" for t in sorted(count)]
    rejected = sum(c.get("accepted") is False for c in r["tools"])
    return ", ".join(parts) + (f" ({rejected} rejected)" if rejected else "")


def trace(arms: list[dict], spec: str) -> list[str]:
    prompt, _, repeat = spec.partition(":")
    lines = [f"#### Trace {prompt} r{repeat or 1}", ""]
    for arm in arms:
        r = arm["results"].get((prompt, int(repeat or 1)))
        if r is None:
            lines.append(f"- {arm['name']}: no such result")
            continue
        lines.append(f"- **{arm['name']}**: {r['verdict']}, ground truth {r['grade']}, level {r['level']}")
        for event in r["timeline"]:
            payload = event.get("payload") or {}
            if event["kind"] != "AGENT_TOOL_CALL":
                if event["kind"] == "OPERATION_MATERIALIZED" and "execute" not in str(payload.get("invocation_id")):
                    continue
                key = TRACE_EVENTS[event["kind"]]
                lines.append(f"  - host: {event['kind']}" + (f" ({key}: {payload.get(key)})" if key else ""))
                continue
            state = {True: "accepted", False: "rejected", None: "ran"}[payload.get("accepted")]
            codes = ", ".join(e.get("code", "?") for e in (payload.get("envelope") or {}).get("errors") or [])
            lines.append(f"  - attempt {payload.get('attempt')}: {payload.get('tool')} {state}" + (f" ({codes})" if codes else ""))
    return lines + [""]


def _script_commit() -> str:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True,
                              timeout=30).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain", "--", "experiments/tool_attribution.py"], cwd=ROOT,
                               capture_output=True, text=True, timeout=30).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return "unknown"
    return head + (" (script modified)" if dirty else "")


def report(arms: list[dict], traces: list[str], problems: list[str]) -> str:
    out = ["# Tool attribution report", "",
           "Generated by `experiments/tool_attribution.py`; the extraction rules are in its docstring. "
           "Correlational throughout: see the note on causation below.", "", "## Inputs", "",
           "| Arm | Commit | Dirty tree (WORKTREE.diff SHA-256) | Route | Agent tools | Reasoning | Providers | Prompts | Repeat |",
           "|---|---|---|---|---|---|---|---|---|"]
    for arm in arms:
        m, code, settings = arm["meta"], arm["meta"].get("code") or {}, arm["meta"].get("run_settings") or {}
        diff = arm["dir"] / (code.get("diff_file") or "WORKTREE.diff")
        sha = hashlib.sha256(diff.read_bytes()).hexdigest()[:12] if code.get("dirty") and diff.is_file() else "clean"
        out.append(f"| `{arm['name']}` | `{(code.get('commit') or '?')[:8]}` | {sha} | {m.get('route')} | "
                   f"{arm['agent_tools']} | {m.get('reasoning_effort')} | {settings.get('providers')} | "
                   f"{m.get('prompt_id_filter') or m.get('category_filter') or 'all'} | {m.get('repeat')} |")
    out += ["", f"Script commit: `{_script_commit()}`.", "", "## Outcomes per arm", "",
            "| Arm | Runs | Ground truth PASS / FAIL / MANUAL / N/A | Ground-truth pass rate (decided) | "
            "Catalogue passes (all runs) | Silent false positives (of decided) | Verdicts | Provenance levels |",
            "|---|---|---|---|---|---|---|---|"]
    summaries = [arm_summary(arm) for arm in arms]
    for arm, s in zip(arms, summaries):
        g = s["grades"]
        out.append(f"| `{arm['name']}` | {s['runs']} | {g['PASS']} / {g['FAIL']} / {g['MANUAL']} / {g['N/A']} | "
                   f"{_rate(g['PASS'], s['decided'])} | {_rate(s['outcomes']['PASS'], s['runs'])} | "
                   f"{_rate(len(s['false_positives']), s['decided'])}: {', '.join(s['false_positives']) or 'none'} | "
                   f"{', '.join(f'{k} {v}' for k, v in sorted(s['verdicts'].items(), key=str))} | "
                   f"{', '.join(f'{k} {v}' for k, v in sorted(s['levels'].items(), key=str))} |")
    out += ["", "## In-call tool use (correlational)", "",
            "| Arm | Tool | Calls | Runs that called it | Accepted | Rejected |", "|---|---|---|---|---|---|"]
    for arm, s in zip(arms, summaries):
        for name, c in sorted(s["tools"].items()):
            work = name in WORK_TOOLS
            out.append(f"| `{arm['name']}` | `{name}` | {c['calls']} | {c['runs']} of {s['runs']} | "
                       f"{'n/a' if work else c['accepted']} | {'n/a' if work else c['rejected']} |")
        if s["tools"]:
            total = sum(c["calls"] for c in s["tools"].values())
            codes = ", ".join(f"{k} {v}" for k, v in s["rejection_codes"].most_common())
            out.append(f"| `{arm['name']}` | all | {total} | | | rejection codes: {codes or 'none'} |")
    out += ["", "## Paired comparisons (reference: first arm)", "",
            "| Against | Measure | Pairs | Reference | Other | Reference only / other only | Exact McNemar p |",
            "|---|---|---|---|---|---|---|"]
    pairs = [paired(arms[0], other, problems) for other in arms[1:]]
    for p in pairs:
        for label, d in (("ground-truth passes (undecided = not passed)", p["passes"]),
                         ("ground-truth passes, both decided", p["decided"]),
                         ("silent false positives", p["false_positives"])):
            out.append(f"| `{p['other']}` | {label} | {d['n']} | {d['a']} | {d['b']} | {d['only_a']} / {d['only_b']} | "
                       f"{d['p']:.4f} |")
        out.append(f"| `{p['other']}` | prompts ahead / behind / tied (passes summed over repeats) | {p['prompts']} | "
                   f"{p['wins']} | {p['losses']} | ties {p['ties']} | sign test {p['sign_p']:.4f} |")
    out += ["", "## Every run", "", "| Prompt | Repeat | " + " | ".join(f"`{a['name']}`" for a in arms) + " |",
            "|---|---|" + "---|" * len(arms)]
    for key in sorted(set().union(*(a["results"] for a in arms))):
        cells = []
        for arm in arms:
            r = arm["results"].get(key)
            cells.append("missing" if r is None else
                         f"{r['verdict']}, {r['grade']}, {r['level'] or '-'}" + (f"; {_tool_cell(r)}" if r["tools"] else ""))
        out.append(f"| {key[0]} | {key[1]} | " + " | ".join(cells) + " |")
    out += ["", "Tool cells: `rp` run_python, `ra` read_attempt, `s:<operation>` a submission tool; counts are calls.", ""]
    if traces:
        out += ["## Traces", ""] + [line for spec in traces for line in trace(arms, spec)]
    out += ["## Data problems", ""] + ([f"- {p}" for p in problems] or ["None."]) + [
        "", "## Correlation and causation", "",
        "The tables say which runs used which tools and how they ended. They do not say that a tool caused an "
        "outcome: the arms differ by more than the tool flag, repeats share prompts, and providers serve calls as "
        "they choose. A trace above can show a mechanism in one run (for example a rejection followed by a fixed "
        "submission that the host accepted); that explains that run, not an effect size.", ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("runs", nargs="+", help="run folders; the first is the reference arm")
    parser.add_argument("--md", type=Path, help="write the report here (default: standard output)")
    parser.add_argument("--trace", action="append", default=[], metavar="ID:REPEAT",
                        help="add the tool-call trace of one run in every arm; repeatable")
    parser.add_argument("--allow-missing", action="store_true",
                        help="exit 0 even when records are missing or malformed (they are still listed)")
    args = parser.parse_args(argv)
    problems: list[str] = []
    arms = [load_run(_resolve(name), problems) for name in args.runs]
    text = report(arms, args.trace, problems)
    if args.md:
        args.md.write_text(text + "\n", encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)
    if problems:
        print(f"{len(problems)} data problem(s); see the report", file=sys.stderr)
    return 1 if problems and not args.allow_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
