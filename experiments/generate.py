"""Generated isomorph items for the acceptance gate and the dev set.

Each family copies a catalogue prompt's wording, including the user's own method
sentences, which are user words and not harness guidance (GUARD-01). Only the
parameters change. Every item's answer is computed by a solver here. Two sets
come from two fixed seeds:
- the **gate set**, which decides acceptance;
- the **dev set**, which is never used to accept or reject; it exists so that
  later calibration never touches the gate set.

Both are generated, frozen and committed before any task-model call.
``python -m experiments.generate --check`` proves the committed files are exactly
what the seeds produce.

Difficulty notes, recorded so nobody reads more into the isomorphs than is there:
- G-HP uses a random Hamiltonian backbone. The catalogue's 01-07 backbone is the
  identity 0-1-...-11, which is easy to guess, so G-HP is harder than 01-07.
- G-LS keeps 19 givens, as 01-05 does. Uniqueness is not required: the grader
  accepts any completion that respects the givens.
- G-SS draws 12 values from 2..35 and keeps instances with 12-25 solutions.
  01-04 has 19.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import random
import sys
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
PROMPTS_ROOT = ROOT / "prompts"

SETS = {"gate": ("G", 20261004), "dev": ("D", 20261005)}
# family -> (catalogue template id, items per set)
FAMILIES: dict[str, tuple[str, int]] = {
    "SS": ("01-04", 4),
    "LS": ("01-05", 4),
    "HP": ("01-07", 4),
    "KK": ("16-03", 6),
    "HG": ("16-07", 6),
}

# --------------------------------------------------------------------------- subset sum (01-04)

SS_TEMPLATE = (
    "Given the set S = {{{values}}} and target T = {target}:\n\n"
    "Find all subsets of S that sum to exactly T. Use a backtracking algorithm that explores the full search "
    "tree. For each solution found, emit the subset and verify its sum. Report the total number of solutions.\n"
)


def _subset_sum(rng: random.Random) -> tuple[str, dict[str, Any]]:
    while True:
        values = rng.sample(range(2, 36), 12)
        target = rng.randint(30, 50)
        subsets = [sorted(c) for r in range(1, 13) for c in itertools.combinations(values, r) if sum(c) == target]
        if 12 <= len(subsets) <= 25:
            break
    text = SS_TEMPLATE.format(values=", ".join(map(str, values)), target=target)
    return text, {"solution_count": len(subsets), "subsets": sorted(subsets),
                  "verified_by": "brute-force enumeration of all 4095 non-empty subsets"}


# --------------------------------------------------------------------------- Latin square (01-05)

LS_TEMPLATE = (
    "Complete the following partially filled 7x7 Latin square. Each row and column must contain the numbers 1-7 "
    "exactly once. Cells marked 0 are empty and must be filled.\n\n{rows}\n\n"
    "Implement a constraint-propagation solver with backtracking. Emit the completed square and verify that every "
    "row and column is a permutation of {{1,...,7}}.\n"
)


def _latin_square(rng: random.Random) -> tuple[str, dict[str, Any]]:
    rows, cols, symbols = list(range(7)), list(range(7)), list(range(1, 8))
    rng.shuffle(rows)
    rng.shuffle(cols)
    rng.shuffle(symbols)
    square = [[symbols[(rows[i] + cols[j]) % 7] for j in range(7)] for i in range(7)]
    keep = set(rng.sample(range(49), 19))
    givens = [[square[i][j] if i * 7 + j in keep else 0 for j in range(7)] for i in range(7)]
    text = LS_TEMPLATE.format(rows="\n".join(f"Row {i + 1}: [{', '.join(map(str, row))}]"
                                             for i, row in enumerate(givens)))
    return text, {"original_complete_square": square, "givens": givens,
                  "note": "any completion in which every row and column is a permutation of 1-7 and every given "
                          "is kept is correct",
                  "verified_by": "constructed from a Latin square (row, column and symbol permutations of the "
                                 "cyclic square) with 30 entries removed"}


# --------------------------------------------------------------------------- Hamiltonian path (01-07)

HP_TEMPLATE = (
    "Given an undirected graph G with 12 nodes (labeled 0-11) and the following edge list:\n"
    "Edges: [{edges}]\n\n"
    "Determine whether G contains a Hamiltonian path (a path that visits every node exactly once). If one exists, "
    "output the complete path. Use a backtracking search with pruning. Include verification that the path visits "
    "all 12 nodes and every consecutive pair in the path is a valid edge.\n"
)


def _hamiltonian_path(rng: random.Random) -> tuple[str, dict[str, Any]]:
    path = list(range(12))
    rng.shuffle(path)
    edges = {frozenset(pair) for pair in zip(path, path[1:])}
    while len(edges) < 16:
        a, b = rng.sample(range(12), 2)
        edges.add(frozenset((a, b)))
    ordered = [tuple(sorted(e)) for e in edges]
    ordered.sort()
    rng.shuffle(ordered)
    text = HP_TEMPLATE.format(edges=", ".join(f"({a},{b})" for a, b in ordered))
    return text, {"hamiltonian_path": path, "edge_list": [list(e) for e in ordered],
                  "verified_by": "graph constructed around a random Hamiltonian backbone plus 5 extra edges"}


# --------------------------------------------------------------------------- knights and knaves (16-03)

KK_INTRO = ("On an island every inhabitant is either a knight, who always tells the truth, or a knave, who "
            "always lies. You meet {count} inhabitants, {names}.\n\n")
KK_QUESTION = ("\nWhich of {names} are knights and which are knaves? Show the reasoning that rules out every "
               "other assignment.\n")
_COUNT_WORD = {3: "three", 4: "four"}


def _join(names: list[str]) -> str:
    return ", ".join(names[:-1]) + " and " + names[-1]


def _kk_statement(rng: random.Random, speaker: str, names: list[str]) -> tuple[str, Callable[[dict[str, bool]], bool]]:
    """One statement and its truth function over an assignment {name: is_knight}."""
    others = [n for n in names if n != speaker]
    n_word = _COUNT_WORD[len(names)]
    kind = rng.randrange(6)
    if kind == 0:
        x = rng.choice(others)
        return f"{x} is a knight.", lambda a, x=x: a[x]
    if kind == 1:
        x = rng.choice(others)
        return f"{x} is a knave.", lambda a, x=x: not a[x]
    if kind == 2:
        k = rng.randint(1, len(names) - 1)
        noun = "is a knight" if k == 1 else "are knights"
        word = {1: "one", 2: "two", 3: "three"}[k]
        return f"Exactly {word} of us {n_word} {noun}.", lambda a, k=k: sum(a.values()) == k
    if kind == 3:
        x = rng.choice(others)
        same = rng.random() < 0.5
        phrase = "of the same kind" if same else "of different kinds"
        return f"{x} and I are {phrase}.", lambda a, x=x, s=speaker, same=same: (a[x] == a[s]) == same
    if kind == 4:
        x, y = rng.sample(others, 2) if len(others) >= 2 else (others[0], speaker)
        same = rng.random() < 0.5
        phrase = "of the same kind" if same else "of different kinds"
        return f"{x} and {y} are {phrase}.", lambda a, x=x, y=y, same=same: (a[x] == a[y]) == same
    x, y = rng.sample(others, 2) if len(others) >= 2 else (others[0], speaker)
    return f"At least one of {x} and {y} is a knave.", lambda a, x=x, y=y: not (a[x] and a[y])


def _knights_and_knaves(rng: random.Random, size: int) -> tuple[str, dict[str, Any]]:
    names = ["A", "B", "C", "D"][:size]
    while True:
        statements = {name: _kk_statement(rng, name, names) for name in names}
        consistent = []
        for values in itertools.product((True, False), repeat=size):
            assignment = dict(zip(names, values))
            if all(assignment[s] == truth(assignment) for s, (_, truth) in statements.items()):
                consistent.append(assignment)
        if len(consistent) == 1:
            break
    lines = "".join(f'{name} says: "{statements[name][0]}"\n' for name in names)
    text = KK_INTRO.format(count=_COUNT_WORD[size], names=_join(names)) + lines + KK_QUESTION.format(names=_join(names))
    answer = {name: "knight" if consistent[0][name] else "knave" for name in names}
    return text, {"answer": answer, "verified_by": f"exhaustive check of all {2 ** size} assignments",
                  "what_would_be_wrong": "Any other assignment, or more than one assignment"}


# --------------------------------------------------------------------------- house grid (16-07)

HG_INTRO = ("Three houses stand in a row, numbered 1 (left), 2 (middle) and 3 (right). Each house has a different "
            "color (red, green, blue), a different owner (Ana, Ben, Cleo) and a different pet (cat, dog, fish).\n\n")
HG_QUESTION = ("\nWho owns the fish? Give the full arrangement of colors, owners and pets, and show how each clue "
               "fixes it.\n")
COLORS, OWNERS, PETS = ("red", "green", "blue"), ("Ana", "Ben", "Cleo"), ("cat", "dog", "fish")
_PLACE = {0: "left", 1: "middle", 2: "right"}


def _arrangements():
    for colors in itertools.permutations(COLORS):
        for owners in itertools.permutations(OWNERS):
            for pets in itertools.permutations(PETS):
                yield colors, owners, pets


def _hg_clues(solution) -> list[tuple[str, Callable]]:
    """Every clue of the template's kinds that the solution satisfies."""
    colors, owners, pets = solution
    pos = lambda seq, item: seq.index(item)  # noqa: E731
    clues: list[tuple[str, Callable]] = []
    for c1, c2 in itertools.permutations(COLORS, 2):
        if pos(colors, c2) == pos(colors, c1) + 1:
            clues.append((f"The {c1} house is immediately to the left of the {c2} house.",
                          lambda s, c1=c1, c2=c2: pos(s[0], c2) == pos(s[0], c1) + 1))
    for o in OWNERS:
        c = colors[pos(owners, o)]
        clues.append((f"{o} lives in the {c} house.", lambda s, o=o, c=c: pos(s[1], o) == pos(s[0], c)))
    for p in PETS:
        place = pos(pets, p)
        clues.append((f"The {p} lives in the {_PLACE[place]} house.", lambda s, p=p, i=place: pos(s[2], p) == i))
        c = colors[place]
        clues.append((f"The owner of the {p} lives in the {c} house.",
                      lambda s, p=p, c=c: pos(s[2], p) == pos(s[0], c)))
    for o1, o2 in itertools.combinations(OWNERS, 2):
        if abs(pos(owners, o1) - pos(owners, o2)) != 1:
            clues.append((f"{o1} does not live next door to {o2}.",
                          lambda s, o1=o1, o2=o2: abs(pos(s[1], o1) - pos(s[1], o2)) != 1))
    for o in OWNERS:
        for p in PETS:
            if pos(owners, o) != pos(pets, p):
                clues.append((f"{o} does not own the {p}.", lambda s, o=o, p=p: pos(s[1], o) != pos(s[2], p)))
    for c in COLORS:
        if pos(colors, c) != 1:
            clues.append((f"The {c} house is not in the middle.", lambda s, c=c: pos(s[0], c) != 1))
    return clues


def _solutions(clues) -> list:
    return [s for s in _arrangements() if all(check(s) for _, check in clues)]


def _house_grid(rng: random.Random) -> tuple[str, dict[str, Any]]:
    all_arrangements = list(_arrangements())
    while True:
        solution = rng.choice(all_arrangements)
        pool = _hg_clues(solution)
        rng.shuffle(pool)
        chosen: list = []
        for clue in pool:
            chosen.append(clue)
            if len(_solutions(chosen)) == 1:
                break
        for clue in list(chosen):  # minimal: drop every clue the answer does not need
            trial = [c for c in chosen if c is not clue]
            if len(_solutions(trial)) == 1:
                chosen = trial
        fish_owner = solution[1][solution[2].index("fish")]
        if 4 <= len(chosen) <= 6:  # 16-07 has 5 clues; no clue kind names the fish's owner directly
            break
    lines = "".join(f"{i}. {text}\n" for i, (text, _) in enumerate(chosen, 1))
    colors, owners, pets = solution
    houses = [{"house": i + 1, "color": colors[i], "owner": owners[i], "pet": pets[i]} for i in range(3)]
    return HG_INTRO + lines + HG_QUESTION, {
        "answer": {"fish_owner": fish_owner, "houses": houses},
        "verified_by": "exhaustive check of all 216 arrangements; clue set minimal",
        "what_would_be_wrong": "Any other fish owner",
    }


# --------------------------------------------------------------------------- sets

def _family_items(family: str, rng: random.Random, count: int) -> list[tuple[str, dict[str, Any]]]:
    if family == "SS":
        return [_subset_sum(rng) for _ in range(count)]
    if family == "LS":
        return [_latin_square(rng) for _ in range(count)]
    if family == "HP":
        return [_hamiltonian_path(rng) for _ in range(count)]
    if family == "KK":
        return [_knights_and_knaves(rng, 3 if i < count - 2 else 4) for i in range(count)]
    if family == "HG":
        return [_house_grid(rng) for _ in range(count)]
    raise ValueError(family)


def build_set(name: str) -> list[dict[str, Any]]:
    """The items of one set, in a fixed order: [{id, family, template, text, solution}]."""
    prefix, seed = SETS[name]
    items = []
    for index, (family, (template, count)) in enumerate(FAMILIES.items()):
        rng = random.Random(seed * 100 + index)
        for n, (text, solution) in enumerate(_family_items(family, rng, count), 1):
            item_id = f"{prefix}-{family}-{n:02d}"
            items.append({"id": item_id, "family": family, "template": template, "text": text,
                          "solution": {"id": item_id, "ground_truth_status": "verified", **solution}})
    return items


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_set(name: str, root: Path = PROMPTS_ROOT) -> Path:
    out = root / name
    manifest = []
    for item in build_set(name):
        prompt_path = out / item["family"] / f"{item['id']}.txt"
        solution_path = out / item["family"] / f"{item['id']}.solution.json"
        prompt_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_path.write_text(item["text"], encoding="utf-8", newline="\n")
        solution_path.write_text(json.dumps(item["solution"], indent=2) + "\n", encoding="utf-8", newline="\n")
        manifest.append({"id": item["id"], "set": name, "family": item["family"], "template": item["template"],
                         "file": prompt_path.relative_to(root).as_posix(),
                         "solution_file": solution_path.relative_to(root).as_posix(),
                         "sha256": _sha256(item["text"])})
    (out / "MANIFEST.jsonl").write_text("".join(json.dumps(m) + "\n" for m in manifest), encoding="utf-8",
                                        newline="\n")
    return out


def check_set(name: str, root: Path = PROMPTS_ROOT) -> list[str]:
    """Differences between the committed files and what the seed generates (empty: identical)."""
    problems = []
    for item in build_set(name):
        prompt_path = root / name / item["family"] / f"{item['id']}.txt"
        solution_path = root / name / item["family"] / f"{item['id']}.solution.json"
        if not prompt_path.is_file() or prompt_path.read_text(encoding="utf-8") != item["text"]:
            problems.append(f"{item['id']}: prompt differs from the seed's")
        if not solution_path.is_file() or json.loads(solution_path.read_text(encoding="utf-8")) != item["solution"]:
            problems.append(f"{item['id']}: solution differs from the seed's")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--check", action="store_true", help="verify the committed sets instead of writing them")
    args = parser.parse_args(argv)
    if args.check:
        problems = [p for name in SETS for p in check_set(name)]
        for problem in problems:
            print(problem)
        print("generated sets match their seeds" if not problems else f"{len(problems)} differences")
        return 1 if problems else 0
    for name in SETS:
        print(f"wrote {write_set(name)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
