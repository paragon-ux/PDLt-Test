"""Blind adjudication: which rows a human checks, and how verdicts become the audited score.

The audit is symmetric (design §12.4). It covers:
- every pending row (a MANUAL or N/A grade);
- **every** discordant pair of the decision comparisons, in both directions;
- a random 20% of the concordant pairs.

A one-directional audit would correct grader errors in one direction only, which
biases the result. The audited score is the human verdict where one exists,
otherwise the automated primary score. The decision rules read the audited score.
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path
from typing import Any

DECISION_PAIRS = (("P_new", "P_old"), ("P_new", "C0"), ("P_unc", "C0"), ("P_unc", "P_old"))
CONCORDANT_SHARE = 0.2


def _key(row: dict[str, Any]) -> tuple[str, str, str, int]:
    return row["model"], row["arm"], row["item_id"], int(row["rep"])


def queue(rows: list[dict[str, Any]], *, seed: int, pairs=DECISION_PAIRS,
          concordant_share: float = CONCORDANT_SHARE) -> list[dict[str, Any]]:
    """The rows to adjudicate, deduplicated, in a stable order."""
    by_key = {_key(r): r for r in rows}
    chosen: dict[tuple, dict[str, Any]] = {}
    for row in rows:
        if (row.get("scores") or {}).get("primary") is None:
            chosen[_key(row)] = row
    rng = random.Random(seed)
    for arm_a, arm_b in pairs:
        concordant = []
        for (model, arm, item, rep), row in sorted(by_key.items()):
            if arm != arm_a:
                continue
            other = by_key.get((model, arm_b, item, rep))
            if other is None:
                continue
            a, b = row["scores"].get("primary"), other["scores"].get("primary")
            if a is None or b is None:
                continue
            if a != b:
                chosen[_key(row)], chosen[_key(other)] = row, other
            else:
                concordant.append((row, other))
        for row, other in rng.sample(concordant, round(len(concordant) * concordant_share)):
            chosen[_key(row)], chosen[_key(other)] = row, other
    return [chosen[k] for k in sorted(chosen)]


def read_verdicts(sheet: Path, key: Path) -> dict[tuple[str, str, str, int], int]:
    """Human verdicts from a filled sheet, mapped back through the key. PASS -> 1, FAIL -> 0."""
    ids = {}
    for line in Path(key).read_text(encoding="utf-8").splitlines():
        if line.strip():
            entry = json.loads(line)
            ids[entry["review_id"]] = (entry["model"], entry["arm"], entry["item_id"], int(entry["rep"]))
    verdicts = {}
    with Path(sheet).open(encoding="utf-8", newline="") as handle:
        for record in csv.DictReader(handle):
            verdict = (record.get("verdict (PASS/FAIL)") or "").strip().upper()
            if verdict in ("PASS", "FAIL") and record["review_id"] in ids:
                verdicts[ids[record["review_id"]]] = 1 if verdict == "PASS" else 0
    return verdicts


def apply(rows: list[dict[str, Any]], verdicts: dict[tuple[str, str, str, int], int]) -> list[dict[str, Any]]:
    """Rows with scores["audited"] set: the verdict where one exists, else the primary score."""
    audited = []
    for row in rows:
        scores = dict(row.get("scores") or {})
        scores["audited"] = verdicts.get(_key(row), scores.get("primary"))
        audited.append({**row, "scores": scores})
    return audited
