"""The representation switch (ledger L97): the confirmed route's prompt and plan artifacts as PDL
(the default) or as natural-language prose, for the PDL-versus-natural-language pilot.

The natural-language arm may differ from the PDL arm only in the artifacts' format rules and
names: no notation clause, the artifacts named as prose, the same output grammar, and an
EXECUTE that differs only in the artifact names inside AUTH-03.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "src", ROOT / "tests"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import run_catalogue  # noqa: E402
import test_reasoning_wire as wire  # noqa: E402
from pdl_taskmaster.host import repl  # noqa: E402
from pdl_taskmaster.providers.api_worker import _PLAN_GUIDANCE, _PROMPT_GUIDANCE  # noqa: E402
from pdl_taskmaster.providers.sys1.recipes.prompt_fidelity import PromptFidelityRecipe  # noqa: E402
from pdl_taskmaster.runtime.context_compiler import ContextCompiler  # noqa: E402
from pdl_taskmaster.runtime.output_contracts import (  # noqa: E402
    DEFAULT_FORM,
    NL_REPRESENTATION_MODE,
    ContractForm,
    grammar_schema,
)
from pdl_taskmaster.runtime.representation import nl_plan_guidance, nl_prompt_guidance, nl_terms  # noqa: E402
from pdl_taskmaster.runtime.session_engine import SessionEngine  # noqa: E402
from pdl_taskmaster.verification.plan_soundness import line_violations, validate_plan_soundness  # noqa: E402

NL = frozenset({NL_REPRESENTATION_MODE})
PDL_WORDS = re.compile(r"(?i)pseudocode|\bPDL\b|PDL-0\d")
# The one sentence of each NL format rule that names what not to write.
FORMAT_RULE_MENTIONS = re.compile(r"(?i)do not express (?:it|the plan) as pseudocode")
VALUES = {
    "BOOTSTRAP_ANALYSIS": {"HOST_PROTOCOL_STATE": "SEMANTIC_READ", "RAW_UNTRUSTED_CONTENT": "Sum the list."},
    "DRAFT_PROMPT": {"HOST_PROTOCOL_STATE": "ACTIVE_BY_EXPLICIT_INVOCATION", "SUBSTANTIVE_REQUEST": "Sum the list."},
    "DRAFT_PLAN": {"CONFIRMED_PROMPT_BODY": "Sum the list.", "CARRIED_APPROACH_SOURCES": []},
    "EXECUTE": {"CONFIRMED_PROMPT_BODY": "Sum the list.", "CONFIRMED_PLAN_BODY": "Add each item.",
                "SUPPLIED_EXECUTION_INPUT_SOURCE": "Sum the list.", "AVAILABLE_EXECUTION_TOOLS": "python"},
}
OPS = tuple(VALUES)
CEREBRAS_FORM = ContractForm(strict_all_required=True, free_form_objects=False)


def _doc(operation: str, modes: frozenset[str] = frozenset()) -> dict:
    return ContextCompiler(ROOT).compile(operation, VALUES[operation], modes=modes).document


def _clause_ids(document: dict) -> list[str]:
    return [c["requirement_id"] for c in document["operation_inputs"]["APPLICABLE_STANDARD_CLAUSES"]]


@pytest.mark.parametrize("operation", (*OPS, "REVISE_PROMPT", "REVISE_PLAN", "EXECUTE_UNCONFIRMED"))
@pytest.mark.parametrize("form", (DEFAULT_FORM, CEREBRAS_FORM))
def test_the_output_grammar_is_the_same_in_both_arms(operation, form) -> None:
    assert grammar_schema(operation, form, frozenset()) == grammar_schema(operation, form, NL)


@pytest.mark.parametrize("operation", OPS)
def test_the_nl_arm_shows_no_notation_clause_and_no_pseudocode_name(operation) -> None:
    document = _doc(operation, NL)
    assert not [rid for rid in _clause_ids(document) if rid.startswith("PDL-")]
    assert not PDL_WORDS.search(json.dumps(document, ensure_ascii=False))


@pytest.mark.parametrize("operation", OPS)
def test_the_nl_arm_differs_only_in_artifact_names_and_notation_clauses(operation) -> None:
    expected = json.loads(nl_terms(json.dumps(_doc(operation), ensure_ascii=False)))
    clauses = expected["operation_inputs"]["APPLICABLE_STANDARD_CLAUSES"]
    expected["operation_inputs"]["APPLICABLE_STANDARD_CLAUSES"] = [
        c for c in clauses if not c["requirement_id"].startswith("PDL-")]
    assert _doc(operation, NL) == expected


def test_execute_differs_only_in_the_artifact_names_inside_auth_03() -> None:
    pdl, nl = _doc("EXECUTE"), _doc("EXECUTE", NL)
    assert pdl["output_schema"] == nl["output_schema"]
    changed = {a["requirement_id"]
               for a, b in zip(pdl["operation_inputs"]["APPLICABLE_STANDARD_CLAUSES"],
                               nl["operation_inputs"]["APPLICABLE_STANDARD_CLAUSES"]) if a != b}
    assert changed == {"AUTH-03"}
    assert {k: v for k, v in pdl["operation_inputs"].items() if k != "APPLICABLE_STANDARD_CLAUSES"} == \
        {k: v for k, v in nl["operation_inputs"].items() if k != "APPLICABLE_STANDARD_CLAUSES"}


def test_the_nl_prompt_guidance_keeps_every_prompt_rule_and_drops_the_notation_rules() -> None:
    guidance = nl_prompt_guidance(_PROMPT_GUIDANCE)
    rules = [line for line in _PROMPT_GUIDANCE.split("\n") if line.startswith("PROMPT-")]
    assert len(rules) == 5 and all(nl_terms(rule) in guidance for rule in rules)
    assert not re.search(r"\bPDL\b|PDL-0\d", guidance)
    assert len(PDL_WORDS.findall(guidance)) == len(FORMAT_RULE_MENTIONS.findall(guidance)) == 1
    # The format-neutral content rule (operational guideline 7) is kept, renamed.
    seventh = next(line for line in _PROMPT_GUIDANCE.split("\n") if line.startswith("7. "))
    assert "Zero Execution Prohibitions" in seventh and "5. Zero Execution Prohibitions" in guidance


def test_the_nl_plan_guidance_keeps_every_plan_rule_and_the_neutral_operational_rules() -> None:
    guidance = nl_plan_guidance(_PLAN_GUIDANCE)
    rules = [line for line in _PLAN_GUIDANCE.split("\n") if line.startswith("PLAN-")]
    assert len(rules) == 9 and all(nl_terms(rule) in guidance for rule in rules)
    for number in ("3. ", "4. "):
        kept = next(line for line in _PLAN_GUIDANCE.split("\n") if line.startswith(number))
        assert kept[len(number):] in guidance
    assert not re.search(r"\bPDL\b|PDL-0\d", guidance)
    assert len(PDL_WORDS.findall(guidance)) == len(FORMAT_RULE_MENTIONS.findall(guidance)) == 1


def test_a_session_in_the_nl_arm_sends_prose_instructions_and_the_same_execute_call(tmp_path) -> None:
    """End to end against the offline stub server: every request the model receives."""
    (tmp_path / "pdl").mkdir()
    (tmp_path / "nl").mkdir()
    pdl_ops, pdl_bodies = wire._run_stub(tmp_path / "pdl", {})
    nl_ops, nl_bodies = wire._run_stub(tmp_path / "nl", {"representation": "nl"})
    assert pdl_ops[:4] == nl_ops[:4] == ["BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "DRAFT_PLAN", "EXECUTE"]
    for operation, body in zip(nl_ops, nl_bodies):
        text = body.get("instructions", "") + body["input"]
        assert len(PDL_WORDS.findall(text)) == len(FORMAT_RULE_MENTIONS.findall(text)), operation
    pdl_execute, nl_execute = pdl_bodies[pdl_ops.index("EXECUTE")], nl_bodies[nl_ops.index("EXECUTE")]
    assert {k: v for k, v in pdl_execute.items() if k != "input"} == {k: v for k, v in nl_execute.items()
                                                                     if k != "input"}
    assert nl_terms(pdl_execute["input"]) == nl_execute["input"]
    for operation in ("DRAFT_PROMPT", "DRAFT_PLAN"):
        pdl_body, nl_body = pdl_bodies[pdl_ops.index(operation)], nl_bodies[nl_ops.index(operation)]
        assert {k: v for k, v in pdl_body.items() if k not in ("input", "instructions")} == \
            {k: v for k, v in nl_body.items() if k not in ("input", "instructions")}


def test_the_prose_lint_keeps_the_content_rules_and_drops_the_field_label_rule() -> None:
    headed = "OBJECTIVE: compute the total of the list.\nCONSTRAINTS: use Python."
    assert not validate_plan_soundness(headed).valid
    assert validate_plan_soundness(headed, representation="nl").valid
    assert line_violations(headed, "nl") == [] and line_violations(headed)
    deferred = "Compute the total of the list. The method is deferred to execution."
    result = validate_plan_soundness(deferred, representation="nl")
    assert not result.valid
    assert result.feedback.startswith("Artifact requirement: ") and "PDL" not in result.feedback
    assert not validate_plan_soundness("Explain the steps.\n```python\nx = 1\n```", representation="nl").valid
    assert validate_plan_soundness(deferred).feedback.startswith("Pseudocode notation requirement: ")


def test_the_fidelity_question_names_the_artifact_of_the_arm() -> None:
    state = {"source_request": "Sum the list.", "drafted_prompt": "Sum the list."}
    default = repr(PromptFidelityRecipe().build_request(state))
    prose = repr(PromptFidelityRecipe("prompt interpretation").build_request(state))
    assert default.count("drafted prompt pseudocode") == 3 and "interpretation" not in default
    assert prose.count("drafted prompt interpretation") == 3 and "pseudocode" not in prose


def test_the_engine_setting_drives_the_session_mode(tmp_path) -> None:
    engine = SessionEngine(ROOT, lambda r: "", workspace_root=tmp_path, sys1_client=None)
    assert engine.representation == "pdl" and engine.bridge.session_modes == frozenset()
    engine.representation = "nl"
    assert engine.bridge.session_modes == NL
    engine.representation = "pdl"
    assert engine.bridge.session_modes == frozenset()
    with pytest.raises(ValueError):
        engine.representation = "json"


def test_the_repl_refuses_the_nl_arm_without_review(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["pdlt", "--representation", "nl"])
    with pytest.raises(SystemExit) as refused:
        repl.main()
    assert "--review" in str(refused.value)


def test_the_runner_passes_the_arm_to_the_child(tmp_path) -> None:
    base = (tmp_path / "p.txt", "s", tmp_path / "t.txt", tmp_path / "d", "m", "low", ())
    nl = run_catalogue.build_harness_command(*base, {"route": "confirmed", "representation": "nl"})
    args = repl._build_parser().parse_args(nl[3:])
    assert args.representation == "nl" and args.no_review is False
    assert repl._api_run_settings(args)["representation"] == "nl"
    default = run_catalogue.build_harness_command(*base, {"route": "confirmed", "representation": "pdl"})
    assert "--representation" not in default


def test_the_runner_refuses_the_nl_arm_off_the_confirmed_route(monkeypatch) -> None:
    monkeypatch.setattr(sys, "argv", ["run_catalogue.py", "--representation", "nl", "--route", "unconfirmed",
                                      "--prompt-id", "16-06"])
    with pytest.raises(SystemExit) as refused:
        run_catalogue.main()
    assert refused.value.code == 2
