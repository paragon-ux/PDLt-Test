"""The acceptance-gate tooling (experiments/): offline, with no model calls."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

import graders
from experiments import adjudicate, analysis, generate, grading, prompt_set, runner, schedule

ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------------------------------- frozen sets

def test_generated_sets_reproduce_from_their_seeds():
    assert [p for name in generate.SETS for p in generate.check_set(name)] == []


def test_prompt_set_lock_matches_every_file():
    assert prompt_set.check_lock() == []


def test_lock_hash_ignores_line_endings(tmp_path):
    lf, crlf = tmp_path / "lf.txt", tmp_path / "crlf.txt"
    lf.write_bytes(b"line one\nline two\n")
    crlf.write_bytes(b"line one\r\nline two\r\n")
    assert prompt_set._sha256(lf) == prompt_set._sha256(crlf)


def test_lock_strata_follow_the_selection_rule():
    lock = json.loads(prompt_set.LOCK_PATH.read_text(encoding="utf-8"))
    counts = lock["counts"]
    assert counts == {"T": 18, "G": 24, "S": 4, "I": 7, "Q": 6, "DEV": 24}
    manifest = grading.catalogue_items()
    # Every T and S prompt has a grader; Q prompts are exactly those whose grader lacks PASS or FAIL.
    for item in lock["items"]:
        if item["stratum"] in ("T", "S", "Q"):
            assert manifest[item["id"]].grade_corpus is not None, item["id"]
    gate_ids = {i["id"] for i in lock["items"] if i["set"] == "gate"}
    dev_ids = {i["id"] for i in lock["items"] if i["set"] == "dev"}
    assert not gate_ids & dev_ids


def _canonical(family: str, solution: dict) -> str:
    if family == "SS":
        return "\n".join(str(s) for s in solution["subsets"]) + f"\nTotal: {solution['solution_count']} subsets."
    if family == "LS":
        return "\n".join(str(r) for r in solution["original_complete_square"])
    if family == "HP":
        return "Path: " + str(solution["hamiltonian_path"])
    if family == "KK":
        return "\n".join(f"{name} is a {role}." for name, role in solution["answer"].items())
    return f"{solution['answer']['fish_owner']} owns the fish."


def _corrupted(family: str, solution: dict) -> str:
    if family == "SS":
        return "\n".join(str(s) for s in solution["subsets"][1:]) + f"\nTotal: {solution['solution_count']}."
    if family == "LS":
        square = [list(r) for r in solution["original_complete_square"]]
        square[0][0], square[0][1] = square[0][1], square[0][1]  # a duplicate in row 1
        return "\n".join(str(r) for r in square)
    if family == "HP":
        return "Path: " + str(solution["hamiltonian_path"][:-1])  # misses a node
    if family == "KK":
        flipped = dict(solution["answer"])
        name = next(iter(flipped))
        flipped[name] = "knave" if flipped[name] == "knight" else "knight"
        return "\n".join(f"{n} is a {r}." for n, r in flipped.items())
    owner = solution["answer"]["fish_owner"]
    wrong = next(o for o in ("Ana", "Ben", "Cleo") if o != owner)
    return f"{wrong} owns the fish."


@pytest.mark.parametrize("set_name", ["gate", "dev"])
def test_generated_items_pass_on_their_answer_and_fail_on_a_corrupted_one(set_name):
    items = grading.generated_items(set_name)
    assert len(items) == 24
    for item_id, item in items.items():
        family = item_id.split("-")[1]
        solution = json.loads((grading.GENERATED / set_name / family / f"{item_id}.solution.json")
                              .read_text(encoding="utf-8"))
        assert grading.grade_text(item, "RESULT", _canonical(family, solution), run_code=False)["grade"] == \
            graders.PASS, item_id
        assert grading.grade_text(item, "RESULT", _corrupted(family, solution), run_code=False)["grade"] != \
            graders.PASS, item_id


def test_generated_logic_items_have_exactly_one_answer():
    import itertools
    import re

    for set_name in ("gate", "dev"):
        for item_id, item in grading.generated_items(set_name).items():
            if "-HG-" not in item_id:
                continue
            clues = re.findall(r"^\d+\. (.+)$", item.prompt_text, re.M)
            pool = {text: check for solution in generate._arrangements()
                    for text, check in generate._hg_clues(solution)}
            matches = [s for s in itertools.islice(generate._arrangements(), None)
                       if all(pool[c](s) for c in clues)]
            assert len(matches) == 1, item_id


# --------------------------------------------------------------------------- grading

def _execution_dir(root: Path, name: str) -> Path:
    path = root / "session" / "W-1" / "turns" / "turn_001" / "stages" / "50_execution" / "output" / name
    path.mkdir(parents=True)
    return path


def test_first_attempt_reads_the_first_execute_reply_not_the_repair(tmp_path):
    (_execution_dir(tmp_path, "0005-execute") / "model-response.txt").write_text(
        json.dumps({"kind": "RESULT", "body": "first"}), encoding="utf-8")
    (_execution_dir(tmp_path, "0006-execute") / "model-response.txt").write_text(
        json.dumps({"kind": "RESULT", "body": "repaired"}), encoding="utf-8")
    first = grading.first_attempt(tmp_path)
    assert (first["status"], first["kind"], first["text"]) == ("reply", "RESULT", "first")


def test_first_attempt_statuses(tmp_path):
    assert grading.first_attempt(tmp_path / "none")["status"] == "not_reached"
    (_execution_dir(tmp_path / "cap", "0005-execute") / "model-response.truncated.txt").write_text("x")
    assert grading.first_attempt(tmp_path / "cap")["status"] == "output_limit"
    (_execution_dir(tmp_path / "bad", "0005-execute") / "model-response.txt").write_text("not json")
    assert grading.first_attempt(tmp_path / "bad")["status"] == "malformed"


def _write_events(root: Path, *events: tuple[str, dict]) -> None:
    path = root / "session" / "W-1" / "turns" / "turn_001" / "events"
    path.mkdir(parents=True, exist_ok=True)
    (path / "events.jsonl").write_text("".join(json.dumps({"kind": k, "payload": p}) + "\n" for k, p in events),
                                       encoding="utf-8")


def test_headless_stop_is_a_published_host_finding(tmp_path):
    _write_events(tmp_path / "a", ("PLAN_ADVANCEMENT_UNRESOLVED", {"host_note": True}))
    _write_events(tmp_path / "b", ("PLAN_ADVANCEMENT", {"verdict": "RESTATES"}), ("PLAN_ADVANCEMENT_RETRY", {}))
    _write_events(tmp_path / "c", ("PROMPT_LINT_UNRESOLVED", {"host_note": True}))
    assert grading.headless_stop(tmp_path / "a") and grading.headless_stop(tmp_path / "c")
    assert not grading.headless_stop(tmp_path / "b")  # a redraft that resolved stops nothing


def test_grading_runs_code_under_one_common_budget(monkeypatch):
    seen = {}

    class FakeSandbox:
        def __init__(self, **kwargs):
            seen["timeout"] = kwargs["timeout_seconds"]

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def run_code(self, code, *, timeout, memory_limit, step_limit):
            seen.update(step_limit=step_limit, memory=memory_limit)

            class Out:
                exit_code, stdout = 0, "42\n"
            return Out()

    import pdl_taskmaster.verification.sandbox as sandbox

    monkeypatch.setattr(sandbox, "ExecutionSandbox", FakeSandbox)
    built = grading.corpus("RESULT", "```python\nprint(42)\n```")
    heavy = sandbox.EXECUTION_BUDGETS["HEAVY_COMPUTE"]
    assert seen == {"timeout": heavy.timeout_seconds, "step_limit": heavy.step_limit,
                    "memory": heavy.memory_limit_bytes}
    assert "[GRADER: deliverable code stdout]\n42" in built


def test_whole_source_deliverables_run_with_their_result_ir_attached(monkeypatch):
    """A protocol deliverable that is a bare program, with its Result IR appended, is
    run as the host ran it. Before, the appended IR made it non-source, so it ran only
    a plain call's fenced code: an asymmetry between arms."""
    ran = []

    class FakeSandbox:
        def __init__(self, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def run_code(self, code, **kwargs):
            ran.append(code)

            class Out:
                exit_code, stdout = 0, "WITNESS: {\"product\": 56}\n"
            return Out()

    import pdl_taskmaster.verification.sandbox as sandbox

    monkeypatch.setattr(sandbox, "ExecutionSandbox", FakeSandbox)
    program = "result = 7 * 8\nprint(result)"
    ir = json.dumps({"files": [], "reconciliation": [], "open_defects": []}, indent=2)
    built = grading.corpus("RESULT", f"{program}\n\n```json\n{ir}\n```")
    assert ran == [program] and "WITNESS" in built


def test_strip_for_adjudication_removes_harness_marks():
    ir = json.dumps({"files": [], "reconciliation": [], "open_defects": [], "witness": {"x": 1}}, indent=2)
    text = f"The answer is 56.\n\n[host] Witness not reproduced by a program run; unverified.\n\n```json\n{ir}\n```"
    assert grading.strip_for_adjudication(text) == "The answer is 56."
    wrapped = "UNVERIFIED ANSWER: x\n\nCandidate deliverable:\nBody here"
    assert grading.strip_for_adjudication(wrapped) == "Body here"
    data_block = 'Result:\n```json\n{"answer": 3}\n```'  # a deliverable's own JSON stays
    assert grading.strip_for_adjudication(data_block) == data_block


def test_export_adjudication_is_blind(tmp_path):
    rows = [{"model": "m", "item_id": "16-03", "rep": 1, "arm": arm, "text": f"text {arm}"}
            for arm in ("C0", "P_new")]
    sheet, key = grading.export_adjudication(rows, tmp_path, seed=1)
    content = sheet.read_text(encoding="utf-8")
    assert "C0" not in content.replace("text C0", "") and "P_new" not in content.replace("text P_new", "")
    assert {json.loads(l)["arm"] for l in key.read_text(encoding="utf-8").splitlines()} == {"C0", "P_new"}


# --------------------------------------------------------------------------- statistics and rules

def test_sign_flip_exact_and_bootstrap():
    assert analysis.sign_flip_p([1, 1, 1, 1, 1]) == pytest.approx(2 / 32)
    assert analysis.sign_flip_p([0, 0]) == 1.0
    lo, hi = analysis.bootstrap_ci([0.5, 0.0, 1.0, 0.5, 0.0, 0.5], seed=3)
    assert lo <= 0.4166 <= hi
    assert analysis.bootstrap_ci([0.5, 0.5]) == (0.5, 0.5)


def _row(model, arm, item, rep, value, stratum="T"):
    return {"model": model, "arm": arm, "item_id": item, "rep": rep, "stratum": stratum,
            "scores": {"primary": value, "audited": value}}


def test_gate_decision_rules():
    rows = []
    for i in range(12):
        for rep in (1, 2):
            rows += [_row("m", "P_old", f"t{i}", rep, 1), _row("m", "P_new", f"t{i}", rep, 0 if i < 10 else 1),
                     _row("m", "C0", f"t{i}", rep, 1)]
    rows += [_row("m", arm, "s1", 1, 1, "S") for arm in ("P_old", "P_new")]
    decision = analysis.gate_decision(rows, "m", mechanism_checks={"FB1": True})
    assert decision["G2"]["decision"] == "reject" and decision["decision"] == "reject"
    better = [dict(r, scores={"primary": 1, "audited": 1}) if r["arm"] == "P_new" else r for r in rows]
    assert analysis.gate_decision(better, "m", mechanism_checks={"FB1": True})["decision"] == "accept"
    assert analysis.gate_decision(better, "m", mechanism_checks={"FB1": False})["decision"] == "reject"
    unsafe = better + [_row("m", "P_old", "s2", 1, 1, "S"), _row("m", "P_new", "s2", 1, 0, "S")]
    assert analysis.gate_decision(unsafe, "m", mechanism_checks={})["G1_safety_regressions"] == ["s2 r1"]


def test_pending_rows_block_a_comparison():
    rows = [_row("m", "P_new", "t1", 1, None), _row("m", "P_old", "t1", 1, 1)]
    with pytest.raises(analysis.PendingAdjudication):
        analysis.compare(rows, "m", "P_new", "P_old", score="audited")


# --------------------------------------------------------------------------- schedule and ledger

def test_schedule_is_seeded_repetition_ordered_and_interleaved():
    blocks = schedule.build_schedule(["a", "b"], ["x", "y", "z"], reps=2, arms=["C0", "P"],
                                     branches={"P": ["P", "HI"]}, seed=7)
    again = schedule.build_schedule(["a", "b"], ["x", "y", "z"], reps=2, arms=["C0", "P"],
                                    branches={"P": ["P", "HI"]}, seed=7)
    assert [b.as_dict() for b in blocks] == [b.as_dict() for b in again]
    assert [b.model for b in blocks[:4]] == ["a", "b", "a", "b"]
    for model in ("a", "b"):
        reps = [b.rep for b in blocks if b.model == model]
        assert reps == sorted(reps)  # every repetition-1 block first
    assert all(set(b.branches["P"]) == {"P", "HI"} for b in blocks)


def test_ledger_resumes_and_voids_whole_blocks(tmp_path):
    ledger = schedule.Ledger(tmp_path / "ledger.jsonl")
    ledger.append({"block_id": "b", "attempt": 1, "arm": "C0", "branch": None, "status": "done"})
    ledger.append({"block_id": "b", "attempt": 1, "arm": "HI", "unit_arm": "P", "branch": "HI", "status": "done"})
    assert ledger.done_units("b") == {("C0", None), ("P", "HI")}
    assert ledger.void_block("b", "429") == 2
    assert ledger.done_units("b") == set() and ledger.results() == []
    ledger.append({"block_id": "b", "attempt": 2, "arm": "C0", "branch": None, "status": "done"})
    assert [r["attempt"] for r in ledger.results()] == [2]


# --------------------------------------------------------------------------- adjudication

def test_adjudication_queue_is_symmetric(tmp_path):
    rows = []
    for i in range(10):
        rows += [_row("m", "P_new", f"t{i}", 1, 1), _row("m", "P_old", f"t{i}", 1, 1 if i else 0),
                 _row("m", "C0", f"t{i}", 1, 0 if i == 1 else 1)]
    rows.append(_row("m", "P_new", "q", 1, None))
    chosen = {(r["arm"], r["item_id"]) for r in adjudicate.queue(rows, seed=0)}
    assert {("P_new", "t0"), ("P_old", "t0")} <= chosen  # P_new passed, P_old failed
    assert {("P_new", "t1"), ("C0", "t1")} <= chosen  # P_new passed, C0 failed
    assert ("P_new", "q") in chosen  # pending
    audited = adjudicate.apply(rows, {("m", "P_new", "q", 1): 0})
    assert next(r for r in audited if r["item_id"] == "q")["scores"]["audited"] == 0


# --------------------------------------------------------------------------- controls (request bodies only)

@pytest.fixture
def controls(tmp_path):
    from experiments.controls import Controls

    c = Controls(ROOT, model="openai/gpt-oss-120b", providers=["Crusoe"], trace_path=tmp_path / "trace.jsonl")
    yield c
    c.close()


def test_c0_sends_the_request_alone(controls):
    body = controls.plain_body("Compute 7*8.", None)
    assert body["input"] == "Compute 7*8." and "reasoning" not in body and "instructions" not in body
    assert body["provider"] == {"order": ["Crusoe"], "allow_fallbacks": False}
    assert "temperature" not in body and "top_p" not in body
    assert controls.plain_body("x", "medium")["reasoning"] == {"effort": "medium"}


@pytest.mark.parametrize("verified", [False, True])
def test_c2_shows_executes_exact_output_contract(controls, verified):
    body = controls.c2_body("Compute 7*8.", "medium", verified=verified)
    projection = controls.execute_request("Compute 7*8.", verified=verified).projection.document
    schema_text = json.dumps(projection["output_schema"], indent=2, ensure_ascii=False)
    assert schema_text in body["input"] and body["text"] == {"format": {"type": "json_object"}}
    assert body["instructions"] == controls.worker._bootstrap.rstrip()
    assert ("result_ir" in schema_text) is verified


def test_c3_is_execute_without_prompt_or_plan(controls):
    request = controls.execute_request("Compute 7*8.")
    inputs = request.projection.document["operation_inputs"]
    assert inputs["CONFIRMED_PROMPT_BODY"] is None and inputs["CONFIRMED_PLAN_BODY"] is None
    assert inputs["SUPPLIED_EXECUTION_INPUT_SOURCE"] == "Compute 7*8."
    assert request.operation == "EXECUTE"


# --------------------------------------------------------------------------- runner

def test_protocol_failures_are_classified_by_category():
    def run(code, stderr="", timed_out=False, fault=None):
        return {"exit_code": code, "stderr": stderr, "timed_out": timed_out, "harness_fault": fault}

    def harness(record):
        return "[harness-error] " + json.dumps(record)

    assert runner.classify_protocol_failure(run(1)) is None
    assert runner.classify_protocol_failure(run(0, timed_out=True)) == "outage"
    assert runner.classify_protocol_failure(run(0, fault="HARNESS_HANG")) == "outage"
    deadline = harness({"category": "PROVIDER_UNAVAILABLE", "message": "call exceeded its 300s deadline"})
    assert runner.classify_protocol_failure(run(4, deadline)) is None  # the arm's outcome
    assert runner.classify_protocol_failure(run(4, harness({"category": "OUTPUT_MALFORMED"}))) is None
    rate = harness({"category": "PROVIDER_UNAVAILABLE", "status": 429, "message": "HTTP 429"})
    assert runner.classify_protocol_failure(run(4, rate)) == "outage"


def test_scores():
    assert runner.to_score(True, graders.PASS) == 1
    assert runner.to_score(True, graders.MANUAL) is None
    assert runner.to_score(False, graders.PASS) == 0
    assert runner.to_score(True, "ERROR") == 0


def test_example_config_plans(capsys):
    config = runner.load_config(ROOT / "experiments" / "gate_config.example.json")
    assert runner.cmd_plan(config, type("A", (), {"smoke": False, "show": 1})()) == 0
    out = capsys.readouterr().out
    assert out.startswith("106 blocks")  # 53 prompts x 2 repetitions, one model


# --------------------------------------------------------------------------- fork fidelity (§3.2)

@pytest.mark.parametrize("verified", [True, False])
def test_a_branch_resumed_from_plan_review_sends_the_unbranched_execute_request(tmp_path, verified):
    """The gate scores P_new from a branch: a copy of the workspace at plan review,
    resumed with --restore. That is valid only if the branch's EXECUTE request is
    byte-identical to the one the uninterrupted session sends."""
    from test_execution_profile import PredictingSys1, VerifiedPredictingSys1, _scripted_model

    from pdl_taskmaster.runtime.session_engine import SessionEngine

    sys1 = (VerifiedPredictingSys1({"WITHIN_100K_STEPS": 0.97, "WITHIN_10M_STEPS": 0.03}) if verified
            else PredictingSys1("WITHIN_10M_STEPS"))
    reply = {"kind": "RESULT", "body": "done"}
    trunk_executes: list = []
    replies = [reply] * 4  # verified mode repairs a witness-less reply; only the first request is compared
    engine = SessionEngine(ROOT, _scripted_model(list(replies), trunk_executes), workspace_root=tmp_path / "trunk",
                           sys1_client=sys1)
    for message in ("$confirm-with-pseudocode compute it", "/confirm"):
        engine.handle_user_message(message)
    branch_root = tmp_path / "branch"
    shutil.copytree(engine.workspace.path, branch_root / engine.workspace.path.name)

    engine.handle_user_message("/confirm")  # the uninterrupted session
    branch_executes: list = []
    resumed = SessionEngine.restore(ROOT, _scripted_model(list(replies), branch_executes),
                                    branch_root / engine.workspace.path.name, sys1_client=sys1)
    resumed.handle_user_message("/confirm")  # the branch
    assert len(trunk_executes) == len(branch_executes) >= 1
    for trunk_request, branch_request in zip(trunk_executes, branch_executes):  # repairs included
        assert branch_request.projection.document == trunk_request.projection.document
        assert branch_request.prompt == trunk_request.prompt


def _cost_row(item, arm, value, *, cluster=None, stratum="T", rep=1, tokens=(1000, 500), elapsed=10.0):
    return {"model": "m", "item_id": item, "cluster": cluster or item, "stratum": stratum, "rep": rep, "arm": arm,
            "scores": {"audited": value, "primary": value},
            "cost": {"calls": 1, "input_tokens": tokens[0], "output_tokens": tokens[1]}, "elapsed_s": elapsed}


def test_generated_items_from_one_template_are_one_unit():
    rows = [_cost_row("G-SS-01", "A", 1, cluster="gate-SS", stratum="G"), _cost_row("G-SS-02", "A", 0, cluster="gate-SS", stratum="G"),
            _cost_row("G-SS-03", "A", 1, cluster="gate-SS", stratum="G"), _cost_row("01-01", "A", 1)]
    units = analysis.per_item(rows, "m", "A", "audited", analysis.TASK_STRATA)
    assert units == {"gate-SS": pytest.approx(2 / 3), "01-01": 1.0}


def test_cost_per_correct_and_default_selection():
    prices = {"m": {"input_per_m": 1.0, "output_per_m": 2.0}}  # each run: 0.001 + 0.001 = $0.002
    cheap = [_cost_row(f"t{i}", "P_unc", 1 if i % 4 else 0, tokens=(1000, 500)) for i in range(20)]
    dear = [_cost_row(f"t{i}", "P_new", 1 if i % 4 else 0, tokens=(5000, 2500)) for i in range(20)]
    c_unc = analysis.cost_per_correct(cheap, "m", "P_unc", prices)
    c_new = analysis.cost_per_correct(dear, "m", "P_new", prices)
    assert c_unc["passes"] == 15 and c_unc["usd_per_correct"] == pytest.approx(0.04 / 15)
    assert c_new["usd_per_correct"] == pytest.approx(5 * c_unc["usd_per_correct"])
    pick = analysis.default_selection({"P_new": True, "P_unc": True}, {"P_new": c_new, "P_unc": c_unc})
    assert pick["default"] == "P_unc"
    assert analysis.default_selection({"P_new": True, "P_unc": False}, {"P_new": c_new, "P_unc": c_unc})["default"] == "P_new"
    assert analysis.default_selection({"P_new": False, "P_unc": False}, {})["default"] == "shipped"


def test_default_selection_tie_keeps_the_confirmation_route():
    near = {"usd_per_correct": 0.010, "ci95": [0.008, 0.012]}
    close = {"usd_per_correct": 0.0095, "ci95": [0.0075, 0.0115]}
    pick = analysis.default_selection({"P_new": True, "P_unc": True}, {"P_new": near, "P_unc": close})
    assert pick == {"default": "P_new", "offered_mode": "P_unc", "reason": "tie on cost per correct"}


def test_interaction_report_compares_on_its_own_stratum_only():
    rows = [_cost_row(f"a{i}", "P_rev", 1, stratum="A") for i in range(6)] + \
           [_cost_row(f"a{i}", "C0", 0, stratum="A") for i in range(6)] + [_cost_row("t1", "C0", 1)]
    report = analysis.interaction_report(rows, "m", "A", "P_rev", ["C0"])
    assert report["stratum"] == "ambiguity"
    assert report["comparisons"][0]["n"] == 6 and report["comparisons"][0]["mean_diff"] == 1.0


# --------------------------------------------------------------------------- interaction groups in the runner


def test_interaction_strata_run_their_own_arms():
    config = runner.load_config(ROOT / "experiments" / "gate_config.example.json")
    core = runner.arms_for(config, "T")
    assert "P_rev" not in core and "C0F" not in core and "P_M" not in core
    assert set(runner.arms_for(config, "A")) == {"P_rev", "C0", "C0F"}
    assert set(runner.arms_for(config, "M")) == {"P_M", "C0F"}
    blocks = schedule.build_schedule(["m"], ["01-01", "A-01"], reps=1, arms=core, seed=1,
                                     arms_by_item={"A-01": runner.arms_for(config, "A")})
    by_item = {b.item_id: set(b.arms) for b in blocks}
    assert by_item["A-01"] == {"P_rev", "C0", "C0F"} and by_item["01-01"] == set(core)


def test_old_protocol_branches_into_the_fb1_arm():
    config = runner.load_config(ROOT / "experiments" / "gate_config.example.json")
    p_old = config["arms"]["P_old"]
    assert p_old.kind == "branched" and set(p_old.branches) == {"P_old", "FB1"}
    assert p_old.branches["FB1"] == ("--api-reasoning-operation", "EXECUTE=medium")


def _judge_says(verdict):
    def send(spec, prompt):
        return json.dumps({"criteria": {"c1": "met" if verdict == "PASS" else "not_met",
                                        "c2": "met" if verdict == "PASS" else "not_met"}})
    return send


def test_scripted_reviewer_drives_the_protocol_through_its_gates(monkeypatch, tmp_path):
    from experiments import interaction, judge

    stages = iter(["PROMPT_REVIEW", "PROMPT_REVIEW", "PLAN_REVIEW", None])
    calls = []

    def fake_run_cli(spec, model, out, *, prompt_file, restore, stdin, extra_args, timeout, exit_on_close=True):
        calls.append(stdin)
        (out / "session" / "W-x").mkdir(parents=True, exist_ok=True)
        return {"exit_code": 2 if len(calls) < 4 else 0, "timed_out": False, "stderr": "", "harness_fault": None,
                "elapsed_s": 1.0}

    monkeypatch.setattr(runner, "run_cli", fake_run_cli)
    monkeypatch.setattr(runner, "controller_stage", lambda session: next(stages))
    monkeypatch.setattr(runner, "artifact_under_review", lambda session, stage: "COMPUTE the mean")
    item = interaction.ambiguity_items()["A-01"]
    specs = [judge.JudgeSpec("a", "m"), judge.JudgeSpec("b", "m")]
    spec = runner.ArmSpec("P_rev", "reviewed")
    run, log = runner.run_reviewed(spec, {"model": "m", "providers": []}, tmp_path, tmp_path / "p.txt", 60, item,
                                   specs, _judge_says("FAIL"))
    # Gate 1: the reading is wrong -> the correction; gate 2: still wrong -> confirmed (one revision per run).
    assert calls == ["", f"/revise {item.correction}\n", "/confirm\n", "/confirm\n"]
    assert [entry["reply"] for entry in log] == ["/revise", "/confirm", "/confirm"]
    assert run["exit_code"] == 0


class _FakeControls:
    def __init__(self, answers):
        self.answers, self.sent = list(answers), []

    def _reply(self, arm):
        from experiments.controls import ControlResult

        return ControlResult(arm, "reply", kind="RESULT", text=self.answers.pop(0), usage={"input_tokens": 10,
                                                                                            "output_tokens": 5})

    def run(self, arm, request, effort=None, **_):
        self.sent.append(request)
        return self._reply(arm)

    def run_conversation(self, arm, messages, effort=None):
        self.sent.append(messages)
        return self._reply(arm)


def test_plain_call_gets_the_correction_only_when_the_reading_was_wrong():
    from experiments import interaction, judge

    item = interaction.ambiguity_items()["A-08"]
    specs = [judge.JudgeSpec("a", "m"), judge.JudgeSpec("b", "m")]
    spec = runner.ArmSpec("C0F", "control_followup")
    right = _FakeControls(["65"])
    result, log = runner.run_control_followup(right, "C0F", spec, item.request, ambiguity_item=item,
                                              judge_specs=specs, send=_judge_says("PASS"))
    assert result.text == "65" and len(right.sent) == 1 and len(log) == 1
    wrong = _FakeControls(["70", "65"])
    result, log = runner.run_control_followup(wrong, "C0F", spec, item.request, ambiguity_item=item,
                                              judge_specs=specs, send=_judge_says("FAIL"))
    assert result.text == "65" and len(log) == 2
    assert wrong.sent[1][-1] == {"role": "user", "content": item.correction}


def test_multi_turn_plain_call_sends_every_scripted_followup():
    from experiments import interaction

    script = interaction.MULTI_TURN["10-04"]
    controls = _FakeControls(["v1", "v2", "v3", "v4"])
    result, log = runner.run_control_followup(controls, "C0F", runner.ArmSpec("C0F", "control_followup"),
                                              "Write an email validator.", script=script)
    assert result.text == "v4" and len(log) == 4
    assert [m["content"] for m in controls.sent[-1] if m["role"] == "user"][1:] == list(script.followups)
