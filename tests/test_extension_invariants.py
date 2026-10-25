"""L124 D3: the core invariants hold whatever an extension does. Each test registers a deliberately misbehaving or
over-reaching extension and shows it cannot break fail-closed behaviour, sandbox confinement, GUARD-01 or provenance
honesty. Offline: scripted worker and System 1."""
from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.extensions import task_types, verifiers
from pdl_taskmaster.extensions.conformance import ScriptedSys1, ScriptedWorker, run_session
from pdl_taskmaster.extensions.profiles import ExtensionFailure, ProfileViolation
from pdl_taskmaster.runtime import provenance
from pdl_taskmaster.verification.sandbox import ExecutionSandbox

from extension_samples import (IR, MARKER, POSITIVE_SAMPLE, AnswersBool, Lenient, Raising, no_witness_type,
                               verifier, witness_type)

ROOT = Path(__file__).resolve().parents[1]
TEXT = {"body": "The labelled list is: a) first, b) second."}


@contextmanager
def scoped():
    with task_types.REGISTRY.scoped(), verifiers.REGISTRY.scoped():
        yield


def _events(result) -> list[dict]:
    path = Path(result.workspace_path) / "turns" / "turn_001" / "events" / "events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


# GUARD-01: what a task type declares never reaches the solver.

def test_classification_text_reaches_system_1_only(tmp_path):
    with scoped():
        api.register_task_type(no_witness_type())
        sys1 = ScriptedSys1({"problem_class": ("STANDARD_EXECUTION", 0.97), "task_type": ("LABELLED_LIST", 0.97)})
        result, worker = run_session(None, "confirmed", TEXT, sys1=sys1, session_dir=tmp_path / "s")
    assert result.provenance["verification"]["problem_class"] == "LABELLED_LIST"
    assert worker.requests and not any(MARKER in prompt for _, prompt in worker.requests)
    assert any(MARKER in json.dumps(request) for request in sys1.requests)


def test_a_task_type_has_no_field_for_solver_text_or_the_sandbox():
    with scoped():
        for extra in ({"sandbox": "audit-only"}, {"guidance": "Use backtracking."}):
            with pytest.raises(ProfileViolation, match="not a component of pdlt.task-type/1"):
                api.register_task_type(no_witness_type(**extra))
        with pytest.raises(ProfileViolation, match="'hint' is not one of"):
            api.register_task_type(no_witness_type(prompt={"classification": None, "instructions": ["hint"]}))


# Provenance honesty.

@pytest.mark.parametrize("route", ["confirmed", "unconfirmed"])
def test_a_type_bound_to_no_verifier_never_claims_more_than_contract_checked(tmp_path, route):
    """Its deliverable prints a positive witness, which the host runs; the claim stays contract_checked."""
    with scoped():
        api.register_task_type(no_witness_type())
        result, _ = run_session("LABELLED_LIST", route, POSITIVE_SAMPLE, session_dir=tmp_path / "s")
    assert result.stage == "CLOSED_UNVERIFIED" and result.provenance["verification"]["level"] == "contract_checked"


def test_the_level_is_capped_by_the_binding_whatever_the_record_says():
    reproduced = {"sandbox_reproduced": True, "provisional": False, "domain_checked": True}
    witness = {"polarity": "positive", "data": {"x": 1}}
    capped = provenance.verification_basis("CLOSED_SUCCESS", True, reproduced, witness, None,
                                           task_type="LABELLED_LIST", verifier="none")
    assert capped["level"] == "contract_checked"
    assert provenance.verification_basis("CLOSED_SUCCESS", True, reproduced, witness, None,
                                         task_type="X", verifier="witness-reproduction")["level"] == "host_verified"


def test_a_lenient_checker_cannot_certify_a_witness_no_program_printed(tmp_path):
    with scoped():
        verifiers.register_verifier(verifier("lenient", Lenient()))
        api.register_task_type(witness_type("LENIENT_CHECKED", "lenient"))
        probe = {"body": "The result is 16.", "result_ir": {**IR, "witness": {"polarity": "positive",
                                                                              "data": {"largest": 16}}}}
        result, _ = run_session("LENIENT_CHECKED", "confirmed", probe, session_dir=tmp_path / "s", max_repairs=0)
    assert (result.stage, result.exit_status, result.provenance) == ("CLOSED_CANCELLED", 1, None)


def test_a_checker_cannot_change_the_witness_the_host_records(tmp_path):
    lenient = Lenient()
    with scoped():
        verifiers.register_verifier(verifier("lenient", lenient))
        api.register_task_type(witness_type("LENIENT_CHECKED", "lenient"))
        result, _ = run_session("LENIENT_CHECKED", "confirmed", POSITIVE_SAMPLE, session_dir=tmp_path / "s")
    assert result.provenance["verification"]["level"] == "host_verified"
    assert result.provenance["verification"]["checker"] == "lenient"  # the record names who judged it
    (validated,) = [e for e in _events(result) if e["kind"] == "RESULT_IR_VALIDATED"]
    assert validated["payload"]["ir"]["witness"]["data"] == {"largest": 20}  # what the program printed (4 * 5)
    assert lenient.arguments and all(not isinstance(v, ExecutionSandbox)
                                     for witness, constraints, body in lenient.arguments
                                     for v in (witness, body, *constraints.values()))


def test_a_form_the_type_does_not_accept_is_refused(tmp_path):
    argued = {"polarity": "positive", "basis": "proof", "data": {"largest": 20},
              "argument": "The largest product of the two ranges is 4 times 5."}
    with scoped():
        verifiers.register_verifier(verifier("lenient", Lenient()))
        api.register_task_type(witness_type("LENIENT_CHECKED", "lenient", forms=["computed"]))
        probe = {"body": "The largest product is 20.", "result_ir": {**IR, "witness": argued}}
        result, _ = run_session("LENIENT_CHECKED", "confirmed", probe, session_dir=tmp_path / "s", max_repairs=0)
    assert result.stage == "CLOSED_CANCELLED"
    assert "WITNESS_FORM_NOT_ACCEPTED" in json.dumps(_events(result))


# Fail-closed.

@pytest.mark.parametrize("checker, message", [(Raising(), "failed .RuntimeError: the checker broke"),
                                              (AnswersBool(), "answered bool, not a VerificationVerdict")])
def test_a_failing_checker_publishes_nothing(tmp_path, checker, message):
    with scoped():
        verifiers.register_verifier(verifier("faulty", checker))
        api.register_task_type(witness_type("FAULTY_CHECKED", "faulty"))
        worker = ScriptedWorker(POSITIVE_SAMPLE, ScriptedSys1())
        with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, task_type="FAULTY_CHECKED", no_review=False) as session:
            session.send("Carry out the stated task.")
            session.confirm()
            with pytest.raises(ExtensionFailure, match=message):
                session.confirm()
            assert session.status()["controller_state"]["stage"] not in ("CLOSED_SUCCESS", "CLOSED_UNVERIFIED")
    assert not list((tmp_path / "s").rglob("provenance.json"))


class Overclaiming:
    """A recipe that reports passing the gate at a confidence below the core floor, and can be made to fail."""

    name = "overclaiming"
    min_confidence = 0.85
    broken = False

    def build_request(self, state):
        if self.broken:
            raise RuntimeError("the recipe broke")
        return task_types.CriterionRecipe("OVERCLAIMED", "The task is any task at all, whatever it asks.").build_request(state)

    def parse_response(self, body, *, duration_ms=0.0):
        from pdl_taskmaster.providers.sys1.schema import RecipeResult

        return RecipeResult(status="ready", verdict="OVERCLAIMED", confidence=0.5, margin=1.0, entropy=0.0,
                            passed_gating=True)

    def map_to_wire(self, result):
        return {}


def test_a_misbehaving_recipe_selects_nothing(tmp_path):
    recipe = Overclaiming()
    sys1 = ScriptedSys1({"problem_class": ("STANDARD_EXECUTION", 0.97)})
    with scoped():
        api.register_task_type(no_witness_type("OVERCLAIMED", prompt={"classification": {"recipe": recipe,
                                                                                         "selects": "OVERCLAIMED"},
                                                                       "instructions": []}))
        assert task_types.select("Any request.", sys1, "confirmed").how == "default"  # below the core floor
        recipe.broken = True
        result, _ = run_session(None, "confirmed", TEXT, sys1=sys1, session_dir=tmp_path / "s")
    (classified,) = [e for e in _events(result) if e["kind"] == "PROBLEM_CLASS_CLASSIFIED"]
    assert (classified["payload"]["task_type"], classified["payload"]["selected_by"]) == ("STANDARD_EXECUTION",
                                                                                         "default")
    assert classified["payload"]["later_classifications"] == [None]  # the failed call, recorded


def test_a_registered_task_type_does_not_change_when_its_declaration_does():
    with scoped():
        declaration = no_witness_type()
        task_type = api.register_task_type(declaration)
        declaration["verifier"] = "witness-reproduction"
        declaration["witness_forms"].append("computed")
        assert task_type.verifier == "none" and task_type.witness_forms == frozenset()
        assert task_types.REGISTRY.get("LABELLED_LIST").declaration["witness_forms"] == []


def test_a_turn_of_an_unregistered_task_type_is_never_resumed_under_another(tmp_path):
    with scoped():
        api.register_task_type(no_witness_type())
        worker = ScriptedWorker(TEXT, ScriptedSys1())
        with api.Session.open(worker, tmp_path / "s", repo_root=ROOT, task_type="LABELLED_LIST", no_review=False) as session:
            assert session.send("Carry out the stated task.").stage == "PROMPT_REVIEW"
    with api.Session.open(ScriptedWorker(TEXT, ScriptedSys1()), tmp_path / "s", repo_root=ROOT, mode="protocol") as resumed:
        assert "'LABELLED_LIST', which is not registered here" in resumed.restore_notice
        assert resumed.status()["workspace_path"] is None  # fresh protocol state, nothing resumed
