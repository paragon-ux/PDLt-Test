"""The report of an L145 study, from its ledger and run folders only, so it can be regenerated and checked.

    python experiments/study_report.py CONFIG [--md OUT] [--json OUT] [--no-lookup] [--trace ARM:ID:REPEAT ...]

**Inputs.** The study's ``ledger.jsonl`` (``experiments/matched_study.py``): the finished units of each block's last
attempt. Each unit's ``result.json`` and session records under its run folder.

**Grades.** Every run is graded again here with this checkout's graders (``graders.grade``; the held-out entries from
their own manifest), so all arms share one grader version; a timed-out run keeps its recorded grade, as the runner
does. Where the new grade differs from the one recorded at run time, the change is listed.

**Outcomes per run.**
- ``pass``: the ground-truth grade is PASS. MANUAL, N/A, ERROR, harness errors and timeouts are not passes.
- ``sfp`` (a silent false positive): the run closed CLOSED_SUCCESS and its grade is FAIL.
- ``stage_pass``: the catalogue's own pass (``run_catalogue.is_prompt_pass``: the expected stage and a PASS).
- the verification level (``provenance.json``), the verdict, the outcome class, the in-call tool calls
  (``AGENT_TOOL_CALL`` events), the wall time, and the generations (``call-trace.jsonl`` ``reply.response_ids``, else
  ``response_id``; Control's ``MODEL_OUTPUT_RECORDED`` event).

**Generations** are looked up at OpenRouter (``/api/v1/generation``; cached in the study folder): the serving provider,
model, cost, tokens and latency of each call. A call served by any provider other than the configured one is listed.

**Statistics** (``experiments/study_stats.py``): prompt-clustered contrasts (the mean per-prompt difference, a BCa
interval over prompts, the exact sign-flip p), run-level exact McNemar, Holm over the primary family. A screen (an arm
run once per prompt) is compared with its reference arm descriptively, with no test.

**Data problems** (a unit with no result, an unreadable record, a grader error, a prompt without the scheduled number
of runs, a generation that could not be looked up) are listed, and the exit status is 1 when there are any."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import graders  # noqa: E402
import run_catalogue  # noqa: E402
from experiments import matched_study, study_stats  # noqa: E402
from experiments.schedule import Ledger  # noqa: E402

GENERATION_URL = "https://openrouter.ai/api/v1/generation?id="


# ---------------------------------------------------------------------------- loading

def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def manifest_entries(config: dict) -> dict[str, dict]:
    entries = {e["id"]: e for e in run_catalogue.load_manifest()}
    heldout = config.get("heldout") or {}
    if heldout.get("manifest"):
        entries.update({e["id"]: e for e in run_catalogue.load_manifest(path=ROOT / heldout["manifest"])})
    return entries


def generation_ids(result_dir: Path) -> dict[str, str]:
    """Each generation of the run and its source: ``system1`` (System 1's decisions, its own model by design) or
    ``task`` (the configured model)."""
    ids: dict[str, str] = {}
    for trace in sorted(result_dir.glob("session/**/call-trace.jsonl")):
        for record in _jsonl(trace):
            reply = record.get("reply") or {}
            source = "system1" if str(record.get("operation", "")).startswith("SYSTEM1:") else "task"
            for gid in reply.get("response_ids") or ([reply["response_id"]] if reply.get("response_id") else []):
                ids.setdefault(gid, source)
    for events in sorted(result_dir.glob("**/events.jsonl")):
        for e in _jsonl(events):
            payload = e.get("payload") or {}
            if e.get("kind") == "MODEL_OUTPUT_RECORDED" and payload.get("operation") == "CONTROL_EXECUTE" \
                    and payload.get("response_id"):
                ids.setdefault(payload["response_id"], "task")
    return ids


def load_unit(row: dict, entries: dict[str, dict], problems: list[str]) -> dict | None:
    where = f"{row['arm']} {row['item']} r{row['rep']}"
    if not row.get("result_dir"):
        problems.append(f"{where}: no result ({row.get('outage') or 'no result folder'})")
        return None
    folder = Path(row["result_dir"])
    try:
        result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        problems.append(f"{where}: result.json unreadable ({exc.__class__.__name__})")
        return None
    entry = entries.get(row["item"])
    recorded = run_catalogue.gt_grade(result)
    if entry is None:
        problems.append(f"{where}: {row['item']} is in no manifest")
        grade = recorded
    elif result.get("timed_out"):
        grade = recorded
    else:
        prompts_dir = run_catalogue.PROMPTS_DIR
        graded = graders.grade(entry, folder, prompts_dir)
        grade = graded.get("grade")
        result["ground_truth_grade"] = graded
    if grade == "ERROR":
        problems.append(f"{where}: grader error ({(result.get('ground_truth_grade') or {}).get('reason')})")
    events = [e for f in sorted(folder.glob("session/**/events.jsonl")) for e in _jsonl(f)]
    events.sort(key=lambda e: e.get("at_utc") or "")
    levels = []
    for prov in sorted(folder.glob("session/**/provenance.json")):
        try:
            levels.append(json.loads(prov.read_text(encoding="utf-8"))["verification"]["level"])
        except (OSError, ValueError, KeyError, TypeError):
            problems.append(f"{where}: {prov.name} unreadable")
    verdict = result.get("verdict")
    return {"arm": row["arm"], "id": row["item"], "rep": row["rep"], "verdict": verdict, "grade": grade,
            "recorded_grade": recorded, "pass": int(grade == graders.PASS),
            "sfp": int(verdict == "CLOSED_SUCCESS" and grade == graders.FAIL),
            "decided": grade in (graders.PASS, graders.FAIL),
            "stage_pass": int(run_catalogue.is_prompt_pass(result)), "outcome": run_catalogue.outcome_class(result),
            "level": levels[-1] if levels else None, "elapsed": result.get("elapsed_seconds"),
            "harness_error": (result.get("harness_error") or {}).get("category"),
            "tools": [e["payload"] for e in events if e.get("kind") == "AGENT_TOOL_CALL"],
            "refused": any("REFUS" in str(e.get("kind")) for e in events),
            "timeline": [e for e in events if e.get("kind") == "AGENT_TOOL_CALL"
                         or e.get("kind") in matched_study_trace_kinds()],
            "generations": generation_ids(folder), "kept_after_reruns": bool(row.get("kept_after_reruns")),
            "folder": str(folder)}


def matched_study_trace_kinds() -> set[str]:
    from experiments.tool_attribution import TRACE_EVENTS

    return set(TRACE_EVENTS)


# ---------------------------------------------------------------------------- generations

def lookup_generations(ids: list[str], cache_path: Path, problems: list[str], *, enabled: bool) -> dict[str, dict]:
    import os

    cache: dict[str, dict] = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.is_file() else {}
    missing = [g for g in ids if g not in cache]
    if missing and enabled:
        key = os.environ.get("OPENROUTER_API_KEY", "")
        for gid in missing:
            for attempt in range(3):
                try:
                    req = urllib.request.Request(GENERATION_URL + gid, headers={"Authorization": f"Bearer {key}"})
                    with urllib.request.urlopen(req, timeout=30) as response:
                        data = json.loads(response.read().decode("utf-8")).get("data") or {}
                    cache[gid] = {k: data.get(k) for k in ("provider_name", "model", "total_cost", "tokens_prompt",
                                                           "tokens_completion", "native_tokens_reasoning",
                                                           "latency", "generation_time")}
                    break
                except (urllib.error.URLError, ValueError, TimeoutError):
                    time.sleep(2 * (attempt + 1))
            time.sleep(0.05)
        cache_path.write_text(json.dumps(cache, indent=0), encoding="utf-8")
    absent = [g for g in ids if g not in cache]
    if absent:
        problems.append(f"{len(absent)} generation(s) not looked up" + ("" if enabled else " (--no-lookup)"))
    return cache


# ---------------------------------------------------------------------------- summaries

def _pct(num: float, den: float) -> str:
    return f"{num}/{den} ({100 * num / den:.1f}%)" if den else f"{num}/0"


def arm_summary(runs: list[dict], generations: dict[str, dict]) -> dict:
    gens = [generations[g] for r in runs for g in r["generations"] if g in generations]
    task = [generations[g] for r in runs for g, src in r["generations"].items() if g in generations and src == "task"]
    cost = sum(float(g.get("total_cost") or 0.0) for g in gens)
    passes = sum(r["pass"] for r in runs)
    elapsed = sorted(float(r["elapsed"]) for r in runs if r["elapsed"] is not None)
    tools: dict[str, Counter] = defaultdict(Counter)
    codes: Counter = Counter()
    for r in runs:
        for name in {c["tool"] for c in r["tools"]}:
            tools[name]["runs"] += 1
        for call in r["tools"]:
            tools[call["tool"]]["calls"] += 1
            if call.get("accepted") is True:
                tools[call["tool"]]["accepted"] += 1
            elif call.get("accepted") is False:
                tools[call["tool"]]["rejected"] += 1
                codes.update(e.get("code") for e in (call.get("envelope") or {}).get("errors") or [])
    return {
        "runs": len(runs), "passes": passes, "decided": sum(r["decided"] for r in runs),
        "decided_passes": sum(r["pass"] for r in runs if r["decided"]), "sfp": sum(r["sfp"] for r in runs),
        "stage_passes": sum(r["stage_pass"] for r in runs),
        "published_success": sum(r["verdict"] == "CLOSED_SUCCESS" for r in runs),
        "verdicts": dict(Counter(r["verdict"] for r in runs)), "grades": dict(Counter(r["grade"] for r in runs)),
        "levels": dict(Counter(str(r["level"]) for r in runs)), "outcomes": dict(Counter(r["outcome"] for r in runs)),
        "harness_errors": dict(Counter(r["harness_error"] for r in runs if r["harness_error"])),
        "refused": sum(r["refused"] for r in runs), "kept_after_reruns": sum(r["kept_after_reruns"] for r in runs),
        "generations": len(gens), "system1_generations": len(gens) - len(task),
        "system1_cost_usd": round(sum(float(g.get("total_cost") or 0.0) for g in gens)
                                  - sum(float(g.get("total_cost") or 0.0) for g in task), 4),
        "providers": dict(Counter(str(g.get("provider_name")) for g in task)),
        "models": dict(Counter(str(g.get("model")) for g in task)),
        "cost_usd": round(cost, 4), "cost_per_pass_usd": round(cost / passes, 5) if passes else None,
        "tokens_prompt": sum(int(g.get("tokens_prompt") or 0) for g in gens),
        "tokens_completion": sum(int(g.get("tokens_completion") or 0) for g in gens),
        "tokens_reasoning": sum(int(g.get("native_tokens_reasoning") or 0) for g in gens),
        "seconds_median": round(statistics.median(elapsed), 1) if elapsed else None,
        "seconds_p90": round(elapsed[min(len(elapsed) - 1, int(0.9 * len(elapsed)))], 1) if elapsed else None,
        "tools": {k: dict(v) for k, v in tools.items()}, "rejection_codes": dict(codes),
    }


def by_prompt(runs: list[dict], endpoint: str, prompts: set[str]) -> dict[str, list[int]]:
    out: dict[str, list[int]] = defaultdict(list)
    for r in sorted(runs, key=lambda r: r["rep"]):
        if r["id"] in prompts:
            out[r["id"]].append(r[endpoint])
    return dict(out)


def by_run(runs: list[dict], endpoint: str, prompts: set[str], *, decided_only: bool = False) -> dict:
    return {(r["id"], r["rep"]): r[endpoint] for r in runs if r["id"] in prompts and (r["decided"] or not decided_only)}


def contrast(runs_a: list[dict], runs_b: list[dict], endpoint: str, prompts: set[str], repeats: int,
             seed: int) -> dict:
    a, b = by_prompt(runs_a, endpoint, prompts), by_prompt(runs_b, endpoint, prompts)
    # A prompt short of its runs (a stopped study) is left out of the prompt-level test and named.
    short = sorted(p for p in set(a) | set(b) if len(a.get(p, [])) != repeats or len(b.get(p, [])) != repeats)
    result = study_stats.prompt_contrast({p: v for p, v in a.items() if p not in short},
                                         {p: v for p, v in b.items() if p not in short}, repeats=repeats, seed=seed)
    result["left_out_short"] = short
    result["runs"] = study_stats.run_mcnemar(by_run(runs_a, endpoint, prompts), by_run(runs_b, endpoint, prompts))
    decided_a = by_run(runs_a, endpoint, prompts, decided_only=True)
    decided_b = by_run(runs_b, endpoint, prompts, decided_only=True)
    both = set(decided_a) & set(decided_b)
    result["runs_decided"] = study_stats.run_mcnemar({k: decided_a[k] for k in both}, {k: decided_b[k] for k in both})
    return result


def screen(runs: list[dict], reference: list[dict], endpoint: str, prompts: set[str]) -> dict:
    """An arm run once per prompt against its reference arm: per prompt, the screen's outcome, the reference's
    outcome at the same repeat (the same block), and the reference's mean over its repeats. No test."""
    ref_mean = {p: sum(v) / len(v) for p, v in by_prompt(reference, endpoint, prompts).items()}
    ref_run = {(r["id"], r["rep"]): r[endpoint] for r in reference}
    rows = {}
    for r in runs:
        if r["id"] in prompts:
            rows[r["id"]] = {"screen": r[endpoint], "reference_same_block": ref_run.get((r["id"], r["rep"])),
                             "reference_mean": ref_mean.get(r["id"])}
    return {"prompts": len(rows), "screen_total": sum(v["screen"] for v in rows.values()),
            "reference_same_block_total": sum(v["reference_same_block"] or 0 for v in rows.values()),
            "reference_mean_total": round(sum(v["reference_mean"] or 0 for v in rows.values()), 3),
            "differs_from_same_block": sorted(p for p, v in rows.items() if v["screen"] != v["reference_same_block"]),
            "rows": rows}


def prompt_sets(config: dict, entries: dict[str, dict]) -> dict[str, set[str]]:
    catalogue = set(config["prompts"])
    graded = {p for p in catalogue if entries.get(p, {}).get("ground_truth_status") == "verified"}
    sets = {"all": catalogue, "machine_graded": graded,
            "heldout": set((config.get("heldout") or {}).get("prompts", [])),
            "categories_01_05": {p for p in graded if p[:2] in {"01", "02", "03", "04", "05"}},
            "categories_06_16": {p for p in graded if p[:2] not in {"01", "02", "03", "04", "05"}}}
    panel = set((config.get("analysis") or {}).get("panel_prompts", []))
    if panel:
        sets["machine_graded_without_panel"] = graded - panel
    return sets


# ---------------------------------------------------------------------------- report

def timeline(run: dict) -> list[str]:
    lines = [f"{run['arm']} {run['id']} r{run['rep']}: {run['verdict']}, grade {run['grade']}, level {run['level']}"
             f" ({run['folder']})"]
    for e in run["timeline"]:
        payload = e.get("payload") or {}
        if e.get("kind") == "AGENT_TOOL_CALL":
            codes = [x.get("code") for x in (payload.get("envelope") or {}).get("errors") or []]
            state = {True: "accepted", False: f"rejected {codes}"}.get(payload.get("accepted"), "")
            lines.append(f"  attempt {payload.get('attempt')}: {payload.get('tool')} {state}".rstrip())
        else:
            lines.append(f"  {e.get('kind')} {json.dumps(payload, ensure_ascii=False)[:160]}")
    return lines


def build(config: dict, *, lookup: bool) -> tuple[dict, list[str], dict[str, list[dict]]]:
    problems: list[str] = []
    out = matched_study.out_dir(config)
    ledger = Ledger(out / "ledger.jsonl")
    entries = manifest_entries(config)
    rows = ledger.results()
    if not rows:
        problems.append(f"no finished units in {out / 'ledger.jsonl'}")
    runs: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        unit = load_unit(row, entries, problems)
        if unit is not None:
            runs[row["arm"]].append(unit)
    blocks = matched_study.schedule(config)
    for arm in sorted(config["arms"]):
        want = Counter(b.item_id for b in blocks if arm in b.arms)
        have = Counter(r["id"] for r in runs.get(arm, []))
        for item, n in sorted(want.items()):
            if have.get(item, 0) != n:
                problems.append(f"{arm} {item}: {have.get(item, 0)} runs of {n} scheduled")
    ids = [g for arm_runs in runs.values() for r in arm_runs for g in r["generations"]]
    generations = lookup_generations(ids, out / "generations.json", problems, enabled=lookup)
    analysis = config.get("analysis") or {}
    repeats = config["repeats"]
    seed = int(analysis.get("seed", config["seed"]))
    sets = prompt_sets(config, entries)
    report: dict[str, Any] = {"study": config["study"], "units": len(rows),
                              "arms": {arm: arm_summary(runs.get(arm, []), generations) for arm in sorted(config["arms"])},
                              "grade_changes": sorted(f"{r['arm']} {r['id']} r{r['rep']}: {r['recorded_grade']} -> "
                                                      f"{r['grade']}" for a in runs.values() for r in a
                                                      if r["recorded_grade"] != r["grade"]),
                              "prompt_sets": {k: sorted(v) for k, v in sets.items()}}
    expected_provider = (analysis.get("provider") or "").lower()
    if expected_provider:
        report["other_providers"] = sorted(
            f"{r['arm']} {r['id']} r{r['rep']}: {generations[g].get('provider_name')}"
            for a in runs.values() for r in a for g, src in r["generations"].items()
            if src == "task" and g in generations
            and str(generations[g].get("provider_name") or "").lower() != expected_provider)
    report["contrasts"] = []
    for c in analysis.get("contrasts", []):
        prompts = sets[c.get("prompt_set", "all")]
        for endpoint in c.get("endpoints", ["pass", "sfp"]):
            report["contrasts"].append({**c, "endpoint": endpoint,
                                        **contrast(runs.get(c["a"], []), runs.get(c["b"], []), endpoint, prompts,
                                                   repeats, seed)})
    report["screens"] = []
    for s in analysis.get("screens", []):
        prompts = sets[s.get("prompt_set", "all")]
        for endpoint in s.get("endpoints", ["pass", "sfp"]):
            report["screens"].append({**s, "endpoint": endpoint,
                                      **screen(runs.get(s["arm"], []), runs.get(s["reference"], []), endpoint,
                                               prompts)})
    primary = analysis.get("primary")
    if primary:
        prompts = sets[primary.get("prompt_set", "machine_graded")]
        tests = {name: contrast(runs.get(primary["a"], []), runs.get(primary["b"], []), endpoint, prompts, repeats,
                                seed)
                 for name, endpoint in primary["endpoints"].items()}
        adjusted = study_stats.holm({name: t["p"] for name, t in tests.items()})
        alpha = float(primary.get("alpha", 0.05))
        report["primary"] = {**primary, "tests": {name: {**t, "p_holm": adjusted[name],
                                                         "rejected": adjusted[name] < alpha}
                                                  for name, t in tests.items()}}
    rule = analysis.get("b_rule")
    if rule:
        prompts = sets[rule.get("prompt_set", "all")]
        passes = contrast(runs.get(rule["a"], []), runs.get(rule["b"], []), "pass", prompts, repeats, seed)
        sfp_a = sum(r["sfp"] for r in runs.get(rule["a"], []) if r["id"] in prompts)
        sfp_b = sum(r["sfp"] for r in runs.get(rule["b"], []) if r["id"] in prompts)
        switch = passes["p"] < 0.05 and passes["effect"] > 0 and sfp_a <= sfp_b
        report["b_rule"] = {**rule, "p": passes["p"], "effect": passes["effect"], "sfp_a": sfp_a, "sfp_b": sfp_b,
                            "switch_to_a": switch}
    return report, problems, runs


def _fmt_p(p: float) -> str:
    return f"{p:.2g}" if p < 0.001 else f"{p:.3f}"


def markdown(config: dict, report: dict, problems: list[str], traces: list[str]) -> str:
    lines = [f"# {config['study']}: generated report", "",
             f"Generated by `experiments/study_report.py` from `{matched_study.out_dir(config) / 'ledger.jsonl'}` "
             f"({report['units']} units). Every number below comes from the run folders.", "", "## Arms", "",
             "| Arm | Runs | Passes | Decided passes | Silent false positives | Stage passes | Published success | "
             "Cost | Cost per pass | Median s | p90 s |", "|---|---|---|---|---|---|---|---|---|---|---|"]
    for arm, s in report["arms"].items():
        lines.append(f"| {arm} | {s['runs']} | {_pct(s['passes'], s['runs'])} | {_pct(s['decided_passes'], s['decided'])}"
                     f" | {_pct(s['sfp'], s['decided'])} | {s['stage_passes']} | {s['published_success']} | "
                     f"${s['cost_usd']:.3f} | {s['cost_per_pass_usd'] if s['cost_per_pass_usd'] is not None else '-'} | "
                     f"{s['seconds_median']} | {s['seconds_p90']} |")
    lines += ["", "| Arm | Verdicts | Grades | Levels | Harness errors | Task-model providers (generations) | "
                  "System 1 generations (cost) | Tokens in / out / reasoning |", "|---|---|---|---|---|---|---|---|"]
    for arm, s in report["arms"].items():
        lines.append(f"| {arm} | {s['verdicts']} | {s['grades']} | {s['levels']} | {s['harness_errors'] or '-'} | "
                     f"{s['providers']} | {s['system1_generations']} (${s['system1_cost_usd']:.4f}) | "
                     f"{s['tokens_prompt']} / {s['tokens_completion']} / {s['tokens_reasoning']} |")
    tool_arms = {arm: s for arm, s in report["arms"].items() if s["tools"]}
    if tool_arms:
        lines += ["", "**In-call tool use (correlational).**", "", "| Arm | Tool | Calls | Runs | Accepted | Rejected |",
                  "|---|---|---|---|---|---|"]
        for arm, s in tool_arms.items():
            for tool, c in sorted(s["tools"].items()):
                lines.append(f"| {arm} | {tool} | {c.get('calls', 0)} | {c.get('runs', 0)} | {c.get('accepted', '-')} |"
                             f" {c.get('rejected', '-')} |")
            if s["rejection_codes"]:
                lines.append(f"| {arm} | rejection codes | {s['rejection_codes']} | | | |")
    if report.get("primary"):
        p = report["primary"]
        lines += ["", f"## Primary analysis: {p['a']} against {p['b']} ({p.get('prompt_set', 'machine_graded')})", "",
                  "| Hypothesis | Endpoint | Prompts | Mean a | Mean b | Effect (a - b) | 95% CI | p | Holm p | "
                  "Rejected | Ahead / behind / tied |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        for name, t in p["tests"].items():
            lines.append(f"| {name} | {p['endpoints'][name]} | {t['prompts']} | {t['mean_a']:.3f} | {t['mean_b']:.3f} | "
                         f"{t['effect']:+.3f} | [{t['ci95'][0]:+.3f}, {t['ci95'][1]:+.3f}] | {_fmt_p(t['p'])} | "
                         f"{_fmt_p(t['p_holm'])} | {t['rejected']} | {t['ahead']} / {t['behind']} / {t['tied']} |")
    if report["contrasts"]:
        lines += ["", "## Contrasts", "", "| Contrast | a - b | Endpoint | Prompts | Effect | 95% CI | Sign-flip p | "
                  "Ahead / behind / tied | Runs: only a / only b (McNemar p) | Decided runs: only a / only b (p) |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for c in report["contrasts"]:
            lines.append(f"| {c.get('label', '')} | {c['a']} - {c['b']} | {c['endpoint']} | {c['prompts']} | "
                         f"{c['effect']:+.3f} | [{c['ci95'][0]:+.3f}, {c['ci95'][1]:+.3f}] | {_fmt_p(c['p'])} | "
                         f"{c['ahead']} / {c['behind']} / {c['tied']} | {c['runs']['only_a']} / {c['runs']['only_b']} "
                         f"({_fmt_p(c['runs']['p'])}) | {c['runs_decided']['only_a']} / {c['runs_decided']['only_b']} "
                         f"({_fmt_p(c['runs_decided']['p'])}) |")
    if report["screens"]:
        lines += ["", "## Screens (one run per prompt; no test)", "",
                  "| Screen | Arm | Reference | Endpoint | Prompts | Screen total | Reference, same block | Reference, "
                  "mean over repeats | Prompts differing from the same block |", "|---|---|---|---|---|---|---|---|---|"]
        for s in report["screens"]:
            lines.append(f"| {s.get('label', '')} | {s['arm']} | {s['reference']} | {s['endpoint']} | {s['prompts']} | "
                         f"{s['screen_total']} | {s['reference_same_block_total']} | {s['reference_mean_total']} | "
                         f"{', '.join(s['differs_from_same_block']) or '-'} |")
    if report.get("b_rule"):
        r = report["b_rule"]
        lines += ["", f"## The B rule ({r['a']} against {r['b']})", "",
                  f"Passes: effect {r['effect']:+.3f}, exact sign-flip p {_fmt_p(r['p'])}; silent false positives "
                  f"{r['sfp_a']} against {r['sfp_b']}. Switch B to {r['a']}: **{r['switch_to_a']}**."]
    if report["contrasts"] or report.get("primary"):
        lines += ["", "## Per-prompt differences (a - b)", ""]
        for c in report["contrasts"] + [dict(t, label=n, a=report['primary']['a'], b=report['primary']['b'],
                                             endpoint=report['primary']['endpoints'][n])
                                        for n, t in (report.get("primary") or {}).get("tests", {}).items()]:
            nonzero = {p: d for p, d in c["differences"].items() if d}
            lines.append(f"- {c.get('label', '')} ({c['a']} - {c['b']}, {c['endpoint']}): "
                         + (", ".join(f"{p} {d:+.2f}" for p, d in sorted(nonzero.items())) or "none differ"))
    lines += ["", "## Grade changes against the grades recorded at run time", ""]
    lines += [f"- {g}" for g in report["grade_changes"]] or ["None."]
    if "other_providers" in report:
        lines += ["", "## Task-model generations served by another provider", ""]
        lines += [f"- {g}" for g in report["other_providers"]] or ["None."]
    if traces:
        lines += ["", "## Traces", "", "```"] + traces + ["```"]
    lines += ["", "## Data problems", ""] + ([f"- {p}" for p in problems] or ["None."])
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("config", type=Path)
    parser.add_argument("--md", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--no-lookup", action="store_true")
    parser.add_argument("--trace", action="append", default=[], metavar="ARM:ID:REPEAT")
    args = parser.parse_args(argv)
    config = matched_study.load_config(args.config)
    report, problems, runs = build(config, lookup=not args.no_lookup)
    traces: list[str] = []
    for spec in args.trace:
        arm, pid, rep = spec.rsplit(":", 2)
        match = [r for r in runs.get(arm, []) if r["id"] == pid and r["rep"] == int(rep)]
        traces += timeline(match[0]) if match else [f"{spec}: no such run"]
    text = markdown(config, report, problems, traces)
    print(text)
    if args.md:
        args.md.write_text(text, encoding="utf-8", newline="\n")
    if args.json:
        args.json.write_text(json.dumps({"report": report, "problems": problems}, indent=1, default=str),
                             encoding="utf-8", newline="\n")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
