"""L145: the held-out set (fresh instances of six catalogue families) is the committed output of its seeded generator,
each instance has a solution, and each family's grader passes a valid answer and fails a broken one on every
instance. Offline."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

import graders
import run_catalogue
from experiments.heldout import generate

ROOT = Path(__file__).resolve().parents[1]
ENTRIES = run_catalogue.load_manifest(path=generate.MANIFEST)
SOLUTIONS = json.loads((generate.OUT / "solutions.json").read_text(encoding="utf-8"))


def _lists(rows) -> str:
    return "\n".join("[" + ", ".join(str(v) for v in row) + "]" for row in rows)


def _answers(entry: dict) -> tuple[str, str]:
    """(a valid answer, a broken one) for the instance, from its stored solution."""
    s = SOLUTIONS[entry["id"]]
    name = entry["grader"]
    if name == "grade_partition_triples":
        return _lists(s["triples"]), _lists(s["triples"][:-1])
    if name == "grade_exact_covers":
        covers = ["Cover: " + ", ".join(c) for c in s["covers"]]
        return "\n".join(covers), covers[0]
    if name == "grade_subset_sum":
        total = f"Total: {len(s['subsets'])} solutions"
        return _lists(s["subsets"]) + "\n" + total, _lists(s["subsets"][:-1]) + "\n" + total
    if name == "grade_latin_square":
        broken = [list(row) for row in s["square"]]
        broken[0][0], broken[0][1] = broken[0][1], broken[0][0]
        return _lists(s["square"]), _lists(broken)
    if name == "grade_first_fit":
        stated = f"First Fit uses {len(s['first_fit'])} bins; the optimum uses {len(s['optimal'])} bins."
        return _lists(s["first_fit"]) + "\n" + _lists(s["optimal"]) + "\n" + stated, _lists(s["first_fit"]) + "\n" + stated
    if name == "grade_hamiltonian_path":
        return _lists([s["path"]]), _lists([s["path"][:-1]])  # one node short
    raise AssertionError(name)


def test_the_committed_set_is_the_generators_output():
    entries, solutions, texts = generate.generate()
    assert ENTRIES == entries and SOLUTIONS == json.loads(json.dumps(solutions))
    for file, text in texts.items():
        assert (generate.PROMPTS / file).read_text(encoding="utf-8") == text


def test_the_set_is_outside_the_catalogue():
    catalogue = {e["id"] for e in run_catalogue.load_manifest()}
    assert len(ENTRIES) == 12 and not catalogue & {e["id"] for e in ENTRIES}
    for entry in ENTRIES:
        assert entry["id"] not in graders.GRADERS and entry["grader"] in graders.GRADERS_BY_NAME
        assert not re.search(r"\b(0[1-9]|1[0-6])-(0[1-7])\b", entry["id"])  # the catalogue's ID pattern


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_each_grader_passes_a_valid_answer_and_fails_a_broken_one(entry):
    prompt = (generate.PROMPTS / entry["file"]).read_text(encoding="utf-8")
    valid, broken = _answers(entry)
    grade = graders.GRADERS_BY_NAME[entry["grader"]]
    assert grade(valid, prompt)[0] == graders.PASS, grade(valid, prompt)
    assert grade(broken, prompt)[0] == graders.FAIL, grade(broken, prompt)


def test_the_runner_runs_the_set_from_its_own_manifest():
    import subprocess
    import sys

    dry = subprocess.run([sys.executable, "run_catalogue.py", "--manifest", "prompts/HELDOUT_MANIFEST.jsonl",
                          "--prompt-id", "HO-01,HO-12", "--dry-run"], cwd=ROOT, capture_output=True, text=True)
    assert dry.returncode == 0, dry.stderr
    assert "HO-01" in dry.stdout and "HO-12" in dry.stdout and "01-01" not in dry.stdout
