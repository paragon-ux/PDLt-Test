"""DRAFT_EXECUTE's typed execution brief (LEDGER L93; ADR-0013 P6; EXECUTION_STANDARD EXEC-06).

The brief is a strict wire model, sent to the provider as its JSON schema, validated by the host, checked
mechanically (step arithmetic against the budget, entity grounding against the task), and passed to EXECUTE as
its own input. These tests run the real parser, compiler, engine and sandbox; only the model is scripted.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdl_taskmaster.controller.mechanical_controller import Stage
from pdl_taskmaster.providers.sys1.recipes.computation import COMPUTATIONAL, OTHER
from pdl_taskmaster.runtime.operation_bridge import OperationBridge, WireError
from pdl_taskmaster.runtime.output_contracts import ContractForm, grammar_schema
from pdl_taskmaster.runtime.session_engine import SessionEngine, _ground_execution_entities
from pdl_taskmaster.runtime.wire_payloads import ExecutionDraftResultData, ExecutionEntity

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = OperationBridge(ROOT)
PROMPT = "COMPUTE the sum of the values 3, 4, 5 with the function total_of\nRETURN the sum"
PLAN = "ADD the values\nEMIT the sum"
MINIMAL_LIMIT = 100_000  # the tier a WITHIN_100K_STEPS prediction routes to (sandbox.EXECUTION_BUDGETS)
FIELDS = ("approach", "data_structures", "step_estimate", "invariants", "self_checks", "execution_entities")


def _brief(**overrides) -> dict:
    brief = {
        "kind": "RESULT",
        "approach": "Add the three given values in one pass and print the sum.",
        "data_structures": ["a running total holding the partial sum"],
        "step_estimate": {"iterations": 3, "steps_per_iteration": 10, "basis": "one iteration per given value"},
        "invariants": ["the running total equals the sum of the values read so far"],
        "self_checks": ["compare the printed sum with 3 + 4 + 5 computed separately"],
        "execution_entities": [{"kind": "identifier", "value": "total_of"}, {"kind": "parameter", "value": "3, 4, 5"}],
    }
    brief.update(overrides)
    return brief


# --- schema and validation -------------------------------------------------------------------------------

def test_a_complete_brief_is_accepted_with_its_types():
    outcome = BRIDGE.parse_execution_draft(json.dumps(_brief()))
    assert outcome.kind == "RESULT" and isinstance(outcome.brief, ExecutionDraftResultData)
    assert outcome.brief.step_estimate.estimated_steps == 30
    assert [e.kind for e in outcome.brief.execution_entities] == ["identifier", "parameter"]


@pytest.mark.parametrize("field", FIELDS)
def test_every_field_is_required(field):
    reply = _brief()
    del reply[field]
    with pytest.raises(WireError):
        BRIDGE.parse_execution_draft(json.dumps(reply))


@pytest.mark.parametrize("field", ["approach", "data_structures", "invariants", "self_checks", "execution_entities"])
def test_null_does_not_stand_in_for_a_required_field(field):
    """Strict providers send null for a property that does not apply; only step_estimate may be null."""
    with pytest.raises(WireError):
        BRIDGE.parse_execution_draft(json.dumps(_brief(**{field: None})))


def test_empty_lists_and_a_null_step_estimate_are_explicit_answers():
    outcome = BRIDGE.parse_execution_draft(json.dumps(_brief(
        data_structures=[], step_estimate=None, invariants=[], self_checks=[], execution_entities=[])))
    assert outcome.brief.step_estimate is None and outcome.brief.execution_entities == []


@pytest.mark.parametrize("change", [
    {"approach": "   "},
    {"approach": 42},
    {"data_structures": "a list"},
    {"invariants": [""]},
    {"step_estimate": {"iterations": "many", "steps_per_iteration": 10, "basis": "b"}},
    {"step_estimate": {"iterations": 10, "steps_per_iteration": 0, "basis": "b"}},
    {"step_estimate": {"iterations": -1, "steps_per_iteration": 10, "basis": "b"}},
    {"step_estimate": {"iterations": 10, "steps_per_iteration": 10, "basis": " "}},
    {"step_estimate": {"iterations": 10, "steps_per_iteration": 10}},
    {"step_estimate": {"iterations": "5000", "steps_per_iteration": 10, "basis": "b"}},
    {"step_estimate": {"iterations": 5000.0, "steps_per_iteration": 10, "basis": "b"}},
    {"step_estimate": {"iterations": True, "steps_per_iteration": 10, "basis": "b"}},
    {"step_estimate": {"iterations": 10**31, "steps_per_iteration": 10, "basis": "b"}},
    {"execution_entities": ["total_of"]},
    {"execution_entities": [{"kind": "api_signature", "value": "total_of"}]},
    {"execution_entities": [{"kind": "identifier", "value": ""}]},
    {"execution_entities": [{"kind": "identifier"}]},
], ids=lambda change: json.dumps(change)[:60])
def test_wrong_types_and_empty_values_are_rejected(change):
    with pytest.raises(WireError):
        BRIDGE.parse_execution_draft(json.dumps(_brief(**change)))


@pytest.mark.parametrize("reply", [
    _brief(brief_body="a free-text brief next to the typed one"),
    _brief(step_estimate={"iterations": 3, "steps_per_iteration": 10, "basis": "b", "confidence": "high"}),
    _brief(execution_entities=[{"kind": "identifier", "value": "total_of", "name": "f"}]),
], ids=["top-level", "step_estimate", "entity"])
def test_undeclared_fields_are_rejected(reply):
    with pytest.raises(WireError) as caught:
        BRIDGE.parse_execution_draft(json.dumps(reply))
    assert caught.value.reason == "extra_fields"


@pytest.mark.parametrize("text", ["", "not json", '{"kind": "RESULT", "approach": ', "[1, 2]"])
def test_malformed_json_is_rejected(text):
    with pytest.raises(WireError):
        BRIDGE.parse_execution_draft(text)


def test_the_unrepaired_scratchpad_reply_does_not_pass_the_contract():
    """The reply shape 990610d3 accepted (free text, entities null) is refused, not passed on as a brief."""
    with pytest.raises(WireError):
        BRIDGE.parse_execution_draft(json.dumps({"kind": "RESULT", "brief_body": "Feasibility looks fine.",
                                                 "execution_entities": None}))


def test_a_blocked_reply_carries_its_reason_and_no_brief():
    outcome = BRIDGE.parse_execution_draft(json.dumps({"kind": "BLOCKED_BY_HIGHER_PRIORITY", "brief_body": "Policy."}))
    assert outcome.kind == "BLOCKED_BY_HIGHER_PRIORITY" and outcome.brief is None and outcome.blocked_reason == "Policy."


def test_a_validated_brief_round_trips():
    brief = ExecutionDraftResultData.model_validate(_brief())
    again = ExecutionDraftResultData.model_validate_json(brief.model_dump_json())
    assert again == brief and again.step_estimate.estimated_steps == 30


# --- the schema the provider receives ---------------------------------------------------------------------

@pytest.mark.parametrize("strict", [False, True], ids=["default", "strict-all-required"])
def test_the_grammar_requires_every_field_and_closes_every_object(strict):
    form = ContractForm(grammar="schema", strict_all_required=strict, free_form_objects=False)
    schema = grammar_schema("DRAFT_EXECUTE", form)
    result = next(b for b in schema["properties"]["outcome"]["anyOf"] if "approach" in b["properties"])
    assert set(result["required"]) == {"kind", *FIELDS} and result["additionalProperties"] is False
    props = result["properties"]
    assert {b.get("type") for b in props["step_estimate"]["anyOf"]} == {"object", "null"}
    assert props["execution_entities"]["type"] == "array"  # never nullable, unlike under 990610d3
    entity = props["execution_entities"]["items"]
    assert entity["additionalProperties"] is False and set(entity["required"]) == {"kind", "value"}
    assert entity["properties"]["kind"]["enum"] == ["identifier", "literal", "parameter"]
    estimate = next(b for b in props["step_estimate"]["anyOf"] if b.get("type") == "object")
    assert set(estimate["required"]) == {"iterations", "steps_per_iteration", "basis"}
    assert estimate["additionalProperties"] is False


@pytest.mark.parametrize("pinning", [{"order": ["Cerebras"], "allow_fallbacks": False},
                                     {"order": ["Baseten", "Crusoe"], "allow_fallbacks": True}],
                         ids=["cerebras", "baseten"])
def test_the_provider_request_carries_the_generated_schema(monkeypatch, pinning):
    from pdl_taskmaster.providers.api_worker import ApiWorker

    sent: dict = {}

    class _Stop(Exception):
        pass

    def fake_send(self, req, deadline=None):
        sent.update(json.loads(req.data))
        raise _Stop

    monkeypatch.setattr(ApiWorker, "_send_json_with_retries", fake_send)
    monkeypatch.setattr(ApiWorker, "_resolve_api_key", lambda self: "k")
    worker = ApiWorker(model="openai/gpt-oss-120b", repo_root=ROOT, provider_pinning=pinning)
    spec = BRIDGE.compiler.execution_contract["operations"]["DRAFT_EXECUTE"]
    inputs = {symbol: "x" for symbol in spec["include"] if symbol not in
              ("OPERATION_ID", "APPLICABLE_STANDARD_CLAUSES", "HIGHER_PRIORITY_CONSTRAINTS")}
    projection = BRIDGE.compiler.compile("DRAFT_EXECUTE", inputs, contract_form=worker.contract_form("DRAFT_EXECUTE"))

    class _Req:
        operation = "DRAFT_EXECUTE"
        prompt = "Draft the execution brief."
        manifest = projection.manifest

    _Req.projection = projection
    with pytest.raises(_Stop):
        worker.call(_Req())
    response_format = sent["text"]["format"]
    assert response_format["type"] == "json_schema"
    assert response_format["schema"] == grammar_schema("DRAFT_EXECUTE", worker.contract_form("DRAFT_EXECUTE"))


# --- host checks ------------------------------------------------------------------------------------------

def test_entities_not_found_verbatim_in_the_task_are_dropped():
    entities = [ExecutionEntity(kind="identifier", value="total_of"),
                ExecutionEntity(kind="identifier", value="`total_of`"),
                ExecutionEntity(kind="literal", value="Sum:   3,\n 4"),
                ExecutionEntity(kind="literal", value="Sum: 3,  4 and"),
                ExecutionEntity(kind="identifier", value="sum_values"),
                ExecutionEntity(kind="identifier", value="Total_Of"),
                ExecutionEntity(kind="identifier", value="total"),
                ExecutionEntity(kind="literal", value="5. Then"),
                ExecutionEntity(kind="parameter", value="7, 8")]
    kept, dropped = _ground_execution_entities(
        entities, ["Write total_of; print Sum: 3, 4 and 5.", None, "Then use 7, 8 as given."])
    assert kept == [{"kind": "identifier", "value": "total_of"}, {"kind": "literal", "value": "Sum: 3, 4"},
                    {"kind": "literal", "value": "Sum: 3, 4 and"}, {"kind": "parameter", "value": "7, 8"}]
    # names are case-sensitive, a fragment of a longer name is not that name, invented values never pass,
    # and a span is never stitched across two task texts
    assert dropped == ["sum_values", "Total_Of", "total", "5. Then"]


class Sys1:
    """Answers each System 1 question by name: the problem class, a MINIMAL-tier step prediction, and the
    computation question."""

    is_configured = True
    model = "fake-sys1"

    def __init__(self, problem_class: str = "STANDARD_EXECUTION", computational: bool = True):
        self.problem_class, self.computational = problem_class, computational
        self.asked: list[str] = []

    def call(self, request):
        name = next(iter(request.questions))
        self.asked.append(name)
        choice, other = {
            "route": ("APPLY_PROTOCOL", "BYPASS"),
            "execution_profile": ("WITHIN_100K_STEPS", "WITHIN_10M_STEPS"),
            "computation": (COMPUTATIONAL, OTHER) if self.computational else (OTHER, COMPUTATIONAL),
        }.get(name, (self.problem_class,
                     "STANDARD_EXECUTION" if self.problem_class == "VERIFIED_EXECUTION" else "VERIFIED_EXECUTION"))
        return {"answers": {name: {"choice": choice, "confidence": 0.97,
                                   "probabilities": {choice: 0.97, other: 0.03}}}}, 1.0


PRINTS = "```python\nprint(3 + 4 + 5)\n```"
LOOPS = "```python\nwhile True:\n    pass\n```"
# A verified task (ADR-0013) closes on a sandbox witness; a step-budget overrun there is a repair finding.
WITNESS = "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'sum': 12}}))"
VERIFIED = "VERIFIED_EXECUTION"


def _confirmed(tmp_path, briefs: list, executes: list[str], *, draft_execute: bool = True, sys1: Sys1 | None = None,
               request: str = "Sum the values 3, 4, 5 with a function total_of."):
    """A confirmed session whose DRAFT_EXECUTE and EXECUTE replies are scripted (a brief may be raw text)."""
    calls: list = []
    briefs, executes = list(briefs), list(executes)

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "Sum the values 3, 4, 5 with total_of.",
                               "approach_notes": "", "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": PROMPT, "approach_handoff": "NONE"})
        if req.operation == "DRAFT_PLAN":
            return json.dumps({"neutral_plan_body": PLAN})
        if req.operation == "DRAFT_EXECUTE":
            reply = briefs.pop(0)
            return reply if isinstance(reply, str) else json.dumps(reply)
        if req.operation == "EXECUTE":
            return json.dumps({"kind": "RESULT", "body": executes.pop(0), "result_ir": {}})
        raise AssertionError(f"unexpected operation {req.operation}")

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=sys1 or Sys1())
    engine.draft_execute = draft_execute
    engine.tier_d1 = True  # the shipped default (L83)
    for message in ("$confirm-with-pseudocode " + request, "/confirm", "/confirm"):
        engine.handle_user_message(message)
    events = list(engine.workspace.read_events())
    return engine, calls, events


def _ops(calls):
    return [c.operation for c in calls]


def _inputs(call) -> dict:
    return call.projection.document["operation_inputs"]


def _clauses(call) -> list[str]:
    return [c["requirement_id"] for c in _inputs(call)["APPLICABLE_STANDARD_CLAUSES"]]


def _event(events, kind):
    return [e["payload"] for e in events if e["kind"] == kind]


# --- integration: what EXECUTE receives -------------------------------------------------------------------

def test_the_validated_brief_reaches_execute_as_its_own_input_under_exec06(tmp_path):
    engine, calls, events = _confirmed(tmp_path, [_brief()], [PRINTS])
    assert _ops(calls)[-2:] == ["DRAFT_EXECUTE", "EXECUTE"]
    execute = calls[-1]
    brief = _inputs(execute)["EXECUTION_BRIEF"]
    assert brief["approach"] == _brief()["approach"]
    assert brief["step_estimate"] == {"iterations": 3, "steps_per_iteration": 10, "estimated_steps": 30,
                                      "step_limit": MINIMAL_LIMIT, "basis": "one iteration per given value"}
    assert brief["execution_entities"] == _brief()["execution_entities"]
    assert "EXEC-06" in _clauses(execute)
    assert "DRAFT_EXECUTE" not in (_inputs(execute).get("REQUIRED_TASK_INPUTS") or {})
    drafted = _event(events, "EXECUTION_BRIEF_DRAFTED")[0]
    assert drafted["estimated_steps"] == 30 and drafted["entities_kept"] == 2 and drafted["entities_dropped"] == 0
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_an_invented_entity_never_reaches_execute(tmp_path):
    reply = _brief(execution_entities=[{"kind": "identifier", "value": "total_of"},
                                       {"kind": "identifier", "value": "compute_everything"}])
    _, calls, events = _confirmed(tmp_path, [reply], [PRINTS])
    assert _inputs(calls[-1])["EXECUTION_BRIEF"]["execution_entities"] == [{"kind": "identifier", "value": "total_of"}]
    assert _event(events, "EXECUTION_ENTITY_DROPPED_UNGROUNDED") == [{"count": 1, "values": ["compute_everything"]}]


def test_without_the_flag_there_is_no_brief_call_input_or_clause(tmp_path):
    """No DRAFT_EXECUTE call, no System 1 computation question, no EXECUTION_BRIEF input and no EXEC-06
    clause. (That such a request matches 83fd0b40's byte for byte was checked across checkouts: LEDGER L93.)"""
    sys1 = Sys1()
    _, calls, events = _confirmed(tmp_path, [], [PRINTS], draft_execute=False, sys1=sys1)
    assert "DRAFT_EXECUTE" not in _ops(calls) and "computation" not in sys1.asked
    execute = calls[-1]
    assert "EXECUTION_BRIEF" not in _inputs(execute) and "EXEC-06" not in _clauses(execute)
    assert not _event(events, "COMPUTATION_CLASSIFIED")


def test_a_brief_not_wanted_leaves_execute_identical_to_the_route_without_the_flag(tmp_path):
    _, without, _ = _confirmed(tmp_path / "a", [], [PRINTS], draft_execute=False, sys1=Sys1(computational=False))
    _, unwanted, events = _confirmed(tmp_path / "b", [], [PRINTS], draft_execute=True, sys1=Sys1(computational=False))
    assert "DRAFT_EXECUTE" not in _ops(unwanted)
    assert _event(events, "COMPUTATION_CLASSIFIED")[0]["computational"] is False
    assert unwanted[-1].prompt == without[-1].prompt


@pytest.mark.parametrize("problem_class, computational, drafted", [
    ("VERIFIED_EXECUTION", False, True),
    ("STANDARD_EXECUTION", True, True),
    ("STANDARD_EXECUTION", False, False),
])
def test_the_gate_follows_adr_0013_p6(tmp_path, problem_class, computational, drafted):
    """Verified execution always gets a brief; any other task only on System 1's confident 'computational'."""
    sys1 = Sys1(problem_class, computational)
    executes = [WITNESS] if problem_class == VERIFIED else [PRINTS]
    _, calls, _ = _confirmed(tmp_path, [_brief()], executes, sys1=sys1)
    assert ("DRAFT_EXECUTE" in _ops(calls)) is drafted
    assert ("computation" in sys1.asked) is (problem_class != "VERIFIED_EXECUTION")


def test_an_invalid_brief_is_retried_once_then_skipped_and_never_reaches_execute(tmp_path):
    bad = json.dumps({"kind": "RESULT", "brief_body": "free text", "execution_entities": None})
    engine, calls, events = _confirmed(tmp_path, [bad, bad], [PRINTS])
    assert _ops(calls).count("DRAFT_EXECUTE") == 2  # the wire retry, then no more
    assert "OPERATOR CORRECTION" in calls[_ops(calls).index("DRAFT_EXECUTE") + 1].prompt
    skipped = _event(events, "EXECUTION_BRIEF_SKIPPED")
    assert len(skipped) == 1 and skipped[0]["reason"] and skipped[0]["feedback"]
    execute = calls[-1]
    assert "EXECUTION_BRIEF" not in _inputs(execute) and "EXEC-06" not in _clauses(execute)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_a_brief_over_the_step_budget_is_redrafted_once_with_the_fact(tmp_path):
    over = _brief(step_estimate={"iterations": 10**9, "steps_per_iteration": 20, "basis": "every subset of the inputs"})
    _, calls, events = _confirmed(tmp_path, [over, _brief()], [PRINTS])
    drafts = [c for c in calls if c.operation == "DRAFT_EXECUTE"]
    assert len(drafts) == 2
    assert "20,000,000,000 steps" in drafts[1].prompt and f"{MINIMAL_LIMIT:,} steps" in drafts[1].prompt
    assert _event(events, "EXECUTION_BRIEF_STEP_CHECK_FAILED") == [
        {"reason": "step_estimate_over_budget", "estimated_steps": 20 * 10**9, "step_limit": MINIMAL_LIMIT}]
    assert _inputs(calls[-1])["EXECUTION_BRIEF"]["step_estimate"]["estimated_steps"] == 30


def test_a_brief_that_stays_over_the_budget_is_rejected_not_followed(tmp_path):
    over = _brief(step_estimate={"iterations": 10**9, "steps_per_iteration": 20, "basis": "every subset"})
    _, calls, events = _confirmed(tmp_path, [over, over], [PRINTS])
    assert _ops(calls).count("DRAFT_EXECUTE") == 2
    assert _event(events, "EXECUTION_BRIEF_REJECTED")[0]["reason"] == "step_estimate_over_budget"
    assert "EXECUTION_BRIEF" not in _inputs(calls[-1]) and "EXEC-06" not in _clauses(calls[-1])


def test_a_run_stopped_at_the_step_budget_withdraws_the_brief_it_contradicts(tmp_path):
    """The brief estimated 30 steps; the sandbox stopped the program at the budget. The repair runs without
    the brief, and its correction states the contradiction (a host finding, no method)."""
    engine, calls, events = _confirmed(tmp_path, [_brief()], [LOOPS, WITNESS], sys1=Sys1(VERIFIED))
    first, repair = [c for c in calls if c.operation == "EXECUTE"]
    assert "EXECUTION_BRIEF" in _inputs(first)
    assert "EXECUTION_BRIEF" not in _inputs(repair) and "EXEC-06" not in _clauses(repair)
    assert "STEP_BUDGET_EXCEEDED" in repair.prompt and "the brief is withdrawn" in repair.prompt
    assert _event(events, "EXECUTION_BRIEF_WITHDRAWN") == [
        {"reason": "STEP_BUDGET_EXCEEDED", "estimated_steps": 30, "step_limit": MINIMAL_LIMIT}]
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_a_failure_that_does_not_contradict_the_brief_keeps_it_for_the_repair(tmp_path):
    fails = "```python\nimport sys\nsys.exit(1)\n```"
    _, calls, events = _confirmed(tmp_path, [_brief()], [fails, WITNESS], sys1=Sys1(VERIFIED))
    first, repair = [c for c in calls if c.operation == "EXECUTE"]
    assert _inputs(repair)["EXECUTION_BRIEF"] == _inputs(first)["EXECUTION_BRIEF"]
    assert not _event(events, "EXECUTION_BRIEF_WITHDRAWN")


# --- the unconfirmed route --------------------------------------------------------------------------------

def _unconfirmed(tmp_path, briefs: list, bodies: list[str]):
    calls: list = []
    briefs, bodies = list(briefs), list(bodies)

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "Sum the values 3, 4, 5 with total_of.",
                               "approach_notes": "", "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_EXECUTE":
            return json.dumps(briefs.pop(0))
        if req.operation == "EXECUTE_UNCONFIRMED":
            return json.dumps({"kind": "RESULT", "interpretation": "SUM the values", "approach": "ADD the values",
                               "body": bodies.pop(0), "result_ir": {}})
        raise AssertionError(f"unexpected operation {req.operation}")

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=Sys1(VERIFIED), no_review=True)
    engine.draft_execute = True
    engine.tier_d1 = True
    engine.handle_user_message("Sum the values 3, 4, 5 with a function total_of.")
    return engine, calls, list(engine.workspace.read_events())


def test_the_unconfirmed_route_receives_the_same_brief_and_withdraws_it_the_same_way(tmp_path):
    engine, calls, events = _unconfirmed(tmp_path, [_brief()], [LOOPS, WITNESS])
    assert _ops(calls) == ["BOOTSTRAP_ANALYSIS", "DRAFT_EXECUTE", "EXECUTE_UNCONFIRMED", "EXECUTE_UNCONFIRMED"]
    first, repair = calls[2], calls[3]
    assert _inputs(first)["EXECUTION_BRIEF"]["execution_entities"] == _brief()["execution_entities"]
    assert "EXEC-06" in _clauses(first)
    assert "EXECUTION_BRIEF" not in _inputs(repair) and "the brief is withdrawn" in repair.prompt
    assert _event(events, "EXECUTION_BRIEF_WITHDRAWN")[0]["estimated_steps"] == 30
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


# --- regressions from the recorded runs (tests/fixtures/draft_execute/recorded.json) ----------------------

RECORDED = json.loads((ROOT / "tests" / "fixtures" / "draft_execute" / "recorded.json").read_text(encoding="utf-8"))


def _catalogue_prompt(relative: str) -> str:
    return (ROOT / "prompts" / relative).read_text(encoding="utf-8-sig").strip()


@pytest.mark.parametrize("key", ["l92_01_01", "l92_04_01", "baseline_01_01"])
def test_recorded_briefs_of_both_earlier_implementations_do_not_pass_as_a_typed_brief(key):
    """The free-text scratchpad (990610d3) and the free-text brief with unchecked entity kinds (83fd0b40)
    cannot reach EXECUTE under the typed contract."""
    with pytest.raises(WireError):
        BRIDGE.parse_execution_draft(RECORDED[key]["draft_execute"]["reply"])


def test_01_01_the_recorded_overrunning_program_withdraws_a_brief_that_claimed_a_few_thousand_states(tmp_path):
    """L92 Arm 4, 01-01: the scratchpad said the search visits 'at most a few thousand recursive states', and the
    program was stopped at the step budget twice. Here the same program runs (at the MINIMAL tier, so it overruns
    in well under a second); the brief that claimed a small count is withdrawn, and the repair closes the task.
    This is also the confirmed-route path L92 credited to the brief (Arm 3 01-01 passed after a repair)."""
    request = _catalogue_prompt("01_combinatorial_search/schur_triples_n15.txt")
    claimed = _brief(
        approach="Search the valid triples for an exact cover of the list, one triple at a time.",
        step_estimate={"iterations": 5000, "steps_per_iteration": 20, "basis": "a few thousand recursive states"},
        execution_entities=[{"kind": "parameter", "value": "N=15"},
                            {"kind": "literal", "value": "15 disjoint triples"},
                            {"kind": "identifier", "value": "find_partition"}])
    overrun = RECORDED["l92_01_01"]["execute_bodies"][0]["body"]
    engine, calls, events = _confirmed(tmp_path, [claimed], [overrun, WITNESS], sys1=Sys1(VERIFIED), request=request)
    first, repair = [c for c in calls if c.operation == "EXECUTE"]
    assert _inputs(first)["EXECUTION_BRIEF"]["execution_entities"] == [
        {"kind": "parameter", "value": "N=15"}, {"kind": "literal", "value": "15 disjoint triples"}]
    assert _event(events, "EXECUTION_ENTITY_DROPPED_UNGROUNDED")[0]["values"] == ["find_partition"]
    run = next(e["payload"] for e in events if e["kind"] == "SANDBOX_RUN")
    assert run["step_budget_exceeded"]
    assert "EXECUTION_BRIEF" not in _inputs(repair)
    assert _event(events, "EXECUTION_BRIEF_WITHDRAWN")[0]["estimated_steps"] == 100_000
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_01_01_the_naive_count_is_caught_before_any_code_runs(tmp_path):
    """A brief that counts the naive search honestly is over the budget: the host says so once, and a brief
    that still does not fit is rejected rather than passed to EXECUTE."""
    request = _catalogue_prompt("01_combinatorial_search/schur_triples_n15.txt")
    naive = _brief(step_estimate={"iterations": 10**30, "steps_per_iteration": 50,
                                  "basis": "every assignment of the 45 values to 15 groups"},
                   execution_entities=[])
    _, calls, events = _confirmed(tmp_path, [naive, naive], [WITNESS], sys1=Sys1(VERIFIED), request=request)
    assert _ops(calls).count("DRAFT_EXECUTE") == 2
    assert _event(events, "EXECUTION_BRIEF_REJECTED")[0]["estimated_steps"] == 50 * 10**30
    assert "EXECUTION_BRIEF" not in _inputs(calls[-1])


def test_04_01_an_error_message_the_task_never_states_is_not_imposed_on_execute(tmp_path):
    """L92 Arm 4, 04-01: the program's own test expected the message 'Expected NUMBER', which its parser never
    raised. The task names no message, so a brief that commits to one as an exact string is not passed on as
    something EXECUTE must reproduce verbatim; strings the task does state are."""
    request = _catalogue_prompt("04_parsers_and_compilers/recursive_descent_calc.txt")
    brief = _brief(step_estimate={"iterations": 200, "steps_per_iteration": 30, "basis": "a few short test inputs"},
                   execution_entities=[{"kind": "literal", "value": "Expected NUMBER"},
                                       {"kind": "literal", "value": "\"3 + 4 * 2\" = 11"},
                                       {"kind": "parameter", "value": "at least 3 error cases"}])
    failing = RECORDED["l92_04_01"]["execute_bodies"][0]["body"]
    engine, calls, events = _confirmed(tmp_path, [brief], [failing, PRINTS], request=request)
    first = next(c for c in calls if c.operation == "EXECUTE")
    assert _inputs(first)["EXECUTION_BRIEF"]["execution_entities"] == [
        {"kind": "literal", "value": "\"3 + 4 * 2\" = 11"}, {"kind": "parameter", "value": "at least 3 error cases"}]
    assert _event(events, "EXECUTION_ENTITY_DROPPED_UNGROUNDED")[0]["values"] == ["Expected NUMBER"]
    # The recorded program still fails its own test in the sandbox: a program defect, not one the brief
    # contradicts, so the brief stays for the repair (Tier D1 feeds the failure back).
    run = next(e["payload"] for e in events if e["kind"] == "SANDBOX_RUN")
    assert run["exit_code"] == 1 and not run["step_budget_exceeded"]
    repair = [c for c in calls if c.operation == "EXECUTE"][1]
    assert "AssertionError" in repair.prompt and "EXECUTION_BRIEF" in _inputs(repair)
    assert engine.controller.state.stage == Stage.CLOSED_SUCCESS


# --- review fixes (LEDGER L93) ----------------------------------------------------------------------------

def test_a_verified_task_cannot_skip_the_count_with_a_null_estimate(tmp_path):
    """The step check had a way around it: null. A verified task's result comes from a program the sandbox
    runs, so a null estimate gets the one re-draft, and a second null is rejected, not passed on."""
    _, calls, events = _confirmed(tmp_path, [_brief(step_estimate=None)] * 2, [WITNESS], sys1=Sys1(VERIFIED))
    drafts = [c for c in calls if c.operation == "DRAFT_EXECUTE"]
    assert len(drafts) == 2 and "step_estimate is null" in drafts[1].prompt
    assert _event(events, "EXECUTION_BRIEF_REJECTED")[0]["reason"] == "step_estimate_missing"
    assert "EXECUTION_BRIEF" not in _inputs(calls[-1])


def test_an_over_budget_brief_cannot_escape_the_check_by_answering_null(tmp_path):
    over = _brief(step_estimate={"iterations": 10**9, "steps_per_iteration": 20, "basis": "every subset"})
    _, calls, events = _confirmed(tmp_path, [over, _brief(step_estimate=None)], [WITNESS], sys1=Sys1(VERIFIED))
    assert _event(events, "EXECUTION_BRIEF_REJECTED")[0]["reason"] == "step_estimate_missing"
    assert "EXECUTION_BRIEF" not in _inputs(calls[-1])


def test_a_task_without_verified_execution_may_answer_without_a_program(tmp_path):
    _, calls, events = _confirmed(tmp_path, [_brief(step_estimate=None)], [PRINTS])
    assert _ops(calls).count("DRAFT_EXECUTE") == 1 and not _event(events, "EXECUTION_BRIEF_STEP_CHECK_FAILED")
    assert _inputs(calls[-1])["EXECUTION_BRIEF"]["step_estimate"] is None


@pytest.mark.parametrize("code, facts, words", [
    ("WALL_CLOCK_EXCEEDED", {"block": 1, "timeout_seconds": 30.0}, "wall-clock limit"),
    ("MEMORY_EXCEEDED", {"block": 1, "memory_mb": 256}, "memory limit"),
    ("STEP_BUDGET_EXCEEDED", {"block": 1, "step_limit": 100_000}, "step budget"),
])
def test_any_resource_stop_withdraws_the_brief(tmp_path, code, facts, words):
    from pdl_taskmaster.verification.error_registry import Finding

    engine = SessionEngine(ROOT, lambda r: "", workspace_root=tmp_path, sys1_client=None)
    engine.workspace = engine._new_workspace()
    brief = {"step_estimate": {"estimated_steps": 30, "step_limit": MINIMAL_LIMIT}}
    context = {"EXECUTION_BRIEF": brief}
    line = engine._withdraw_brief_on_overrun(context, [Finding(code, **facts)])
    assert "EXECUTION_BRIEF" not in context and words in line and "withdrawn" in line
    payload = [e["payload"] for e in engine.workspace.read_events() if e["kind"] == "EXECUTION_BRIEF_WITHDRAWN"]
    assert payload == [{"reason": code, "estimated_steps": 30, "step_limit": MINIMAL_LIMIT}]


def test_a_failure_that_is_no_resource_stop_leaves_the_brief(tmp_path):
    from pdl_taskmaster.verification.error_registry import Finding

    engine = SessionEngine(ROOT, lambda r: "", workspace_root=tmp_path, sys1_client=None)
    engine.workspace = engine._new_workspace()
    context = {"EXECUTION_BRIEF": {"step_estimate": None}}
    failed = Finding("PROGRAM_FAILED", block=1, exit_code=1, stderr="")
    assert engine._withdraw_brief_on_overrun(context, [failed, "an unregistered note"]) == ""
    assert "EXECUTION_BRIEF" in context


def test_a_brief_cut_off_at_the_output_cap_is_skipped_not_a_harness_error(tmp_path):
    class Capped(RuntimeError):
        output_limit = 16384

    calls: list = []

    def model_call(req):
        calls.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "Sum 3, 4, 5.", "approach_notes": "",
                               "risk_notes": "", "task_entities": []})
        if req.operation == "DRAFT_PROMPT":
            return json.dumps({"kind": "PROMPT", "prompt_body": PROMPT, "approach_handoff": "NONE"})
        if req.operation == "DRAFT_PLAN":
            return json.dumps({"neutral_plan_body": PLAN})
        if req.operation == "DRAFT_EXECUTE":
            raise Capped("output cap")
        return json.dumps({"kind": "RESULT", "body": PRINTS})

    engine = SessionEngine(ROOT, model_call, workspace_root=tmp_path, sys1_client=Sys1())
    engine.draft_execute = True
    for message in ("$confirm-with-pseudocode Sum the values 3, 4, 5 with a function total_of.", "/confirm", "/confirm"):
        engine.handle_user_message(message)
    events = list(engine.workspace.read_events())
    assert _event(events, "EXECUTION_BRIEF_SKIPPED")[0]["reason"] == "output_limit"
    assert "EXECUTION_BRIEF" not in _inputs(calls[-1]) and engine.controller.state.stage == Stage.CLOSED_SUCCESS


def test_entities_are_grounded_in_input_the_user_supplied_to_the_task(tmp_path):
    """REQUIRED_TASK_INPUTS (supplied input, a prior deliverable) is task text DRAFT_EXECUTE is shown."""
    kept, dropped = _ground_execution_entities(
        [ExecutionEntity(kind="identifier", value="merge_rows")], ["Fix the function.", {"x": 1}, "def merge_rows(a):"])
    assert kept == [{"kind": "identifier", "value": "merge_rows"}] and dropped == []
