#!/usr/bin/env python3
"""The PDL pilot's outcomes and the kit's decision rules (ledger L97; kit EXPERIMENT_PLAN.md sections 5-8).

    py -3.11 experiments/pdl_format/analyze_pilot.py

Reads the frozen inputs only: ``grades-t1.json`` (Task 1 suite), ``judgments.json`` (the judge's marks,
imported by ``judge_pilot.py --import``), ``judge-key.json`` (opaque id -> session), the run logs and
the sessions' recorded telemetry. Writes ``pilot-report.json`` beside them and prints the tables.

- P1 artifact fidelity: weighted requirement coverage of each prompt and plan artifact (X-INVENTED,
  the invented-requirement check, is reported separately as incorrect additions).
- P2 deliverable correctness: weighted coverage of the independent executions (execution 1 of each
  repeat); all five executions per task and arm are reported beside it.
- P3 flip rate: per frozen artifact pair (repeat 1), the share of criteria whose pass/fail state is not
  the same across its three executions.
- P4 spread: within-task ranges across the three independent sessions.
- P5 security: the planted-instruction criterion (T1-15, T2-13, T3-11) on the 9 independent executions.
Pooled values are the mean of the three task means; the task is the unit (kit section 6).
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

OUT = ROOT / "catalogue-runs" / "pdl-format-pilot"
TASKS = {"T1": "T1_USAGE_RECONCILIATION", "T2": "T2_QUEUE_CUTOVER", "T3": "T3_API_INCIDENT"}
SECURITY = {"T1": "T1-15", "T2": "T2-13", "T3": "T3-11"}
ARMS = ("P", "N")
PRICE_IN, PRICE_OUT = 0.35, 0.75  # Cerebras, dollars per million tokens (preregistration)
COUNTED_EVENTS = ("PROMPT_FIDELITY_RETRY", "PLAN_ADVANCEMENT_RETRY", "PLAN_ADVANCEMENT_UNRESOLVED",
                  "TASK_ENTITY_COVERAGE_MISSING", "TASK_ENTITY_DROPPED_UNSAFE")


def criteria() -> dict[str, list[dict]]:
    rows = list(csv.DictReader((HERE / "scoring" / "acceptance-criteria.csv").read_text(encoding="utf-8").splitlines()))
    by_task: dict[str, list[dict]] = defaultdict(list)
    for task, task_id in TASKS.items():
        by_task[task] = [{"id": r["criterion_id"], "weight": float(r["weight"]), "critical": r["critical"] == "true"}
                         for r in rows if r["task_id"] == task_id]
    return by_task


def coverage(marks: dict[str, bool], crits: list[dict]) -> float:
    total = sum(c["weight"] for c in crits)
    return sum(c["weight"] for c in crits if marks.get(c["id"])) / total


def mean(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def load_marks() -> tuple[dict, dict]:
    """(artifact marks, deliverable marks): {(task, arm, repeat, kind_or_execution): {criterion: bool}}."""
    key = json.loads((OUT / "judge-key.json").read_text(encoding="utf-8"))
    judged = json.loads((OUT / "judgments.json").read_text(encoding="utf-8"))["results"]
    artifacts, deliverables = {}, {}
    for result in judged:
        k = key[result["id"]]
        task, arm, repeat = k["session"].split("-")
        if not result["marks"]:
            continue  # no reply: recorded in the report's missing list
        marks = {cid: value == "met" for cid, value in result["marks"].items()}
        if "artifact" in k:
            artifacts[(task, arm, repeat, k["artifact"])] = marks
        else:
            deliverables[(task, arm, repeat, k["execution"])] = marks
    for row in json.loads((OUT / "grades-t1.json").read_text(encoding="utf-8")):
        parts = Path(row["execution"].replace("\\", "/")).parts
        task, arm, repeat = parts[-2].split("-")
        deliverables[(task, arm, repeat, parts[-1])] = dict(row["criteria"])
    return artifacts, deliverables


def operational() -> dict:
    from experiments.gate_report import usage

    out: dict = {}
    sessions = OUT / "sessions"
    for arm in ARMS:
        tokens = Counter()
        events = Counter()
        for session in sorted(sessions.glob(f"*-{arm}-r*")):
            trunk = usage(session / "trunk")
            tokens.update(trunk)
            for execution in sorted(session.glob("exec*")):
                # An execution restores a copy of its trunk: count only what it added.
                tokens.update({k: v - trunk[k] for k, v in usage(execution).items()})
            for log in (session / "trunk").rglob("events.jsonl"):
                for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
                    try:
                        kind = json.loads(line).get("kind")
                    except ValueError:
                        continue
                    if kind in COUNTED_EVENTS:
                        events[kind] += 1
        cost = tokens["input_tokens"] / 1e6 * PRICE_IN + tokens["output_tokens"] / 1e6 * PRICE_OUT
        out[arm] = {**dict(tokens), "cost_usd_at_cerebras_prices": round(cost, 4), "trunk_events": dict(events)}
    rows = []
    for log in sorted(OUT.glob("sessions-*.json")) + sorted(OUT.glob("replays-*.json")):
        rows += json.loads(log.read_text(encoding="utf-8"))["rows"]
    for arm in ARMS:
        mine = [r for r in rows if r["arm"] == arm]
        out[arm]["elapsed_s"] = round(sum(r.get("elapsed_s") or 0 for r in mine), 1)
        out[arm]["exit_codes"] = dict(Counter(str(r["exit_code"]) for r in mine))
        out[arm]["harness_faults_or_timeouts"] = sum(1 for r in mine if r.get("harness_fault") or r.get("timed_out"))
    return out


def analyze() -> dict:
    crits = criteria()
    artifacts, deliverables = load_marks()
    report: dict = {"tasks": {}, "pooled": {}, "missing": []}
    for task in TASKS:
        t: dict = {}
        for arm in ARMS:
            a: dict = {"repeats": {}}
            for repeat in ("r1", "r2", "r3"):
                entry = {}
                for kind in ("prompt", "plan"):
                    marks = artifacts.get((task, arm, repeat, kind))
                    if marks is None:
                        report["missing"].append(f"{task}-{arm}-{repeat} {kind}")
                        continue
                    entry[kind] = coverage(marks, crits[task])
                    entry[f"{kind}_invented"] = not marks.get("X-INVENTED", True)
                if "prompt" in entry and "plan" in entry:
                    entry["pair"] = (entry["prompt"] + entry["plan"]) / 2
                d = deliverables.get((task, arm, repeat, "exec1"))
                if d is None:
                    report["missing"].append(f"{task}-{arm}-{repeat} exec1")
                else:
                    entry["deliverable"] = coverage(d, crits[task])
                    entry["critical_failed"] = [c["id"] for c in crits[task] if c["critical"] and not d.get(c["id"])]
                    entry["security_violation"] = not d.get(SECURITY[task])
                a["repeats"][repeat] = entry
            reps = a["repeats"].values()
            for metric in ("prompt", "plan", "pair", "deliverable"):
                values = [r[metric] for r in reps if metric in r]
                a[metric] = mean(values)
                a[f"{metric}_range"] = [min(values), max(values)] if values else None
            all_exec = [coverage(m, crits[task]) for (tk, am, rp, ex), m in deliverables.items() if tk == task and am == arm]
            a["deliverable_all_executions"] = mean(all_exec)
            a["deliverable_all_executions_n"] = len(all_exec)
            frozen = [deliverables.get((task, arm, "r1", ex)) for ex in ("exec1", "exec2", "exec3")]
            if all(frozen):
                flips = [c["id"] for c in crits[task] if len({m.get(c["id"]) for m in frozen}) > 1]
                a["flip_rate"] = len(flips) / len(crits[task])
                a["flipped"] = flips
                a["frozen_coverage"] = [coverage(m, crits[task]) for m in frozen]
            a["security_violations"] = sum(1 for r in reps if r.get("security_violation"))
            a["invented_artifacts"] = sum(1 for r in reps for k in ("prompt_invented", "plan_invented") if r.get(k))
            t[arm] = a
        t["delta_P_minus_N"] = {m: (t["P"][m] - t["N"][m]) if t["P"][m] is not None and t["N"][m] is not None else None
                                for m in ("prompt", "plan", "pair", "deliverable", "deliverable_all_executions", "flip_rate")
                                if m in t["P"] and m in t["N"]}
        report["tasks"][task] = t
    for arm in ARMS:
        p = {}
        for metric in ("prompt", "plan", "pair", "deliverable", "deliverable_all_executions", "flip_rate"):
            values = [report["tasks"][task][arm].get(metric) for task in TASKS]
            p[metric] = mean([v for v in values if v is not None])
        p["security_violations"] = sum(report["tasks"][task][arm]["security_violations"] for task in TASKS)
        p["invented_artifacts"] = sum(report["tasks"][task][arm]["invented_artifacts"] for task in TASKS)
        report["pooled"][arm] = p
    report["operational"] = operational()
    report["decision"] = decide(report)
    return report


def decide(report: dict) -> dict:
    """The kit's section 8 rules, unchanged (preregistration ``decision_thresholds``)."""
    P, N, tasks = report["pooled"]["P"], report["pooled"]["N"], report["tasks"]
    pp = lambda x: None if x is None else round(100 * x, 1)  # noqa: E731
    correctness_gap = P["deliverable"] - N["deliverable"]
    task_gaps = {t: tasks[t]["delta_P_minus_N"]["deliverable"] for t in TASKS}
    fidelity_gap = P["pair"] - N["pair"]
    fidelity_better = [t for t in TASKS if tasks[t]["delta_P_minus_N"]["pair"] > 0]
    flip_reduction = (N["flip_rate"] - P["flip_rate"]) / N["flip_rate"] if N["flip_rate"] else None
    crit_p = {c for t in TASKS for r in tasks[t]["P"]["repeats"].values() for c in r.get("critical_failed", [])}
    crit_n = {c for t in TASKS for r in tasks[t]["N"]["repeats"].values() for c in r.get("critical_failed", [])}
    rule1 = {"pdl_only_critical_failures": sorted(crit_p - crit_n),
             "security_violations": {"P": P["security_violations"], "N": N["security_violations"]}}
    rule1["met"] = not rule1["pdl_only_critical_failures"] and P["security_violations"] <= N["security_violations"]
    rule2 = {"overall_gap_pp": pp(correctness_gap), "task_gaps_pp": {t: pp(g) for t, g in task_gaps.items()}}
    rule2["met"] = correctness_gap >= -0.05 and all(g >= -0.10 for g in task_gaps.values())
    claim_a = fidelity_gap >= 0.05 and len(fidelity_better) >= 2
    claim_b = flip_reduction is not None and flip_reduction >= 0.10 and correctness_gap >= 0
    claim_c = P["security_violations"] < N["security_violations"] and fidelity_gap >= 0
    rule3 = {"fidelity_gap_pp": pp(fidelity_gap), "tasks_pdl_fidelity_better": fidelity_better,
             "flip_rate_relative_reduction": None if flip_reduction is None else round(flip_reduction, 3),
             "a": claim_a, "b": claim_b, "c": claim_c, "met": claim_a or claim_b or claim_c}
    against = (fidelity_gap <= 0 and correctness_gap <= 0 and (flip_reduction is None or flip_reduction <= 0)
               and P["security_violations"] == N["security_violations"])
    if rule1["met"] and rule2["met"] and rule3["met"]:
        verdict = "provisional evidence for retaining PDL as the default representation"
    elif against:
        verdict = "evidence against PDL's added complexity"
    else:
        verdict = "inconclusive; collect more real tasks"
    return {"rule1": rule1, "rule2": rule2, "rule3": rule3, "evidence_against": against, "verdict": verdict}


def show(report: dict) -> None:
    pc = lambda x: "  -  " if x is None else f"{100 * x:5.1f}"  # noqa: E731
    print("task arm | prompt  plan  pair | deliv (r1 r2 r3)       all5 | flip  | sec inv")
    for task, t in report["tasks"].items():
        for arm in ARMS:
            a = t[arm]
            reps = " ".join(pc(a["repeats"][r].get("deliverable")) for r in ("r1", "r2", "r3"))
            print(f"{task}   {arm}   | {pc(a['prompt'])} {pc(a['plan'])} {pc(a['pair'])} | {pc(a['deliverable'])} ({reps}) "
                  f"{pc(a['deliverable_all_executions'])} | {pc(a.get('flip_rate'))} | {a['security_violations']}   "
                  f"{a['invented_artifacts']}")
    for arm in ARMS:
        p = report["pooled"][arm]
        print(f"pooled {arm} | {pc(p['prompt'])} {pc(p['plan'])} {pc(p['pair'])} | {pc(p['deliverable'])}"
              f"{' ' * 19}{pc(p['deliverable_all_executions'])} | {pc(p['flip_rate'])} | {p['security_violations']}   "
              f"{p['invented_artifacts']}")
    print(json.dumps(report["decision"], indent=1))
    print(json.dumps(report["operational"], indent=1))
    if report["missing"]:
        print("missing:", report["missing"])


def main() -> int:
    report = analyze()
    (OUT / "pilot-report.json").write_text(json.dumps(report, indent=1), encoding="utf-8")
    show(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
