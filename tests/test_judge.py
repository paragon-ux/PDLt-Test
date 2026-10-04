"""Evaluation plane: the judged group's rubrics and the blinded judge tool (offline)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from experiments import judge

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = {
    json.loads(l)["id"]: json.loads(l)
    for l in (ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines()
    if l.strip()
}


def _prompt(rid: str) -> str:
    return (ROOT / "prompts" / MANIFEST[rid]["file"]).read_text(encoding="utf-8-sig")


@pytest.mark.parametrize("rid", judge.rubric_ids())
def test_every_rubric_is_well_formed_and_has_labelled_stress_answers(rid):
    rubric = judge.load_rubric(rid)
    assert rid in MANIFEST, f"{rid} is not a catalogue prompt"
    assert any(c.required for c in rubric.criteria)
    labels = [label for _, label, _ in judge.stress_answers(rid)]
    assert "PASS" in labels and "FAIL" in labels, f"{rid} needs at least one pass_ and one fail_ answer"


def test_judged_prompts_are_not_also_machine_graded():
    import graders

    for rid in judge.rubric_ids():
        entry = MANIFEST[rid]
        machine = entry.get("hidden_tests") or (rid in graders.GRADERS and rid not in judge.QUALITATIVE)
        assert not machine, f"{rid} has a machine grader and a rubric"


def test_verdict_is_computed_from_required_criteria_only():
    rubric = judge.load_rubric("14-06")  # c5 is optional
    marks = {c.id: judge.MET for c in rubric.criteria}
    assert rubric.verdict(marks) == "PASS"
    assert rubric.verdict({**marks, "c5": judge.NOT_MET}) == "PASS"
    assert rubric.verdict({**marks, "c4": judge.NOT_MET}) == "FAIL"


def test_parse_marks_reads_json_and_treats_anything_else_as_not_met():
    rubric = judge.load_rubric("16-04")
    reply = 'Here you go:\n```json\n{"criteria": {"c1": "met", "c2": "Met", "c3": "not met"}, "verdict": "PASS"}\n```'
    marks = judge.parse_marks(reply, rubric)
    assert marks == {"c1": judge.MET, "c2": judge.MET, "c3": judge.NOT_MET}
    assert rubric.verdict(marks) == "FAIL"  # the judge's own "PASS" is never used
    assert set(judge.parse_marks("no json here", rubric).values()) == {judge.NOT_MET}


def test_judge_prompt_is_blind():
    rubric = judge.load_rubric("16-02")
    text = "The answer.\n\n[host] Witness not reproduced by a program run; unverified."
    prompt = judge.judge_prompt(rubric, _prompt("16-02"), text)
    instructions = prompt.split("## The task")[0]
    for word in ("P_new", "P_old", "C0", "C1", "control", "protocol", "harness", "pseudocode"):
        assert word not in instructions
    seen = {}

    def send(spec, p):
        seen[spec.name] = p
        return '{"criteria": {"c1": "met", "c2": "met", "c3": "met"}}'

    out = judge.judge(rubric, _prompt("16-02"), text, [judge.JudgeSpec("a", "m1"), judge.JudgeSpec("b", "m2")], send)
    assert "[host]" not in seen["a"]  # harness marks are stripped before judging
    assert judge.settled(out) == "PASS"


def test_disagreement_and_failed_calls_are_not_settled():
    rubric = judge.load_rubric("16-04")

    def send(spec, _prompt):
        if spec.name == "down":
            raise TimeoutError("provider timeout")
        return '{"criteria": {"c1": "met", "c2": "met", "c3": "met"}}' if spec.name == "yes" else "{}"

    specs = [judge.JudgeSpec("yes", "m"), judge.JudgeSpec("no", "m")]
    assert judge.settled(judge.judge(rubric, "q", "a", specs, send)) is None
    out = judge.judge(rubric, "q", "a", [judge.JudgeSpec("yes", "m"), judge.JudgeSpec("down", "m")], send)
    assert out["down"]["verdict"] is None and judge.settled(out) is None


def test_cohen_kappa():
    assert judge.cohen_kappa(["PASS", "FAIL"] * 5, ["PASS", "FAIL"] * 5) == 1.0
    assert judge.cohen_kappa(["PASS", "PASS", "FAIL", "FAIL"], ["PASS", "FAIL", "PASS", "FAIL"]) == 0.0
    assert judge.cohen_kappa(["PASS"] * 4, ["PASS"] * 4) == 1.0
    a = ["PASS"] * 6 + ["FAIL"] * 4
    b = ["PASS"] * 5 + ["FAIL"] * 5
    assert round(judge.cohen_kappa(a, b), 3) == 0.8


def test_calibration_with_perfect_judges_is_usable(tmp_path):
    rids = judge.rubric_ids()

    def oracle(spec, prompt):
        # A judge that marks every criterion met exactly for the pass_ answers.
        is_pass = any(text.strip() in prompt for rid in rids for name, label, text in judge.stress_answers(rid)
                      if label == "PASS")
        rid = next(r for r in rids if judge.load_rubric(r).task in prompt)
        marks = {c.id: "met" if is_pass else "not_met" for c in judge.load_rubric(rid).criteria}
        return json.dumps({"criteria": marks})

    report = judge.calibrate(rids, {r: _prompt(r) for r in rids},
                             [judge.JudgeSpec("a", "m1"), judge.JudgeSpec("b", "m2")], oracle)
    assert report["kappa_between_judges"] == 1.0 and report["kappa_a_vs_label"] == 1.0
    assert report["usable"]


def test_manual_mode_round_trip(tmp_path):
    index = judge.export_requests([{"key": "r1", "rubric": "16-04", "prompt_text": _prompt("16-04"),
                                    "deliverable": "He is short; he uses his umbrella on rainy days."}], tmp_path)
    assert (tmp_path / "r1.txt").is_file()
    (tmp_path / "r1.reply.txt").write_text('{"criteria": {"c1": "met", "c2": "met", "c3": "met"}}', encoding="utf-8")
    assert judge.import_verdicts(index, tmp_path)["r1"]["verdict"] == "PASS"
