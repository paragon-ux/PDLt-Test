"""Ground-truth graders for the PDLt catalogue (evaluation plane).

This module is allowed to know the benchmark; the harness package
(``src/pdl_taskmaster``) is not. It never influences a run: it reads what a
finished session published and decides whether a ``CLOSED_SUCCESS`` verdict is
substantively right (PASS), wrong (FAIL, a false positive), or needs the GOAL.md
Step 5 human spot check (MANUAL). Prompts without machine-checkable ground truth
return N/A.

Answers are recovered from the published deliverable (``current.md``) and, when
the deliverable contains a Python block, from that block's stdout run in the
harness sandbox. Graders check structure against the prompt and the solution
files; they do not trust prose claims alone.
"""
from __future__ import annotations

import itertools
import json
import re
from pathlib import Path
from typing import Callable

PASS, FAIL, MANUAL, NA = "PASS", "FAIL", "MANUAL", "N/A"

_INT = r"-?\d+"
_LIST_RE = re.compile(r"[\[\(\{]\s*(" + _INT + r"(?:\s*,\s*" + _INT + r")*)\s*[\]\)\}]")


# --------------------------------------------------------------------------- corpus

def find_deliverable(result_dir: Path) -> str | None:
    """Newest published execution deliverable under a result directory."""
    files = [
        p for p in Path(result_dir).rglob("current.md")
        if p.parent.match("*/stages/50_execution/output")
    ]
    if not files:
        return None
    newest = max(files, key=lambda p: p.stat().st_mtime)
    return newest.read_text(encoding="utf-8", errors="replace")


def _python_blocks(text: str) -> list[str]:
    return re.findall(r"```(?:python|py)\s*\n(.*?)```", text, re.S)


def build_corpus(result_dir: Path, *, run_code: bool = True) -> str | None:
    text = find_deliverable(result_dir)
    if text is None:
        return None
    if run_code:
        blocks = _python_blocks(text)
        if blocks:
            from pdl_taskmaster.verification.sandbox import ExecutionSandbox

            out = ExecutionSandbox(timeout_seconds=30.0).run_code(blocks[-1])
            if out.stdout:
                text += "\n\n[GRADER: deliverable code stdout]\n" + out.stdout
    return text


def int_lists(text: str) -> list[list[int]]:
    return [[int(x) for x in m.group(1).split(",")] for m in _LIST_RE.finditer(text)]


def _prompt_text(prompts_dir: Path, entry: dict) -> str:
    return (Path(prompts_dir) / entry["file"]).read_text(encoding="utf-8-sig")


# --------------------------------------------------------------------------- 01-01

def grade_partition_triples(corpus: str, prompt: str) -> tuple[str, str]:
    universe = {int(x) for x in re.search(r"\{([^}]*)\}", prompt).group(1).split(",")}
    valid: set[tuple[int, ...]] = set()
    for lst in int_lists(corpus):
        if len(lst) == 3 and set(lst) <= universe and len(set(lst)) == 3:
            a, b, c = sorted(lst)
            if a + b == c:
                valid.add((a, b, c))
    triples = sorted(valid)

    def cover(remaining: frozenset[int], chosen: int) -> bool:
        if not remaining:
            return True
        pivot = min(remaining)
        for t in triples:
            if pivot in t and set(t) <= remaining and cover(remaining - set(t), chosen + 1):
                return True
        return False

    if cover(frozenset(universe), 0):
        return PASS, "found 15 disjoint valid triples partitioning the list"
    return FAIL, f"no exact partition into valid triples among {len(triples)} valid triples presented"


# --------------------------------------------------------------------------- 01-02

def _exact_covers(prompt: str) -> set[frozenset[str]]:
    sets = {f"S{n}": frozenset(int(x) for x in body.split(",")) for n, body in re.findall(r"S(\d+)\s*=\s*\{([^}]*)\}", prompt)}
    universe = frozenset(int(x) for x in re.search(r"U\s*=\s*\{([^}]*)\}", prompt).group(1).split(","))
    covers = set()
    for r in range(1, len(sets) + 1):
        for combo in itertools.combinations(sorted(sets), r):
            elems = [e for name in combo for e in sets[name]]
            if len(elems) == len(universe) and frozenset(elems) == universe:
                covers.add(frozenset(combo))
    return covers


def grade_exact_covers(corpus: str, prompt: str) -> tuple[str, str]:
    expected = _exact_covers(prompt)
    named = {
        frozenset(re.findall(r"S\d+", m.group(0)))
        for m in re.finditer(r"S\d+(?:['\"]?\s*,\s*['\"]?S\d+)+", corpus)
    }
    sets = {f"S{n}": tuple(sorted(int(x) for x in body.split(","))) for n, body in re.findall(r"S(\d+)\s*=\s*\{([^}]*)\}", prompt)}
    by_elements = {v: k for k, v in sets.items()}
    element_groups = set()
    for lst in int_lists(corpus):
        if len(lst) == 3 and tuple(sorted(lst)) in by_elements:
            element_groups.add(by_elements[tuple(sorted(lst))])
    found = {g for g in named if len(g) == 3}
    # a cover may also be presented as its member element-lists
    for cover in expected:
        if cover <= element_groups:
            found.add(cover)
    missing = expected - found
    wrong = {g for g in found if g not in expected}
    if missing:
        return FAIL, f"missing {len(missing)} of {len(expected)} exact covers"
    if wrong:
        return FAIL, f"presented {len(wrong)} non-cover(s)"
    return PASS, f"all {len(expected)} exact covers presented"


# --------------------------------------------------------------------------- 01-03

def grade_wheel_coloring(corpus: str, prompt: str) -> tuple[str, str]:
    edges = {(0, i) for i in range(1, 12)} | {(i, i + 1) for i in range(1, 11)} | {(11, 1)}

    def proper(coloring: dict[int, int]) -> bool:
        return (
            set(coloring) == set(range(12))
            and all(1 <= c <= 4 for c in coloring.values())
            and all(coloring[a] != coloring[b] for a, b in edges)
        )

    current: dict[int, int] = {}
    candidates = []
    for m in re.finditer(r"['\"]?(\d{1,2})['\"]?\s*(?:[:=]|->)\s*([1-4])\b", corpus):
        node, color = int(m.group(1)), int(m.group(2))
        if node in current or node > 11:
            current = {}
        if node <= 11:
            current[node] = color
        if len(current) == 12:
            candidates.append(dict(current))
            current = {}
    for lst in int_lists(corpus):
        if len(lst) == 12 and all(1 <= c <= 4 for c in lst):
            candidates.append(dict(enumerate(lst)))
    if any(proper(c) for c in candidates):
        return PASS, "valid 4-coloring found (3-color impossibility proof not machine-graded)"
    return FAIL, f"no proper 4-coloring among {len(candidates)} candidate colorings"


# --------------------------------------------------------------------------- 01-04

def grade_subset_sum(corpus: str, prompt: str) -> tuple[str, str]:
    S = [int(x) for x in re.search(r"S\s*=\s*\{([^}]*)\}", prompt).group(1).split(",")]
    T = int(re.search(r"T\s*=\s*(\d+)", prompt).group(1))
    expected = {
        frozenset(c)
        for r in range(1, len(S) + 1)
        for c in itertools.combinations(S, r)
        if sum(c) == T
    }
    found = {frozenset(l) for l in int_lists(corpus) if len(set(l)) == len(l) and set(l) <= set(S) and sum(l) == T}
    missing = expected - found
    if missing:
        return FAIL, f"{len(found)} of {len(expected)} solution subsets presented"
    if not re.search(rf"\b{len(expected)}\b", corpus):
        return FAIL, f"all subsets presented but total ({len(expected)}) not reported"
    return PASS, f"all {len(expected)} subsets and the total presented"


# --------------------------------------------------------------------------- 01-05

def grade_latin_square(corpus: str, prompt: str) -> tuple[str, str]:
    givens = [[int(x) for x in row.split(",")] for row in re.findall(r"Row \d+:\s*\[([^\]]*)\]", prompt)]
    rows = [l for l in int_lists(corpus) if len(l) == 7]
    want = set(range(1, 8))
    for start in range(len(rows) - 6):
        grid = rows[start:start + 7]
        if (
            all(set(r) == want for r in grid)
            and all({grid[r][c] for r in range(7)} == want for c in range(7))
            and all(g == 0 or g == grid[r][c] for r, row in enumerate(givens) for c, g in enumerate(row))
        ):
            return PASS, "valid completion respecting all givens"
    return FAIL, "no valid 7x7 completion respecting the givens"


# --------------------------------------------------------------------------- 01-06

def grade_first_fit(corpus: str, prompt: str) -> tuple[str, str]:
    cap = int(re.search(r"C\s*=\s*(\d+)", prompt).group(1))
    items = sorted(int(x) for x in re.search(r"Items\s*=\s*\[([^\]]*)\]", prompt).group(1).split(","))
    ff_bins = 0
    remaining: list[int] = []
    for it in [int(x) for x in re.search(r"Items\s*=\s*\[([^\]]*)\]", prompt).group(1).split(",")]:
        for i, room in enumerate(remaining):
            if it <= room:
                remaining[i] -= it
                break
        else:
            remaining.append(cap - it)
    ff_bins = len(remaining)
    bins = [l for l in int_lists(corpus) if 1 <= len(l) <= 4 and sum(l) <= cap and set(l) <= set(items)]

    def packs(rest: list[int], k: int, used: tuple[int, ...]) -> bool:
        if not rest:
            return True
        if k == 0:
            return False
        for b in bins:
            trial = list(rest)
            try:
                for x in b:
                    trial.remove(x)
            except ValueError:
                continue
            if packs(sorted(trial), k - 1, used):
                return True
        return False

    optimal_ok = packs(items, ff_bins - 1, ())
    ff_stated = re.search(rf"\b{ff_bins}\s+bins?\b", corpus, re.I) is not None
    if optimal_ok and ff_stated:
        return PASS, f"valid {ff_bins - 1}-bin packing presented and First Fit stated as {ff_bins} bins"
    return FAIL, f"optimal packing presented={optimal_ok}, First Fit={ff_bins} bins stated={ff_stated}"


# --------------------------------------------------------------------------- 01-07

def grade_hamiltonian_path(corpus: str, prompt: str) -> tuple[str, str]:
    edges = {frozenset(map(int, p)) for p in re.findall(r"\((\d+),\s*(\d+)\)", prompt)}
    n = int(re.search(r"(\d+) nodes", prompt).group(1))
    for lst in int_lists(corpus):
        if len(lst) == n and sorted(lst) == list(range(n)) and all(frozenset(p) in edges for p in zip(lst, lst[1:])):
            return PASS, "valid Hamiltonian path over the stated edges"
    return FAIL, "no valid Hamiltonian path presented"


# --------------------------------------------------------------------------- 13-01

_UNSAT_PHRASES = (
    "unsatisfiable", "no solution", "no solutions", "no valid assignment",
    "cannot be satisfied", "not satisfiable", "no assignment satisfies", "has no solution",
)


def grade_reports_no_solution(corpus: str, prompt: str) -> tuple[str, str]:
    low = corpus.lower()
    if any(p in low for p in _UNSAT_PHRASES):
        return PASS, "reports that no solution exists"
    return FAIL, "does not report unsatisfiability"


GRADERS: dict[str, Callable[[str, str], tuple[str, str]]] = {
    "01-01": grade_partition_triples,
    "01-02": grade_exact_covers,
    "01-03": grade_wheel_coloring,
    "01-04": grade_subset_sum,
    "01-05": grade_latin_square,
    "01-06": grade_first_fit,
    "01-07": grade_hamiltonian_path,
    "13-01": grade_reports_no_solution,
}


def grade(entry: dict, result_dir: Path, prompts_dir: Path, *, run_code: bool = True) -> dict:
    """Grade one finished run. Never raises."""
    if entry.get("ground_truth_status") != "verified":
        return {"grade": NA, "reason": "no ground truth required"}
    fn = GRADERS.get(entry["id"])
    if fn is None:
        return {"grade": MANUAL, "reason": "needs GOAL.md Step 5 human spot check"}
    try:
        corpus = build_corpus(Path(result_dir), run_code=run_code)
        if corpus is None:
            return {"grade": FAIL, "reason": "no published deliverable"}
        verdict, reason = fn(corpus, _prompt_text(prompts_dir, entry))
        return {"grade": verdict, "reason": reason}
    except Exception as exc:  # a grader bug must never mask a run
        return {"grade": "ERROR", "reason": f"{type(exc).__name__}: {exc}"}


if __name__ == "__main__":  # python graders.py <result_dir> <prompt_id>
    import sys

    root = Path(__file__).resolve().parent
    manifest = [json.loads(l) for l in (root / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines() if l.strip()]
    entry = next(e for e in manifest if e["id"] == sys.argv[2])
    print(json.dumps(grade(entry, Path(sys.argv[1]), root / "prompts"), indent=2))
