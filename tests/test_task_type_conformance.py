"""L124 D4: the task-type conformance kit. The built-ins pass; an outside task type written for these tests (not
derived from any benchmark prompt) passes; deliberately broken ones fail with errors that say what is wrong.
Offline: scripted worker and System 1."""
from __future__ import annotations

from pdl_taskmaster.extensions import task_types, verifiers
from pdl_taskmaster.extensions.conformance import check_task_type

from extension_samples import (POSITIVE_SAMPLE, ROW_TOTALS, ROW_TOTALS_SAMPLE, ROW_TOTALS_VERIFIER, IR,
                               no_witness_type, witness_type)


def _names(report):
    return [c.name for c in report.checks]


def test_the_built_ins_conform():
    verified = check_task_type("VERIFIED_EXECUTION", sample=POSITIVE_SAMPLE)
    assert verified.ok, verified
    assert _names(verified) == ["profile", "classification", "route:confirmed", "route:unconfirmed",
                                "unreproduced-witness"]
    standard = check_task_type("STANDARD_EXECUTION")
    assert standard.ok, standard
    assert _names(standard) == ["profile", "classification", "route:confirmed", "route:unconfirmed"]


def test_an_outside_task_type_with_its_own_verifier_conforms():
    with verifiers.REGISTRY.scoped():
        verifiers.register_verifier(ROW_TOTALS_VERIFIER)
        report = check_task_type(ROW_TOTALS, sample=ROW_TOTALS_SAMPLE)
    assert report.ok, report
    assert "ROW_TOTALS" not in task_types.REGISTRY  # the kit leaves the registry as it found it


def test_an_incomplete_declaration_fails_naming_each_missing_component():
    report = check_task_type({"profile": task_types.PROFILE_ID, "category": "ROW_TOTALS"})
    assert not report.ok and _names(report) == ["profile"]
    assert all(any(p.startswith(f"profile: {name}: missing") for p in report.problems())
               for name in ("prompt", "witness_forms", "deliverable", "route", "operations", "verifier"))


def test_a_sample_its_verifier_rejects_fails_the_route_checks():
    wrong = {**ROW_TOTALS_SAMPLE, "body": ROW_TOTALS_SAMPLE["body"].replace("totals = [sum(r) for r in rows]",
                                                                           "totals = [sum(r) + 1 for r in rows]")}
    with verifiers.REGISTRY.scoped():
        verifiers.register_verifier(ROW_TOTALS_VERIFIER)
        report = check_task_type(ROW_TOTALS, sample=wrong)
    assert not report.ok
    assert any(p.startswith("route:confirmed: the sample did not close with a published result")
               for p in report.problems()), report


def test_a_witness_checking_type_without_a_sample_is_told_to_supply_one():
    report = check_task_type(witness_type("SAMPLE_LESS", "witness-reproduction"))
    assert not report.ok and report.problems() == [
        "sample: a task type that checks a witness supplies a sample deliverable whose program prints a witness "
        "its verifier accepts"]


def test_a_type_whose_route_cannot_close_fails_with_the_stage_it_stopped_at():
    """A deliverable written for another task type: no witness where this one needs one."""
    report = check_task_type(witness_type("NEEDS_A_WITNESS", "witness-reproduction"),
                             sample={"body": "A text answer.", "result_ir": IR})
    assert not report.ok
    assert any("stage CLOSED_CANCELLED" in p for p in report.problems()), report


def test_a_report_reads_as_a_checklist():
    text = str(check_task_type(no_witness_type()))
    assert text.splitlines()[0] == "task type LABELLED_LIST: conforms"
    assert "  pass  route:unconfirmed" in text
