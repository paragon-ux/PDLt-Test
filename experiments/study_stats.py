"""The statistics of the L145 studies, in one place for the report and the power simulation.

- **Prompt-clustered contrast** (the primary test): per prompt, the difference of the two arms' mean outcomes over its
  repeats; the effect is the mean of those differences over prompts. The test is the exact two-sided sign-flip
  permutation test of that mean: with every prompt run the same number of times R, each difference is a multiple of
  1/R, so the permutation distribution of the sum is counted exactly over integers (no Monte Carlo). The interval is
  the BCa bootstrap over prompts (``experiments.analysis.bootstrap_ci``, seed fixed).
- **Run-level exact McNemar** (secondary): ``experiments.five_arm_report.exact_mcnemar`` over the discordant pairs of
  runs matched by prompt and repeat. Repeats of a prompt are not independent, so it overstates the evidence.
- **Holm** step-down adjustment over a pre-specified family."""
from __future__ import annotations

from typing import Iterable

from experiments.analysis import bootstrap_ci
from experiments.five_arm_report import exact_mcnemar


def _tail(ks: list[int], threshold: int) -> float:
    """P(|sum of ±k_i| >= threshold) with independent fair signs."""
    total = sum(ks)
    counts = {0: 1}
    for k in ks:
        nxt: dict[int, int] = {}
        for s, c in counts.items():
            nxt[s + k] = nxt.get(s + k, 0) + c
            nxt[s - k] = nxt.get(s - k, 0) + c
        counts = nxt
    hits = sum(c for s, c in counts.items() if abs(s) >= threshold)
    return hits / (2 ** len(ks)) if total else 1.0


def sign_flip_p(diffs: list[float], repeats: int) -> float:
    """The exact two-sided sign-flip p of the observed mean difference."""
    ks = [round(d * repeats) for d in diffs]
    for d, k in zip(diffs, ks):
        if abs(k - d * repeats) > 1e-6:
            raise ValueError(f"difference {d} is not a multiple of 1/{repeats}")
    nonzero = [abs(k) for k in ks if k]
    if not nonzero:
        return 1.0
    return _tail(nonzero, abs(sum(ks)))


def holm(pvalues: dict[str, float]) -> dict[str, float]:
    """Holm-adjusted p-values (monotone, capped at 1)."""
    order = sorted(pvalues, key=lambda name: pvalues[name])
    adjusted: dict[str, float] = {}
    running = 0.0
    for rank, name in enumerate(order):
        running = max(running, min(1.0, (len(order) - rank) * pvalues[name]))
        adjusted[name] = running
    return adjusted


def prompt_contrast(a: dict[str, list[int]], b: dict[str, list[int]], *, repeats: int, seed: int = 0,
                    n_boot: int = 10_000) -> dict:
    """Arm a against arm b over the prompts both ran, each a list of 0/1 outcomes of its repeats."""
    prompts = sorted(set(a) & set(b))
    for p in prompts:
        if len(a[p]) != repeats or len(b[p]) != repeats:
            raise ValueError(f"{p}: {len(a[p])} and {len(b[p])} runs, not {repeats} each")
    diffs = [sum(a[p]) / repeats - sum(b[p]) / repeats for p in prompts]
    low, high = bootstrap_ci(diffs, n_boot=n_boot, seed=seed) if diffs else (float("nan"), float("nan"))
    return {"prompts": len(prompts), "mean_a": sum(sum(a[p]) for p in prompts) / (repeats * len(prompts) or 1),
            "mean_b": sum(sum(b[p]) for p in prompts) / (repeats * len(prompts) or 1),
            "effect": sum(diffs) / len(diffs) if diffs else float("nan"), "ci95": [low, high],
            "p": sign_flip_p(diffs, repeats), "ahead": sum(d > 0 for d in diffs), "behind": sum(d < 0 for d in diffs),
            "tied": sum(d == 0 for d in diffs), "differences": dict(zip(prompts, diffs))}


def run_mcnemar(a: dict[tuple[str, int], int], b: dict[tuple[str, int], int]) -> dict:
    """Exact McNemar over runs matched by (prompt, repeat)."""
    keys = sorted(set(a) & set(b))
    only_a = sum(1 for k in keys if a[k] and not b[k])
    only_b = sum(1 for k in keys if b[k] and not a[k])
    return {"pairs": len(keys), "only_a": only_a, "only_b": only_b, "p": exact_mcnemar(only_a, only_b)}
