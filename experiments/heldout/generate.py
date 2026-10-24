"""The held-out set of ledger L145: fresh instances of the catalogue families whose grader reads its instance from the
prompt, so a grader can judge an instance it was not written for.

    python experiments/heldout/generate.py            # writes prompts/heldout/, the manifest and the solutions

Six families (the catalogue prompts 01-01, 01-02, 01-04, 01-05, 01-06 and 01-07), two instances each, from one fixed
seed. Each prompt keeps its family's wording and changes only the instance. Every instance has a solution by
construction (planted, or checked here by exhaustive search), and ``solutions.json`` holds one valid answer per
instance for the graders' self-tests (``tests/test_l145_heldout.py``). Generated and committed before any study run;
never regenerated with another seed after results exist.

The set tests whether results carry over to instances no prompt, test or design note has seen. It does not test
breadth: all six families are combinatorial search, the category where the protocol's lead has been largest (L94)."""
from __future__ import annotations

import itertools
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = ROOT / "prompts"
OUT = PROMPTS / "heldout"
MANIFEST = PROMPTS / "HELDOUT_MANIFEST.jsonl"
SEED = 20261022


def _braces(values) -> str:
    return "{" + ", ".join(str(v) for v in values) + "}"


def partition_triples(rng: random.Random) -> tuple[str, dict]:
    used: set[int] = set()
    triples = []
    while len(triples) < 15:
        a, b = rng.randint(10, 100), rng.randint(10, 100)
        c = a + b
        if len({a, b, c}) == 3 and not {a, b, c} & used:
            used |= {a, b, c}
            triples.append(sorted((a, b, c)))
    values = sorted(used)
    rng.shuffle(values)
    prompt = (f"Given the list L of 45 distinct positive integers (N=15):\nL = {_braces(values)}\n\n"
              "Determine whether L can be partitioned into 15 disjoint triples (a_i, b_i, c_i) such that a_i + b_i = "
              "c_i for every triple i in {1, ..., 15}. If a valid partition exists, emit one complete example.\n")
    return prompt, {"triples": triples}


def exact_covers(rng: random.Random) -> tuple[str, dict]:
    while True:
        sets: list[tuple[int, ...]] = []
        for _ in range(2):  # two planted covers
            elements = list(range(1, 10))
            rng.shuffle(elements)
            sets += [tuple(sorted(elements[i:i + 3])) for i in (0, 3, 6)]
        while len(sets) < 9:
            sets.append(tuple(sorted(rng.sample(range(1, 10), 3))))
        if len(set(sets)) == 9:
            break
    rng.shuffle(sets)
    names = {f"S{i}": s for i, s in enumerate(sets, 1)}
    covers = sorted(sorted(c) for r in (3,) for c in itertools.combinations(names, r)
                    if sorted(e for n in c for e in names[n]) == list(range(1, 10)))
    rows = [", ".join(f"S{i} = {_braces(names[f'S{i}'])}" for i in range(k, k + 3)) for k in (1, 4, 7)]
    prompt = ("Given the universe U = {1, 2, 3, 4, 5, 6, 7, 8, 9} and the collection of sets:\n"
              + ",\n".join(rows) + "\n\n"
              "Find ALL exact covers of U (subcollections where every element of U appears in exactly one selected "
              "set). Implement the search using Knuth's Algorithm X with dancing links. Include a self-contained test "
              "that verifies each solution covers U exactly once.\n")
    return prompt, {"covers": covers}


def subset_sum(rng: random.Random) -> tuple[str, dict]:
    while True:
        values = rng.sample(range(2, 41), 12)
        target = rng.randint(30, 50)
        found = [sorted(c) for r in range(1, 13) for c in itertools.combinations(values, r) if sum(c) == target]
        if 4 <= len(found) <= 20:
            break
    prompt = (f"Given the set S = {_braces(values)} and target T = {target}:\n\n"
              "Find all subsets of S that sum to exactly T. Use a backtracking algorithm that explores the full search "
              "tree. For each solution found, emit the subset and verify its sum. Report the total number of "
              "solutions.\n")
    return prompt, {"subsets": found}


def latin_square(rng: random.Random) -> tuple[str, dict]:
    rows, cols, symbols = list(range(7)), list(range(7)), list(range(1, 8))
    for order in (rows, cols, symbols):
        rng.shuffle(order)
    square = [[symbols[(rows[r] + cols[c]) % 7] for c in range(7)] for r in range(7)]
    kept = set(rng.sample(range(49), 19))  # the catalogue prompt gives 19 cells
    givens = [[square[r][c] if r * 7 + c in kept else 0 for c in range(7)] for r in range(7)]
    lines = "\n".join(f"Row {r + 1}: [{', '.join(str(v) for v in row)}]" for r, row in enumerate(givens))
    prompt = ("Complete the following partially filled 7x7 Latin square. Each row and column must contain the numbers "
              "1-7 exactly once. Cells marked 0 are empty and must be filled.\n\n" + lines + "\n\n"
              "Implement a constraint-propagation solver with backtracking. Emit the completed square and verify that "
              "every row and column is a permutation of {1,...,7}.\n")
    return prompt, {"square": square}


def _first_fit(items: list[int], cap: int) -> list[list[int]]:
    bins: list[list[int]] = []
    for item in items:
        for b in bins:
            if sum(b) + item <= cap:
                b.append(item)
                break
        else:
            bins.append([item])
    return bins


def _optimal(items: list[int], cap: int) -> list[list[int]]:
    best: list[list[int]] | None = None

    def place(index: int, bins: list[list[int]]) -> None:
        nonlocal best
        if best is not None and len(bins) >= len(best):
            return
        if index == len(items):
            best = [list(b) for b in bins]
            return
        for b in bins:
            if sum(b) + items[index] <= cap:
                b.append(items[index])
                place(index + 1, bins)
                b.pop()
        bins.append([items[index]])
        place(index + 1, bins)
        bins.pop()

    place(0, [])
    return best or []


def first_fit(rng: random.Random) -> tuple[str, dict]:
    while True:
        items = [rng.randint(2, 8) for _ in range(8)]
        ff, opt = _first_fit(items, 10), _optimal(sorted(items, reverse=True), 10)
        if len(ff) == len(opt) + 1 and all(len(b) <= 4 for b in opt) and all(len(b) <= 4 for b in ff):
            break
    prompt = (f"Consider the bin packing problem with bin capacity C = 10 and items arriving in the following order:\n"
              f"Items = [{', '.join(str(i) for i in items)}]\n\n"
              "1. Run the First Fit algorithm on the items in the given arrival order and report the resulting "
              "packing.\n2. Find an optimal packing that minimizes the number of bins.\n3. Report the gap between "
              "First Fit and optimal, and explain why the arrival order causes FF to use more bins.\n\n"
              "Include a self-test that verifies both packings use all items exactly once and respect the capacity "
              "constraint.\n")
    return prompt, {"first_fit": ff, "optimal": opt}


def hamiltonian_path(rng: random.Random) -> tuple[str, dict]:
    path = list(range(12))
    rng.shuffle(path)
    edges = {tuple(sorted(p)) for p in zip(path, path[1:])}
    while len(edges) < 16:  # the catalogue prompt has 16 edges
        a, b = rng.sample(range(12), 2)
        edges.add(tuple(sorted((a, b))))
    listed = sorted(edges)
    rng.shuffle(listed)
    prompt = ("Given an undirected graph G with 12 nodes (labeled 0-11) and the following edge list:\n"
              f"Edges: [{', '.join(f'({a},{b})' for a, b in listed)}]\n\n"
              "Determine whether G contains a Hamiltonian path (a path that visits every node exactly once). If one "
              "exists, output the complete path. Use a backtracking search with pruning. Include verification that "
              "the path visits all 12 nodes and every consecutive pair in the path is a valid edge.\n")
    return prompt, {"path": path}


FAMILIES = [  # (catalogue prompt of the family, name, its grader, generator)
    ("01-01", "partition_triples", "grade_partition_triples", partition_triples),
    ("01-02", "exact_covers", "grade_exact_covers", exact_covers),
    ("01-04", "subset_sum", "grade_subset_sum", subset_sum),
    ("01-05", "latin_square", "grade_latin_square", latin_square),
    ("01-06", "first_fit", "grade_first_fit", first_fit),
    ("01-07", "hamiltonian_path", "grade_hamiltonian_path", hamiltonian_path),
]


def generate() -> tuple[list[dict], dict[str, dict], dict[str, str]]:
    rng = random.Random(SEED)
    entries, solutions, texts = [], {}, {}
    number = 0
    for instance in (1, 2):
        for family, name, grader, make in FAMILIES:
            number += 1
            pid = f"HO-{number:02d}"
            prompt, solution = make(rng)
            file = f"heldout/{pid}_{name}.txt"
            entries.append({"id": pid, "category": "heldout_combinatorial_search", "file": file,
                            "difficulty": "hard", "expected_routing": "VERIFIED_EXECUTION",
                            "expected_stage": "CLOSED_SUCCESS", "ground_truth_status": "verified", "grader": grader,
                            "family": family, "instance": instance, "tags": ["heldout", name]})
            solutions[pid] = solution
            texts[file] = prompt
    return entries, solutions, texts


def main() -> int:
    entries, solutions, texts = generate()
    OUT.mkdir(parents=True, exist_ok=True)
    for file, text in texts.items():
        (PROMPTS / file).write_text(text, encoding="utf-8", newline="\n")
    MANIFEST.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8", newline="\n")
    (OUT / "solutions.json").write_text(json.dumps(solutions, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"wrote {len(entries)} prompts, {MANIFEST.name} and solutions.json (seed {SEED})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
