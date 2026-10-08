#!/usr/bin/env python3
"""Five-route benchmark report: Control + Arms 1-4, from finished catalogue runs. Read-only.

Every figure comes from the runs' own artifacts (result.json, RUN_META.json, KEY_USAGE.json); a pass is
`run_catalogue.outcome_class(r) == "PASS"` (the expected stage and a grader PASS). Ungraded and pending
prompts are never passes.

    py -3.11 experiments/five_arm_report.py --runs-dir catalogue-runs --commit <sha> --md report.md --json report.json
    py -3.11 experiments/five_arm_report.py --arm control=catalogue-runs/run-... --arm unconfirmed=...   (explicit runs)
"""
from __future__ import annotations

import argparse
import json
import math
import os
import statistics
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(os.environ.get("PDLT_TEST_ROOT") or Path(__file__).resolve().parent.parent)
sys.path.insert(0, str(ROOT))

import run_catalogue  # noqa: E402  (one definition of a pass, shared with the scoreboards)

# name, short label, the RUN_META.run_settings that identify the run
ARMS = (
    ("control", "Control", {"route": "control", "draft_execute": False}),
    ("unconfirmed", "Arm 1", {"route": "unconfirmed", "draft_execute": False}),
    ("confirmed", "Arm 2", {"route": "confirmed", "draft_execute": False}),
    ("confirmed-draft-execute", "Arm 3", {"route": "confirmed", "draft_execute": True}),
    ("unconfirmed-draft-execute", "Arm 4", {"route": "unconfirmed", "draft_execute": True}),
)
LABEL = {name: label for name, label, _ in ARMS}
TITLE = {
    "control": "Control: direct model",
    "unconfirmed": "Arm 1: Unconfirmed",
    "confirmed": "Arm 2: Confirmed",
    "confirmed-draft-execute": "Arm 3: Confirmed + DRAFT-EXECUTE",
    "unconfirmed-draft-execute": "Arm 4: Unconfirmed + DRAFT-EXECUTE",
}
CATEGORY_TITLES = {
    "combinatorial_search": "Combinatorial Search", "data_structures": "Data Structures",
    "systems_programming": "Systems Programming", "parsers_and_compilers": "Parsers & Compilers",
    "algorithm_design": "Algorithm Design", "debugging_and_repair": "Debugging & Repair",
    "refactoring_and_design": "Refactoring & Design", "specification_extraction": "Specification Extraction",
    "adversarial_and_injection": "Adversarial & Injection", "multi_turn_and_revision": "Multi-Turn & Revision",
    "cross_domain_composition": "Cross-Domain Composition", "domain_knowledge": "Domain Knowledge",
    "negative_and_impossible": "Negative & Impossible", "formal_verification": "Formal Verification",
    "performance_and_scale": "Performance & Scale", "logic_and_reasoning": "Logic & Reasoning",
}
# Contrasts that answer a question: the two route effects, the two DRAFT-EXECUTE effects, each arm vs control.
PAIRS = (
    ("unconfirmed", "control"), ("confirmed", "control"),
    ("confirmed-draft-execute", "control"), ("unconfirmed-draft-execute", "control"),
    ("confirmed", "unconfirmed"), ("confirmed-draft-execute", "unconfirmed-draft-execute"),
    ("unconfirmed-draft-execute", "unconfirmed"), ("confirmed-draft-execute", "confirmed"),
)


# ---------------------------------------------------------------- loading
def load_run(run_dir: Path) -> dict:
    meta = json.loads((run_dir / "RUN_META.json").read_text(encoding="utf-8"))
    files = sorted(run_dir.glob("results/*/result.json"))
    results = [json.loads(p.read_text(encoding="utf-8")) for p in files]
    usage_file = run_dir / "KEY_USAGE.json"
    usage = json.loads(usage_file.read_text(encoding="utf-8")) if usage_file.exists() else None
    return {"dir": run_dir, "meta": meta, "results": results, "usage": usage, "result_dirs": [p.parent for p in files]}


def discover(runs_dir: Path, commit: str | None, timeout: int, total: int) -> dict[str, Path]:
    """The newest finished run for each arm that matches the sweep's fixed settings."""
    found: dict[str, Path] = {}
    for run_dir in sorted(runs_dir.glob("run-*"), reverse=True):
        meta_file = run_dir / "RUN_META.json"
        if not meta_file.exists() or not (run_dir / "SCOREBOARD.json").exists():
            continue
        meta = json.loads(meta_file.read_text(encoding="utf-8"))
        settings = meta.get("run_settings", {})
        if meta.get("total_prompts") != total or meta.get("timeout_per_prompt") != timeout:
            continue
        if meta.get("model") != "openai/gpt-oss-120b" or meta.get("reasoning_effort") != "low":
            continue
        if commit and not (meta.get("code", {}).get("commit") or "").startswith(commit):
            continue
        for name, _, want in ARMS:
            if name not in found and all(settings.get(k) == v for k, v in want.items()):
                found[name] = run_dir
    return found


# ---------------------------------------------------------------- statistics
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z * z / n
    centre = p + z * z / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((centre - margin) / denom, (centre + margin) / denom)


def exact_mcnemar(b: int, c: int) -> float:
    """Two-sided exact p for b vs c discordant pairs (binomial, p = 0.5)."""
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, i) for i in range(min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)] if ordered else 0.0


# ---------------------------------------------------------------- metrics
def token_totals(run: dict) -> dict:
    """Input, cached and output tokens of every model call of a run, from the run's own observation records (and the
    control's event). The counts stored in result.json before LEDGER L82 covered only the first call of each record."""
    totals = {"input": 0, "cached": 0, "output": 0}
    for result_dir in run.get("result_dirs", []):
        usage = run_catalogue.token_usage(result_dir)
        totals["input"] += sum(usage["input_tokens"].values())
        totals["cached"] += sum(usage.get("cached_tokens", {}).values())
        totals["output"] += sum(usage["output_tokens"].values())
    return totals


def gate_activity(run_dir: Path | None) -> dict:
    """What the System 1 gates decided in a run, from its own events: the verdict of every prompt-fidelity and
    plan-advancement decision (no verdict means System 1 was unavailable), and the retries they caused. Also how
    the computation question (which gates the DRAFT-EXECUTE brief) was answered."""
    fidelity: Counter = Counter()
    advancement: Counter = Counter()
    kinds: Counter = Counter()
    computation: Counter = Counter()
    if run_dir is None:
        return {}
    for events in Path(run_dir).rglob("events.jsonl"):
        for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
            if '"COMPUTATION_CLASSIFIED"' in line:
                try:
                    payload = json.loads(line).get("payload") or {}
                except ValueError:
                    continue
                computation["yes" if payload.get("computational") else (payload.get("fallback") or "no")] += 1
                continue
            if '"PROMPT_FIDELITY' not in line and '"PLAN_ADVANCEMENT' not in line:
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            kind, payload = event.get("kind"), event.get("payload") or {}
            if kind == "PROMPT_FIDELITY":
                fidelity[payload.get("verdict") or "NO_DECISION"] += 1
            elif kind == "PLAN_ADVANCEMENT":
                advancement[payload.get("verdict") or "NO_DECISION"] += 1
            else:
                kinds[kind] += 1
    return {"fidelity": dict(fidelity), "advancement": dict(advancement), "events": dict(kinds),
            "computation": dict(computation)}


def arm_metrics(run: dict, *, light: bool = False) -> dict:
    """Everything the report says about one run. ``light`` skips what needs the run's event files and
    observation records (gates, tokens): enough for the pass rates of a regraded copy."""
    results = run["results"]
    outcome = {r["id"]: run_catalogue.outcome_class(r) for r in results}
    verified = [r for r in results if r.get("ground_truth_status") == "verified"]
    v_pass = sum(outcome[r["id"]] == "PASS" for r in verified)
    v_fail = sum(outcome[r["id"]] == "FAIL" for r in verified)
    v_pending = sum(outcome[r["id"]] == "PENDING" for r in verified)
    v_stage_miss = sum(not run_catalogue.stage_pass(r) for r in verified)
    v_false_pos = sum(
        1 for r in verified if run_catalogue.stage_pass(r) and run_catalogue.gt_grade(r) == "FAIL")
    decided = v_pass + v_fail
    lo, hi = wilson(v_pass, decided)
    seconds = [float(r.get("elapsed_seconds") or 0) for r in results]
    calls = [int((r.get("model_calls") or {}).get("total") or 0) for r in results]
    v_seconds = [float(r.get("elapsed_seconds") or 0) for r in verified]
    v_calls = [int((r.get("model_calls") or {}).get("total") or 0) for r in verified]
    counts = run_catalogue.outcome_counts(results)
    verdicts = Counter(r.get("verdict") for r in results)
    n = len(results)
    cost = (run["usage"] or {}).get("cost_usd")
    return {
        "run_id": run["meta"]["run_id"],
        "commit": (run["meta"].get("code") or {}).get("commit"),
        "dirty": (run["meta"].get("code") or {}).get("dirty"),
        "settings": run["meta"].get("run_settings"),
        "prompts": n,
        "verified": {
            "n": len(verified), "pass": v_pass, "fail": v_fail, "pending": v_pending,
            "stage_miss": v_stage_miss, "false_positive": v_false_pos,
            "decided": decided, "decided_rate": v_pass / decided if decided else 0.0,
            "ci": [lo, hi], "rate_of_all": v_pass / len(verified) if verified else 0.0,
            "seconds_per_pass": sum(v_seconds) / v_pass if v_pass else None,
            "calls_per_pass": sum(v_calls) / v_pass if v_pass else None,
        },
        "catalogue": {
            "pass": counts["pass"], "fail": counts["fail"], "pending": counts["pending"],
            "ungraded": counts["ungraded"], "held": counts["held"],
            "stage": sum(run_catalogue.stage_pass(r) for r in results),
        },
        "latency": {
            "total_s": sum(seconds), "mean_s": statistics.mean(seconds) if seconds else 0.0,
            "median_s": statistics.median(seconds) if seconds else 0.0, "p90_s": percentile(seconds, 0.9),
            "max_s": max(seconds) if seconds else 0.0,
        },
        "calls": {"total": sum(calls), "per_prompt": sum(calls) / n if n else 0.0},
        "verdicts": dict(verdicts),
        "timeouts": verdicts.get("TIMEOUT", 0),
        "faults": sum(v for k, v in verdicts.items() if str(k).startswith("HARNESS")),
        "cost_usd": cost,
        "tokens": {} if light else token_totals(run),
        "gates": {} if light else gate_activity(run.get("dir")),
        "outcome": outcome,
    }


def regrade_run(run_dir: Path, cache: dict) -> dict[str, dict]:
    """Every result of a run graded again with today's graders, read-only (experiments/baseline.py):
    {prompt id: {old, new, reason}}. ``cache`` (name of the run folder -> that mapping) saves a slow rerun."""
    key = Path(run_dir).name
    if key not in cache:
        from experiments import baseline

        cache[key] = {row["id"]: {"old": row["old_grade"], "new": row["new_grade"], "reason": row["reason"]}
                      for row in baseline.regrade(Path(run_dir))["rows"]}
    return cache[key]


def with_grades(run: dict, grades: dict[str, dict]) -> dict:
    """The run as it reads with the regraded verdicts in place of the recorded ones."""
    results = []
    for r in run["results"]:
        g = grades.get(r["id"])
        if g is not None and g["new"] != g["old"]:
            r = {**r, "ground_truth_grade": {**(r.get("ground_truth_grade") or {}), "grade": g["new"],
                                             "reason": g["reason"]}}
        results.append(r)
    return {**run, "results": results}


def grade_changes(runs: dict[str, dict], grades: dict[str, dict[str, dict]]) -> list[dict]:
    """The verified prompts whose grade differs between the recorded run and the regrade."""
    rows = []
    for name, run in runs.items():
        for r in run["results"]:
            g = grades[name].get(r["id"])
            if r.get("ground_truth_status") == "verified" and g is not None and g["new"] != g["old"]:
                rows.append({"route": name, "id": r["id"], "old": g["old"], "new": g["new"], "reason": g["reason"]})
    return sorted(rows, key=lambda c: (c["id"], c["route"]))


def by_category(runs: dict[str, dict], metrics: dict[str, dict]) -> list[dict]:
    categories: dict[str, dict] = {}
    for name, run in runs.items():
        for r in run["results"]:
            cell = categories.setdefault(r["category"], {"n": 0, "verified": 0, "per_arm": {}})
            arm = cell["per_arm"].setdefault(name, {"v_pass": 0, "stage": 0, "total": 0, "v_n": 0})
            arm["total"] += 1
            arm["stage"] += run_catalogue.stage_pass(r)
            if r.get("ground_truth_status") == "verified":
                arm["v_n"] += 1
                arm["v_pass"] += metrics[name]["outcome"][r["id"]] == "PASS"
    order = list(CATEGORY_TITLES)
    rows = []
    for category in sorted(categories, key=lambda c: order.index(c) if c in order else 99):
        cell = categories[category]
        any_arm = max(cell["per_arm"].values(), key=lambda a: a["total"])
        rows.append({"category": category, "verified": any_arm["v_n"], "total": any_arm["total"],
                     "per_arm": cell["per_arm"]})
    return rows


def paired(runs: dict[str, dict], metrics: dict[str, dict]) -> list[dict]:
    out = []
    for a, b in PAIRS:
        if a not in runs or b not in runs:
            continue
        shared = sorted(
            {r["id"] for r in runs[a]["results"] if r.get("ground_truth_status") == "verified"}
            & {r["id"] for r in runs[b]["results"] if r.get("ground_truth_status") == "verified"})
        only_a = sum(metrics[a]["outcome"][i] == "PASS" and metrics[b]["outcome"][i] != "PASS" for i in shared)
        only_b = sum(metrics[b]["outcome"][i] == "PASS" and metrics[a]["outcome"][i] != "PASS" for i in shared)
        out.append({"a": a, "b": b, "n": len(shared), "only_a": only_a, "only_b": only_b,
                    "p": exact_mcnemar(only_a, only_b)})
    return out


def brief_split(runs: dict[str, dict], metrics: dict[str, dict]) -> list[dict]:
    """Where the DRAFT-EXECUTE brief actually ran, and how much a pipeline disagrees with itself elsewhere.

    The brief runs only when a task needs verified execution. On every other prompt a DRAFT-EXECUTE arm is
    the same pipeline as its plain counterpart, so their disagreement there is run-to-run noise."""
    rows = []
    for plain, brief in (("unconfirmed", "unconfirmed-draft-execute"), ("confirmed", "confirmed-draft-execute")):
        if plain not in runs or brief not in runs:
            continue
        ran = {r["id"] for r in runs[brief]["results"]
               if ((r.get("model_calls") or {}).get("by_operation") or {}).get("DRAFT_EXECUTE")}
        verified = ({r["id"] for r in runs[plain]["results"] if r.get("ground_truth_status") == "verified"}
                    & {r["id"] for r in runs[brief]["results"] if r.get("ground_truth_status") == "verified"})

        def tally(ids: set[str], plain: str = plain, brief: str = brief) -> dict:
            ordered = sorted(ids)
            only_plain = sum(metrics[plain]["outcome"][i] == "PASS" and metrics[brief]["outcome"][i] != "PASS"
                             for i in ordered)
            only_brief = sum(metrics[brief]["outcome"][i] == "PASS" and metrics[plain]["outcome"][i] != "PASS"
                             for i in ordered)
            return {"n": len(ordered),
                    "plain": sum(metrics[plain]["outcome"][i] == "PASS" for i in ordered),
                    "brief": sum(metrics[brief]["outcome"][i] == "PASS" for i in ordered),
                    "only_plain": only_plain, "only_brief": only_brief,
                    "p": exact_mcnemar(only_plain, only_brief)}

        rows.append({"plain": plain, "brief": brief, "ran_on": sorted(ran),
                     "with_brief": tally(verified & ran), "without_brief": tally(verified - ran)})
    return rows


def pareto(metrics: dict[str, dict]) -> dict[str, list[str]]:
    """For each route, the routes that dominate it: no worse on decided pass rate, seconds per prompt and
    calls per prompt, and strictly better on at least one. Point estimates only; see the paired tests."""
    point = {n: (m["verified"]["decided_rate"], m["latency"]["mean_s"], m["calls"]["per_prompt"])
             for n, m in metrics.items()}
    dominated_by: dict[str, list[str]] = {}
    for a, (acc_a, sec_a, call_a) in point.items():
        dominated_by[a] = [
            b for b, (acc_b, sec_b, call_b) in point.items()
            if b != a and acc_b >= acc_a and sec_b <= sec_a and call_b <= call_a
            and (acc_b > acc_a or sec_b < sec_a or call_b < call_a)]
    return dominated_by


# ---------------------------------------------------------------- rendering
def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def money(x: float | None) -> str:
    return "n/a" if x is None else f"${x:.2f}"


def render(runs: dict[str, dict], metrics: dict[str, dict], categories: list[dict], pairs: list[dict],
           dominated: dict[str, list[str]], splits: list[dict], recorded: dict[str, dict] | None = None,
           changes: list[dict] | None = None) -> str:
    names = [n for n, _, _ in ARMS if n in metrics]
    out: list[str] = []
    w = out.append

    w("### Provenance\n")
    w("| Route | Run | Commit | Tier D1 | DRAFT-EXECUTE |")
    w("| :--- | :--- | :--- | :---: | :---: |")
    for n in names:
        m = metrics[n]
        s = m["settings"] or {}
        d1 = "n/a" if s.get("route") == "control" else ("on" if s.get("tier_d1") else "off")
        w(f"| {TITLE[n]} | `{m['run_id']}` | `{(m['commit'] or '?')[:8]}`{' (dirty)' if m['dirty'] else ''} | "
          f"{d1} | {'yes' if s.get('draft_execute') else 'no'} |")

    w("\n### Verified ground truth: decided pass rate (57 prompts)\n")
    w("| Route | Pass | Fail | Pending | Decided pass rate (95% CI) | Pass of all 57 | Of the fails: false positives / missed stage |")
    w("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    for n in names:
        v = metrics[n]["verified"]
        w(f"| {TITLE[n]} | {v['pass']} | {v['fail']} | {v['pending']} | "
          f"**{pct(v['decided_rate'])}** ({pct(v['ci'][0])}-{pct(v['ci'][1])}) | {pct(v['rate_of_all'])} | "
          f"{v['false_positive']} / {v['stage_miss']} |")

    if recorded is not None:
        w("\n### The grades as recorded, and after the grader fixes (LEDGER L84)\n")
        w("Every table in this report scores all five routes with today's graders, so that no route is scored by an "
          "older rule than another. This table sets that beside what the graders said when each run was scored. "
          "The graders changed in four ways, none of which changes what a correct answer must do: the loader registers "
          "the deliverable as a module (a `@dataclass` under `from __future__ import annotations` failed to load "
          "before); the tests that scan an object's attributes read `__slots__` classes; a coloring written one node "
          "per table row is read; and the fence rule no longer loses a block after an unclosed one or cuts a block at "
          "a docstring that mentions a fence.\n")
        w("| Route | Decided pass rate as recorded | With today's graders | Verified grades that changed |")
        w("| :--- | :---: | :---: | :---: |")
        for n in names:
            r, v = recorded[n]["verified"], metrics[n]["verified"]
            moved = sum(1 for c in (changes or []) if c["route"] == n)
            w(f"| {TITLE[n]} | {r['pass']} / {r['decided']} = {pct(r['decided_rate'])} | "
              f"{v['pass']} / {v['decided']} = {pct(v['decided_rate'])} | {moved} |")
        if changes:
            w("\n| Route | Prompt | Recorded | Today | What the grader says now |")
            w("| :--- | :---: | :---: | :---: | :--- |")
            for c in changes:
                reason = " ".join(str(c["reason"]).split())[:150].replace("|", "/")
                w(f"| {LABEL[c['route']]} | {c['id']} | {c['old']} | {c['new']} | {reason} |")

    w("\n### Cost and latency (all 112 prompts)\n")
    w("Tokens are counted from every model call in the run's own records (millions: input / of which cached / output); "
      "key spend is the OpenRouter counter's change over the run, System 1 included.\n")
    w("| Route | Model calls | Calls / prompt | Mean s / prompt | Median | p90 | Total time | Tokens in / cached / out (M) | Timeouts | Harness faults | Key spend |")
    w("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for n in names:
        m = metrics[n]
        lat, tok = m["latency"], m.get("tokens") or {}
        tokens = (f"{tok['input'] / 1e6:.2f} / {tok['cached'] / 1e6:.2f} / {tok['output'] / 1e6:.2f}" if tok else "n/a")
        w(f"| {TITLE[n]} | {m['calls']['total']} | {m['calls']['per_prompt']:.2f} | {lat['mean_s']:.1f} | "
          f"{lat['median_s']:.1f} | {lat['p90_s']:.1f} | {lat['total_s'] / 60:.0f} min | {tokens} | {m['timeouts']} | "
          f"{m['faults']} | {money(m['cost_usd'])} |")

    w("\n### Full catalogue outcomes (112 prompts)\n")
    w("| Route | Pass | Fail | Pending | Ungraded | Held | Reached expected stage |")
    w("| :--- | :---: | :---: | :---: | :---: | :---: | :---: |")
    for n in names:
        c = metrics[n]["catalogue"]
        w(f"| {TITLE[n]} | {c['pass']} | {c['fail']} | {c['pending']} | {c['ungraded']} | {c['held']} | "
          f"{c['stage']} / {metrics[n]['prompts']} |")

    w("\n### By category\n")
    w("Verified categories show ground-truth passes out of the category's verified prompts; the rest show "
      "prompts that reached the expected stage (no grader judged the deliverable).\n")
    w("| # | Category | Basis | " + " | ".join(LABEL[n] for n in names) + " |")
    w("| :---: | :--- | :--- | " + " | ".join(":---:" for _ in names) + " |")
    for idx, row in enumerate(categories, 1):
        cells = []
        for n in names:
            arm = row["per_arm"].get(n)
            if arm is None:
                cells.append("-")
            elif row["verified"]:
                cells.append(f"{arm['v_pass']} / {arm['v_n']}")
            else:
                cells.append(f"{arm['stage']} / {arm['total']} (stage)")
        basis = f"{row['verified']} verified" + (f", {row['total'] - row['verified']} ungraded" if row['verified'] != row['total'] else "")
        w(f"| {idx:02d} | {CATEGORY_TITLES.get(row['category'], row['category'])} | {basis} | " + " | ".join(cells) + " |")

    w("\n### Paired comparisons on the verified prompts\n")
    w("Passes that one route has and the other lacks, over the prompts both ran. Exact two-sided McNemar test; "
      "one run per prompt, so a p-value above 0.05 means the difference is not distinguishable from run-to-run noise.\n")
    w("| Route A | Route B | A only | B only | p |")
    w("| :--- | :--- | :---: | :---: | :---: |")
    for p in pairs:
        w(f"| {LABEL[p['a']]} | {LABEL[p['b']]} | {p['only_a']} | {p['only_b']} | {p['p']:.3f} |")

    if splits:
        w("\n### Where DRAFT-EXECUTE ran\n")
        w("The brief runs when a task needs verified execution, or when System 1 judges its deliverable to be an "
          "algorithm or a calculation (LEDGER L85). On every other prompt a DRAFT-EXECUTE arm is the same pipeline as "
          "its plain counterpart, so how often the two disagree there is run-to-run noise.\n")
        w("| Plain route | DRAFT-EXECUTE route | Prompts with the brief | Verified passes on those (plain / brief) | "
          "Other verified prompts | Passes on those (plain / brief) | Flipped (plain only / brief only) | p |")
        w("| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")
        for row in splits:
            on, off = row["with_brief"], row["without_brief"]
            ran = len(row["ran_on"])
            listed = f" ({', '.join(row['ran_on'])})" if ran <= 12 else ""
            w(f"| {LABEL[row['plain']]} | {LABEL[row['brief']]} | {ran}{listed} | "
              f"{on['plain']} / {on['brief']} of {on['n']} | {off['n']} | {off['plain']} / {off['brief']} | "
              f"{off['only_plain']} / {off['only_brief']} | {off['p']:.3f} |")
        for row in splits:
            asked = metrics[row["brief"]]["gates"].get("computation")
            if asked:
                w(f"\n{TITLE[row['brief']]}: the computation question was asked on {sum(asked.values())} prompts "
                  f"(verified-execution tasks skip it) and answered "
                  + ", ".join(f"{k} {v}" for k, v in sorted(asked.items(), key=lambda kv: -kv[1])) + ".")

    w("\n### Pareto frontier\n")
    w("A route is dominated when another is no worse on decided pass rate, mean seconds per prompt and calls per "
      "prompt, and strictly better on one (point estimates). A DRAFT-EXECUTE arm runs the same pipeline as its plain "
      "counterpart except where the brief ran (previous table), so a gap on the other prompts is noise.\n")
    w("| Route | Decided pass rate | Mean s / prompt | Calls / prompt | Seconds per verified pass | Calls per verified pass | Dominated by |")
    w("| :--- | :---: | :---: | :---: | :---: | :---: | :--- |")
    for n in names:
        m = metrics[n]
        v = m["verified"]
        by = ", ".join(LABEL[b] for b in dominated[n]) or "**none (frontier)**"
        w(f"| {TITLE[n]} | {pct(v['decided_rate'])} | {m['latency']['mean_s']:.1f} | {m['calls']['per_prompt']:.2f} | "
          f"{(v['seconds_per_pass'] or 0):.1f} | {(v['calls_per_pass'] or 0):.1f} | {by} |")

    w("\n```mermaid")
    w("quadrantChart")
    w("    title Decided pass rate vs speed on the 57 verified prompts, one run each")
    w('    x-axis "Slower (more seconds per prompt)" --> "Faster (fewer seconds per prompt)"')
    w('    y-axis "Lower decided pass rate" --> "Higher decided pass rate"')
    w('    quadrant-1 "Fast and accurate"')
    w('    quadrant-2 "Slow but accurate"')
    w('    quadrant-3 "Slow and less accurate"')
    w('    quadrant-4 "Fast but less accurate"')
    slowest = max(metrics[n]["latency"]["mean_s"] for n in names) or 1.0
    for n in names:
        x = 0.05 + 0.9 * (1 - metrics[n]["latency"]["mean_s"] / slowest)
        y = min(0.97, max(0.03, metrics[n]["verified"]["decided_rate"]))
        w(f'    "{TITLE[n].replace(": ", " - ")}": [{x:.2f}, {y:.2f}]')  # no colon inside a point label
    w("```")

    gated = [n for n in names if metrics[n]["gates"].get("fidelity") or metrics[n]["gates"].get("advancement")]
    if gated:
        w("\n### System 1 gate activity\n")
        w("Decisions of the two classifier gates on the confirmed routes. *Uncertain* means the classifier was below its "
          "confidence floor and the draft passed unchanged; *flagged* means a confident violation, which asks the model "
          "for one redraft.\n")
        w("| Route | Prompt fidelity: decisions | faithful | uncertain | flagged | Plan advancement: decisions | advances / prompt states method | uncertain | restates | Redrafts asked (prompt / plan) |")
        w("| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for n in gated:
            g = metrics[n]["gates"]
            f, a, ev = g.get("fidelity", {}), g.get("advancement", {}), g.get("events", {})
            f_total, a_total = sum(f.values()), sum(a.values())
            f_ok, f_unc = f.get("FAITHFUL", 0), f.get("UNCERTAIN", 0) + f.get("NO_DECISION", 0)
            a_ok, a_unc = a.get("ADVANCES", 0) + a.get("PROMPT_STATES_METHOD", 0), a.get("UNCERTAIN", 0) + a.get("NO_DECISION", 0)
            w(f"| {TITLE[n]} | {f_total} | {f_ok} | {f_unc} | {f_total - f_ok - f_unc} | {a_total} | {a_ok} | {a_unc} | "
              f"{a_total - a_ok - a_unc} | {ev.get('PROMPT_FIDELITY_RETRY', 0)} / {ev.get('PLAN_ADVANCEMENT_RETRY', 0)} |")
    w("\n### Every verified prompt\n")
    w(appendix(runs, metrics, names))
    return "\n".join(out) + "\n"


def appendix(runs: dict[str, dict], metrics: dict[str, dict], names: list[str]) -> str:
    """One row per verified prompt: pass, FAIL (the answer was wrong), miss (the run did not reach the expected
    stage) or pending (a grader asked for a human check), plus how many routes passed each prompt."""
    by_id = {n: {r["id"]: r for r in runs[n]["results"]} for n in names}
    ids = sorted({pid for n in names for pid, r in by_id[n].items() if r.get("ground_truth_status") == "verified"})
    lines = ["| Prompt | " + " | ".join(LABEL[n] for n in names) + " | Routes passing |",
             "| :--- | " + " | ".join(":---:" for _ in names) + " | :---: |"]
    histogram: Counter = Counter()
    for pid in ids:
        cells, passing = [], 0
        for n in names:
            result = by_id[n].get(pid)
            outcome = metrics[n]["outcome"].get(pid)
            if result is None:
                cells.append("-")
            elif outcome == "PASS":
                cells.append("pass")
                passing += 1
            elif outcome == "PENDING":
                cells.append("pending")
            elif not run_catalogue.stage_pass(result):
                cells.append("miss")
            else:
                cells.append("FAIL")
        histogram[passing] += 1
        lines.append(f"| {pid} | " + " | ".join(cells) + f" | {passing} / {len(names)} |")
    spread = ", ".join(
        f"{histogram[k]} prompt{'s' if histogram[k] != 1 else ''} passed on {k} route{'s' if k != 1 else ''}"
        for k in range(len(names), -1, -1) if histogram[k])
    return f"By prompt: {spread}.\n\n" + "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--runs-dir", type=Path, default=ROOT / "catalogue-runs")
    parser.add_argument("--commit", default=None, help="only runs of this commit (prefix)")
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--total", type=int, default=112, help="prompts a run must have")
    parser.add_argument("--arm", action="append", default=[], metavar="NAME=RUN_DIR")
    parser.add_argument("--md", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--regrade", action="store_true",
                        help="also grade every run again with today's graders (read-only, slow) and show it next to "
                             "the recorded numbers")
    parser.add_argument("--regrade-cache", type=Path, default=None,
                        help="JSON file of regrades: read first, extended, written back")
    args = parser.parse_args()

    chosen = discover(args.runs_dir, args.commit, args.timeout, args.total)
    for spec in args.arm:
        name, _, path = spec.partition("=")
        chosen[name] = Path(path)
    if not chosen:
        print("no matching runs found", file=sys.stderr)
        return 1
    runs = {name: load_run(path) for name, _, _ in ARMS if (path := chosen.get(name))}
    recorded = changes = None
    if args.regrade:  # every table below is then computed on the regraded runs; the recorded numbers sit beside them
        cache = (json.loads(args.regrade_cache.read_text(encoding="utf-8"))
                 if args.regrade_cache and args.regrade_cache.exists() else {})
        graded = {name: regrade_run(run["dir"], cache) for name, run in runs.items()}
        if args.regrade_cache:
            args.regrade_cache.write_text(json.dumps(cache, indent=1), encoding="utf-8")
        recorded = {name: arm_metrics(run, light=True) for name, run in runs.items()}
        changes = grade_changes(runs, graded)
        runs = {name: with_grades(run, graded[name]) for name, run in runs.items()}
    metrics = {name: arm_metrics(run) for name, run in runs.items()}
    categories = by_category(runs, metrics)
    pairs = paired(runs, metrics)
    dominated = pareto(metrics)
    splits = brief_split(runs, metrics)

    markdown = render(runs, metrics, categories, pairs, dominated, splits, recorded, changes)
    if args.md:
        args.md.write_text(markdown, encoding="utf-8")
    else:
        sys.stdout.buffer.write(markdown.encode("utf-8"))
    if args.json:
        slim = {n: {k: v for k, v in m.items() if k != "outcome"} for n, m in metrics.items()}
        payload = {"arms": slim, "pairs": pairs, "dominated_by": dominated, "brief_split": splits}
        if recorded is not None:
            payload["recorded_grades"] = {n: m["verified"] for n, m in recorded.items()}
            payload["grade_changes"] = changes
        args.json.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
