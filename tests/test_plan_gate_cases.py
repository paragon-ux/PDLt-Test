"""Structure of the logic-and-reasoning plan-gate cases run by run_plan_gate.py (live)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / "prompts" / "16_logic_and_reasoning" / "plan_gate_cases.json").read_text(encoding="utf-8"))
MANIFEST = {
    json.loads(line)["id"]: json.loads(line)
    for line in (ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines()
    if line.strip()
}


def test_every_logic_prompt_has_plan_gate_cases():
    logic = sorted(i for i, e in MANIFEST.items() if e["category"] == "logic_and_reasoning")
    assert logic == sorted(case["id"] for case in CASES["cases"])


def test_each_case_has_one_passing_and_three_rejected_plans():
    assert all(extra["expect"] in ("pass", "reject") and extra["id"] in MANIFEST for extra in CASES.get("extra_cases", []))
    assert CASES["expect"] == {"reasoning": "pass", "copied": "reject", "paraphrased": "reject", "expanded": "reject"}
    for case in CASES["cases"]:
        assert set(case["plans"]) == set(CASES["expect"]), case["id"]
        assert all(plan.strip() for plan in case["plans"].values()), case["id"]


def test_copied_plans_reuse_the_prompt_and_reasoning_plans_do_not():
    for case in CASES["cases"]:
        prompt_lines = {line.strip().lower() for line in case["prompt"].splitlines()}
        reasoning = [line.strip().lower() for line in case["plans"]["reasoning"].splitlines()]
        assert not prompt_lines & set(reasoning), case["id"]
        assert case["plans"]["copied"].strip(), case["id"]


def test_reasoning_plans_do_not_state_the_answer():
    """PLAN-04: a reasoning plan exposes the approach, never the result."""
    answers = {"16-03": ("a is a knight", "b is a knave"), "16-04": ("umbrella", "too short"),
               "16-05": ("catcher", "umpire"), "16-06": ("s + 1", "s+1"), "16-07": ("ben owns", "fish is in")}
    for case in CASES["cases"]:
        plan = case["plans"]["reasoning"].lower()
        for answer in answers.get(case["id"], ()):
            assert answer not in plan, (case["id"], answer)
