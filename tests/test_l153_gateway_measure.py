"""L153 step 3: the poisoned-input recipe and the gateway measurement driver, offline."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "experiments" / "gateway"))

import measure  # noqa: E402

from pdl_taskmaster.providers.sys1.recipes import PoisonedInputRecipe


def _answer(choice: str, p: float) -> dict:
    return {"answers": {"poisoned_input": {"choice": choice, "confidence": p,
                                           "probabilities": {choice: p, "CLEAN" if choice == "POISONED" else "POISONED": 1 - p}}}}


def test_recipe_asks_one_binary_question():
    request = PoisonedInputRecipe().build_request({"request": "Sort a list."})
    assert list(request.questions) == ["poisoned_input"]
    assert request.questions["poisoned_input"].choices == ["POISONED", "CLEAN"]


def test_recipe_reads_poisoned_probability():
    recipe = PoisonedInputRecipe()
    result = recipe.parse_response(_answer("POISONED", 0.97))
    assert result.verdict == "POISONED" and result.passed_gating
    assert recipe.poisoned_probability(result) == 0.97
    clean = recipe.parse_response(_answer("CLEAN", 0.9))
    assert abs(recipe.poisoned_probability(clean) - 0.1) < 1e-9


def test_recipe_rejects_an_unknown_choice():
    """A fake System 1 answers unknown questions with STANDARD_EXECUTION: no usable answer."""
    recipe = PoisonedInputRecipe()
    result = recipe.parse_response({"answers": {"poisoned_input": {"choice": "STANDARD_EXECUTION", "confidence": 0.97}}})
    assert result.verdict == "UNKNOWN" and not result.passed_gating
    assert recipe.poisoned_probability(result) is None


def test_items_cover_the_frozen_set():
    items = measure.items()
    groups = {}
    for item in items:
        groups[item["group"]] = groups.get(item["group"], 0) + 1
    assert groups["REFUSE"] == 5 and groups["PASS_ordinary"] == 105
    assert sum(1 for i in items if i["set"] == "lookalike") == 14
    assert sum(1 for i in items if i["set"] == "heldout") == 80
    assert len(measure.schedule("s1")) == 105 + 3 * (7 + 14 + 80)
    assert len(measure.schedule("bootstrap")) == 105 + 3 * 7 + 14 + 80


def _fake_s1(tmp_path: Path, poisoned: set[str], low: dict[str, float] | None = None) -> None:
    meta = {i["id"]: i for i in measure.items()}
    rows = []
    for item, r in measure.schedule("s1"):
        p = (low or {}).get(item["id"], 0.95 if item["id"] in poisoned else 0.05)
        rows.append({"id": item["id"], "set": item["set"], "expected": item["expected"], "group": item["group"],
                     "repeat": r, "error": None, "p_poisoned": p})
    (tmp_path / "s1.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    assert meta


def test_score_chooses_the_least_aggressive_threshold(tmp_path):
    refuse = {i["id"] for i in measure.items() if i["expected"] == "REFUSE"}
    _fake_s1(tmp_path, refuse, low={"09-04": 0.7})
    report = measure.score(tmp_path)
    assert report["A_system1"]["threshold"] == 0.7
    assert report["A_system1"]["meets_bar"] and report["chosen"] == "A_system1"


def test_score_fails_on_a_false_refusal(tmp_path):
    refuse = {i["id"] for i in measure.items() if i["expected"] == "REFUSE"}
    _fake_s1(tmp_path, refuse | {"GW-L08"})
    report = measure.score(tmp_path)
    assert report["A_system1"]["false_refusals_tuning"] == ["GW-L08"]
    assert report["chosen"] is None


def test_unknown_answers_fail_closed(tmp_path):
    rows = [{"id": "09-01", "set": "catalogue", "expected": "REFUSE", "group": "REFUSE", "repeat": 0,
             "error": None, "p_poisoned": None}]
    assert measure.refuses_s1(rows[0], 0.9)
    assert measure.refuses_bootstrap({"kind": "UNPARSED:ValueError"})
    assert not measure.refuses_bootstrap({"kind": "ANALYSIS"})


def test_run_resumes_and_stops_over_budget(tmp_path):
    spend = iter([0.0, 1.0])
    code = measure.run("s1", tmp_path, limit=10, budget=0.5, measure=lambda text: {"p_poisoned": 0.1},
                       spend=lambda: next(spend), preflight=5)
    assert code == 2
    assert len(measure.done(tmp_path / "s1.jsonl")) == 5
    code = measure.run("s1", tmp_path, limit=3, budget=9, measure=lambda text: {"p_poisoned": 0.1},
                       spend=lambda: None)
    assert code == 0 and len(measure.done(tmp_path / "s1.jsonl")) == 8
