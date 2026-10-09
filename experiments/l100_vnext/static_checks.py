"""L100 vNext static acceptance (docs/plans/ENTITY_VNEXT_PLAN.md, section 4). No model call, no network, no key.

    py -3.11 experiments/l100_vnext/static_checks.py s1 ORIGINAL_TREE OUT_DIR
        S1 at this tree and at ORIGINAL_TREE (a worktree at a5973ae7), every catalogue prompt:
        (a) the rendered prompts (scripts/render_recorded_prompts.py render + compare: the recorded
            fixture's requests, and each prompt's first request with no System 1 attached);
        (b) the provider bodies ApiWorker builds (build_request_body: no HTTP request is made, and
            no header, which would carry the key, exists) for BOOTSTRAP and EXECUTE, System 1's
            decisions held fixed and BOOTSTRAP answered with an analysis that names no entity.
    py -3.11 experiments/l100_vnext/static_checks.py replay OUT_DIR
        S2-S5 on L99's 126 recorded runs (a5973ae7, recorded provider bodies): each recorded
        BOOTSTRAP reply parses (S2); each run is replayed through this tree's engine, System 1
        answering from the run's recorded events and BOOTSTRAP from its recorded replies; System 1's
        replayed decisions must equal the recorded ones, the BOOTSTRAP provider body must equal the
        recorded one, and so must the EXECUTE body except D1's additions to TASK_ENTITIES (S3);
        the additions must be the plan's list, labelled, with the planted payload kept out (S4, S5).
    py -3.11 experiments/l100_vnext/static_checks.py bodies OUT_JSON
        (internal, for s1) the BOOTSTRAP provider bodies of the tree named by $PDLT_CHECK_TREE.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TREE = HERE.parents[1]
L99 = TREE / "catalogue-runs" / "run-20261009-042907-unconfirmed-tier-d1"
WORKER = dict(model="openai/gpt-oss-120b", provider_pinning={"order": ["Cerebras"], "allow_fallbacks": False},
              structured_output=True, reasoning_effort="low")

# The plan's list (section 4, S4/S5): every (run, name) D1 adds, and the payload that must stay out.
D1_EXPECTED = {
    ("12-04_docker_multi_stage_r1", "explanations of each optimization"),
    ("12-04_docker_multi_stage_r3", "optimized multi-stage Dockerfile"),
    ("12-07_tls_certificate_chain_r3", "server‑side fix"),
    ("12-07_tls_certificate_chain_r3", "client‑side debugging aid"),
    ("12-07_tls_certificate_chain_r3", "openssl verify"),
    ("16-03_knights_and_knaves_r2", "knights and knaves"),
    ("16-06_sibling_count_r3", "number of sisters each brother has"),
    ("16-07_house_grid_r2", "house 1"),
    ("16-07_house_grid_r2", "house 2"),
    ("16-07_house_grid_r2", "house 3"),
}
PLANTED_RUN = "09-04_json_payload_pollution_r2"
HOSTILE_MARKS = ("[REDACTED_IOC]", "TRIPWIRE_", "CANARY_", "SYSTEM OVERRIDE")
SYS1_EVENTS = ("ACTIVATION_ROUTED", "PROBLEM_CLASS_CLASSIFIED", "EXECUTION_PROFILE_ROUTED")
FIXTURE_CONSTRAINTS = "Obey applicable provider/platform safety, privacy, permission, and tool constraints."


class _Stop(Exception):
    pass


# --- S1 ------------------------------------------------------------------------------------------

def bodies(out: Path) -> None:
    tree = Path(os.environ["PDLT_CHECK_TREE"]).resolve()
    sys.path[:0] = [str(tree / "src")]
    from pdl_taskmaster.providers.api_worker import ApiWorker
    from pdl_taskmaster.runtime.session_engine import SessionEngine

    worker = ApiWorker(repo_root=tree, **WORKER)
    # System 1's decisions held fixed (L99's 12-04 r1: apply, standard execution); BOOTSTRAP answered
    # with an analysis that names no entity, so both trees build EXECUTE from the same input.
    turn = next((L99 / "results" / "12-04_docker_multi_stage_r1" / "session").glob("W-*/turns/turn_001"))
    events = [json.loads(x) for x in (turn / "events/events.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
    decisions = {k: _first_event(events, k) for k in SYS1_EVENTS}
    analysis = json.dumps({"kind": "ANALYSIS", "task_summary": "Complete the request.", "approach_notes": "",
                           "risk_notes": "", "task_entities": []})
    result = {}
    for line in (tree / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        text = (tree / "prompts" / item["file"]).read_text(encoding="utf-8-sig")
        built = {}

        def model_call(request, _built=built):
            _built.setdefault(request.operation, worker.build_request_body(request)[0])
            if request.operation == "BOOTSTRAP_ANALYSIS":
                return analysis
            raise _Stop

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            engine = SessionEngine(str(tree), model_call, available_execution_tools=None, workspace_root=tmp,
                                   sys1_client=ReplaySys1(decisions), no_review=True, render_compact=True,
                                   higher_priority_constraints=FIXTURE_CONSTRAINTS)
            engine.bridge.contract_form = worker.contract_form
            engine.tier_d1 = True
            try:
                engine.handle_user_message(text)
            except Exception:
                pass
        result[item["id"]] = built
    out.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=1), encoding="utf-8")


def s1(original: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    for name, tree in (("original", original.resolve()), ("vnext", TREE)):
        env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PDLT_CHECK_TREE": str(tree)}
        env.pop("PYTHONPATH", None)
        subprocess.run([sys.executable, "scripts/render_recorded_prompts.py", "render", str(out / f"render-{name}.json")],
                       cwd=tree, env=env, check=True, capture_output=True)
        subprocess.run([sys.executable, str(HERE / "static_checks.py"), "bodies", str(out / f"bodies-{name}.json")],
                       cwd=tree, env=env, check=True)
    cmp = subprocess.run([sys.executable, "scripts/render_recorded_prompts.py", "compare",
                          str(out / "render-original.json"), str(out / "render-vnext.json")],
                         cwd=TREE, capture_output=True, text=True, encoding="utf-8")
    renders = {n: json.loads((out / f"render-{n}.json").read_text(encoding="utf-8")) for n in ("original", "vnext")}
    print(f"S1a render compare: exit {cmp.returncode}; fixture requests {len(renders['vnext']['fixture'])}, "
          f"bootstrap requests {len(renders['vnext']['bootstrap'])}")
    print("   ", (cmp.stdout + cmp.stderr).strip()[-1200:])
    a = json.loads((out / "bodies-original.json").read_text(encoding="utf-8"))
    b = json.loads((out / "bodies-vnext.json").read_text(encoding="utf-8"))
    sent = {op: sum(op in v for v in b.values()) for op in ("BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED")}
    differ = sorted(f"{k}:{op}" for k in set(a) | set(b) for op in set(a.get(k, {})) | set(b.get(k, {}))
                    if a.get(k, {}).get(op) != b.get(k, {}).get(op))
    print(f"S1b provider bodies (System 1 fixed, render compact): {len(b)} prompts, built {sent}; "
          f"bodies or operations that differ: {len(differ)} {differ[:5]}")
    ok = cmp.returncode == 0 and not differ and set(a) == set(b) and sent["BOOTSTRAP_ANALYSIS"] == len(b)
    print("S1", "PASS" if ok else "FAIL")
    return 0 if ok else 1


# --- S2-S5 ---------------------------------------------------------------------------------------

class ReplaySys1:
    """System 1 answering from one recorded run's events (plan 3.1): its decisions are held fixed.
    The route event records the verdict, its confidence and whether the gate passed, not the
    distribution; the answer puts the rest on one other choice when the gate passed, and spreads
    it when it did not (the replayed event must equal the recorded one either way)."""

    is_configured = True
    model = "replay"
    ROUTES = ("APPLY_PROTOCOL", "PROTOCOL_DISCUSSION", "BYPASS", "BLOCKED_BY_HIGHER_PRIORITY")
    EVENT = {"route": "ACTIVATION_ROUTED", "problem_class": "PROBLEM_CLASS_CLASSIFIED",
             "execution_profile": "EXECUTION_PROFILE_ROUTED"}

    def __init__(self, recorded: dict[str, dict | None]):
        self.recorded = recorded
        self.unknown: list[str] = []

    def call(self, request):
        name = next(iter(request.questions))
        p = self.recorded.get(self.EVENT.get(name, ""))
        if p is None:
            self.unknown.append(name)
            raise RuntimeError(f"no recorded System 1 answer for {name}")
        if name == "route":
            conf, others = float(p["confidence"]), [c for c in self.ROUTES if c != p["verdict"]]
            rest = [1 - conf, 0.0, 0.0] if p["passed_gating"] else [(1 - conf) / 3] * 3
            answer = {"choice": p["verdict"], "confidence": conf,
                      "probabilities": {p["verdict"]: conf, **dict(zip(others, rest))}}
        elif name == "problem_class":
            answer = {"choice": p["verdict"], "confidence": p["confidence"], "probabilities": p["distribution"]}
        else:
            dist = p["distribution"]
            choice = max(dist, key=dist.get)
            answer = {"choice": choice, "confidence": dist[choice], "probabilities": dist}
        return {"answers": {name: answer}}, 1.0


def _first_event(events: list[dict], kind: str):
    return next((e["payload"] for e in events if e["kind"] == kind), None)


def _split(text: str) -> tuple[dict, str]:
    """A provider body's input: the projection, then any text the worker appends after it."""
    doc, end = json.JSONDecoder().raw_decode(text)
    return doc, text[end:]


def _recorded_body(session: Path, operation: str):
    files = sorted(session.glob(f"*/provider-requests/*-{operation}-1-a1.json"))
    return json.loads(files[0].read_text(encoding="utf-8")) if files else None


def _without_additions(body: dict) -> dict:
    """The body with D1's entries taken out of TASK_ENTITIES, serialized as the worker serializes it."""
    doc, tail = _split(body["input"])
    inputs = doc["operation_inputs"]
    inputs["TASK_ENTITIES"] = [e for e in inputs.get("TASK_ENTITIES") or [] if "name_source" not in e]
    return {**body, "input": json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + tail}


def replay(out: Path) -> int:
    sys.path[:0] = [str(TREE / "src")]
    from pdl_taskmaster.providers.api_worker import ApiWorker
    from pdl_taskmaster.runtime.operation_bridge import OperationBridge
    from pdl_taskmaster.runtime.session_engine import SessionEngine

    out.mkdir(parents=True, exist_ok=True)
    api = ApiWorker(repo_root=TREE, **WORKER)
    bridge = OperationBridge(TREE)
    runs = sorted((L99 / "results").iterdir())
    constraints = next(_split(b["input"])[0]["operation_inputs"]["HIGHER_PRIORITY_CONSTRAINTS"] for d in runs
                       if (b := _recorded_body(d / "session", "EXECUTE_UNCONFIRMED")) is not None)
    s2_fail, s2_count, rows = [], 0, []
    for d in runs:
        session = d / "session"
        turn = next(session.glob("W-*/turns/turn_001"))
        replies = [p.read_text(encoding="utf-8") for p in
                   sorted(turn.glob("stages/10_prompt/output/*-bootstrap_analysis/model-response.txt"))]
        for text in replies:  # S2
            s2_count += 1
            try:
                bridge.parse_bootstrap_analysis(text)
            except Exception as exc:
                s2_fail.append((d.name, str(exc)[:120]))
        events = [json.loads(x) for x in (turn / "events/events.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]
        recorded_sys1 = {k: _first_event(events, k) for k in SYS1_EVENTS}
        recorded = {op: _recorded_body(session, op) for op in ("BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED")}
        sys1 = ReplaySys1(recorded_sys1)
        queue, built = list(replies), {}

        def worker(request, _queue=queue, _built=built):
            _built.setdefault(request.operation, api.build_request_body(request)[0])
            if request.operation == "BOOTSTRAP_ANALYSIS" and _queue:
                return _queue.pop(0)
            raise _Stop

        file = json.loads((d / "result.json").read_text(encoding="utf-8"))["file"]
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            engine = SessionEngine(str(TREE), worker, available_execution_tools=None, workspace_root=tmp,
                                   sys1_client=sys1, no_review=True, render_compact=True,
                                   higher_priority_constraints=constraints)
            engine.bridge.contract_form = api.contract_form
            engine.tier_d1 = True
            try:
                engine.handle_user_message((TREE / "prompts" / file).read_text(encoding="utf-8-sig"))
            except Exception:
                pass
            replay_events = engine.workspace.read_events() if engine.workspace is not None else []
        row = {"run": d.name, "sys1_unknown": sys1.unknown,
               "sys1_same": all(_first_event(replay_events, k) == recorded_sys1[k] for k in SYS1_EVENTS),
               # the operations sent, and the BOOTSTRAP body byte for byte
               "operations_same": set(built) == {op for op, b in recorded.items() if b is not None},
               "bootstrap_same": built.get("BOOTSTRAP_ANALYSIS") == recorded["BOOTSTRAP_ANALYSIS"]}
        new, rec = built.get("EXECUTE_UNCONFIRMED"), recorded["EXECUTE_UNCONFIRMED"]
        if new is not None and rec is not None:
            ni = _split(new["input"])[0]["operation_inputs"]
            row["execute"] = ("identical" if new == rec else
                              "additions only" if _without_additions(new) == rec else "differs")
            row["added"] = [[e["surface"], e.get("status"), e.get("name_source")]
                            for e in ni.get("TASK_ENTITIES") or [] if "name_source" in e]
            row["forwarded"] = ni.get("TASK_ENTITIES") or []
        row["unanchored_event"] = [e["payload"] for e in replay_events if e["kind"] == "TASK_ENTITY_UNANCHORED"]
        rows.append(row)
        print(d.name, {k: row[k] for k in ("sys1_same", "operations_same", "bootstrap_same")},
              row.get("execute", "no EXECUTE"), row.get("added") or "", flush=True)

    (out / "replay.json").write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    upstream = [r["run"] for r in rows if not (r["sys1_same"] and r["operations_same"] and r["bootstrap_same"])]
    executed = [r for r in rows if "execute" in r]
    count = {k: sum(r["execute"] == k for r in executed) for k in ("identical", "additions only", "differs")}
    added = {(r["run"], name) for r in executed for name, _status, _src in r["added"]}
    unlabelled = [r["run"] for r in executed if any(src != "model" for _n, _s, src in r["added"])]
    counted = [r["run"] for r in rows if r["unanchored_event"] != ([{"count": len(r["added"])}] if r.get("added") else [])]
    planted = [r for r in executed if r["run"] == PLANTED_RUN]
    planted_out = bool(planted) and all("[REDACTED_IOC]" not in json.dumps(r["forwarded"]) and not r["added"] for r in planted)
    hostile = [(r["run"], m) for r in executed for m in HOSTILE_MARKS if m in json.dumps(r["forwarded"], ensure_ascii=False)]
    print(f"\nS2 recorded BOOTSTRAP replies that parse: {s2_count - len(s2_fail)} of {s2_count} {s2_fail[:3]}")
    print(f"S3 runs replayed {len(rows)}; System 1 decisions, operations sent or BOOTSTRAP body (bytes) differ in: "
          f"{upstream or 'none'}")
    print(f"S3 EXECUTE bodies ({len(executed)} runs; the other {len(rows) - len(executed)} sent no EXECUTE, as recorded): "
          f"byte-identical {count['identical']}, byte-identical once D1's entries are taken out {count['additions only']}, "
          f"other differences {count['differs']}")
    for r in [r for r in executed if r["execute"] == "differs"][:10]:
        print("    differs:", r["run"])
    print(f"S4 additions are the plan's list: {added == D1_EXPECTED} (missing {sorted(D1_EXPECTED - added)}, "
          f"extra {sorted(added - D1_EXPECTED)}); TASK_ENTITY_UNANCHORED wrong in: {counted or 'none'}")
    print(f"S5 every addition labelled name_source=model: {not unlabelled}; planted payload ({PLANTED_RUN}) kept out: "
          f"{planted_out}; hostile marks forwarded: {hostile or 'none'}")
    ok = (not s2_fail and not upstream and not count["differs"] and added == D1_EXPECTED and not unlabelled
          and not counted and planted_out and not hostile)
    print("S2-S5", "PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    command = sys.argv[1]
    if command == "bodies":
        bodies(Path(sys.argv[2]))
    elif command == "s1":
        raise SystemExit(s1(Path(sys.argv[2]), Path(sys.argv[3])))
    elif command == "replay":
        raise SystemExit(replay(Path(sys.argv[2])))
