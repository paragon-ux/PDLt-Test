"""Power of the L145 primary test, simulated from the L94 per-prompt outcomes (the largest paired unconfirmed-against-
Control evaluation at reasoning low on Cerebras: 57 machine-graded prompts, 3 repeats).

    python experiments/power_sim.py [--results PATH] [--sims N] [--seed S] [--md OUT]

Each prompt's true rates are taken as the observed L94 rates of the two arms (U and C), for passes and for silent
false positives (CLOSED_SUCCESS with ground truth FAIL). A simulated study draws R runs per prompt and arm from those
rates and applies the primary test (``experiments.study_stats.sign_flip_p``, exact, two-sided, alpha 0.05); power is
the share of studies that reject. Two prompt models: **fixed** (the same 57 prompts, as Study B runs them) and
**resampled** (K prompts drawn with replacement, for a population of prompts like these). Plug-in rates treat a prompt
seen 3 of 3 as certain, so fixed-prompt power is a lower figure and resampled power an upper one; the effect L94
measured was on an older commit and may not hold now."""
from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from catalogue_runs import RUNS_DIR  # noqa: E402
from experiments.study_stats import sign_flip_p  # noqa: E402

ALPHA = 0.05


def rates(path: Path) -> tuple[list[str], dict[str, dict[str, tuple[float, float]]]]:
    rows = json.loads(path.read_text(encoding="utf-8"))["rows"]
    seen: dict[str, dict[str, list[tuple[int, int]]]] = defaultdict(lambda: defaultdict(list))
    for r in rows:
        if r["variant"] in ("U", "C"):
            sfp = int(r["verdict"] == "CLOSED_SUCCESS" and r["grade"] == "FAIL")
            seen[r["id"]][r["variant"]].append((int(bool(r["passed"])), sfp))
    ids = sorted(p for p in seen if seen[p]["U"] and seen[p]["C"])
    out = {p: {arm: (sum(x for x, _ in seen[p][arm]) / len(seen[p][arm]),
                     sum(y for _, y in seen[p][arm]) / len(seen[p][arm])) for arm in ("U", "C")} for p in ids}
    return ids, out


def power(ids, table, *, endpoint: int, repeats: int, prompts: int | None, sims: int, rng: random.Random) -> float:
    hits = 0
    for _ in range(sims):
        chosen = [rng.choice(ids) for _ in range(prompts)] if prompts else ids
        diffs = []
        for p in chosen:
            pu, pc = table[p]["U"][endpoint], table[p]["C"][endpoint]
            u = sum(rng.random() < pu for _ in range(repeats))
            c = sum(rng.random() < pc for _ in range(repeats))
            diffs.append((u - c) / repeats)
        hits += sign_flip_p(diffs, repeats) < ALPHA
    return hits / sims


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--results", type=Path, default=RUNS_DIR / "sweep-logs" / "L94-results.json")
    parser.add_argument("--sims", type=int, default=2000)
    parser.add_argument("--seed", type=int, default=20261022)
    parser.add_argument("--md", type=Path, default=None)
    args = parser.parse_args(argv)
    ids, table = rates(args.results)
    rng = random.Random(args.seed)
    observed = {name: sum(table[p]["U"][e] - table[p]["C"][e] for p in ids) / len(ids)
                for name, e in (("passes", 0), ("silent false positives", 1))}
    rows = []
    for name, endpoint in (("passes", 0), ("silent false positives", 1)):
        for repeats, prompts in ((3, None), (3, 57), (5, None), (5, 57), (3, 80), (3, 112)):
            value = power(ids, table, endpoint=endpoint, repeats=repeats, prompts=prompts, sims=args.sims, rng=rng)
            rows.append({"endpoint": name, "repeats": repeats, "prompts": prompts or len(ids),
                         "model": "fixed" if prompts is None else "resampled", "power": round(value, 3)})
    lines = [f"Power of the exact prompt-clustered sign-flip test (alpha {ALPHA}, two-sided), from "
             f"`{args.results.name}`: {len(ids)} prompts; observed mean per-prompt differences U - C: passes "
             f"{observed['passes']:+.3f}, silent false positives {observed['silent false positives']:+.3f}. "
             f"{args.sims} simulated studies per row, seed {args.seed}.", "",
             "| Endpoint | Prompts | Repeats | Prompt model | Power |", "|---|---|---|---|---|"]
    lines += [f"| {r['endpoint']} | {r['prompts']} | {r['repeats']} | {r['model']} | {r['power']:.2f} |" for r in rows]
    text = "\n".join(lines) + "\n"
    print(text)
    if args.md:
        args.md.write_text(text, encoding="utf-8", newline="\n")
        args.md.with_suffix(".json").write_text(json.dumps({"observed": observed, "rows": rows}, indent=1),
                                                encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
