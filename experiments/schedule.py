"""The gate's run order and its append-only ledger (design §9.2).

**Schedule.**
- Fixed by a seed, before Day 1.
- Per model: every repetition-1 block, then every repetition-2 block, each pass in
  its own random prompt order.
- Within a block, the arms run in a random order. A branched arm's branches run in
  a random order after its trunk.
- Models are interleaved block by block, so both run under the same conditions.

**Ledger.**
- An append-only JSONL file.
- A crash or restart resumes at the first block with an unfinished arm, so nothing
  is duplicated or skipped.
- An outage voids the whole block, which is re-run (at most ``MAX_BLOCK_RERUNS``
  times) and never partly kept.
"""
from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

MAX_BLOCK_RERUNS = 2


@dataclass(frozen=True)
class Block:
    block_id: str
    model: str
    item_id: str
    rep: int
    arms: tuple[str, ...]  # run order
    branches: dict[str, tuple[str, ...]] = field(default_factory=dict)  # branched arm -> branch run order

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "arms": list(self.arms), "branches": {k: list(v) for k, v in self.branches.items()}}


def build_schedule(models: list[str], item_ids: list[str], *, reps: int, arms: list[str],
                   branches: dict[str, list[str]] | None = None, seed: int) -> list[Block]:
    rng = random.Random(seed)
    per_model: dict[str, list[Block]] = {}
    for model in models:
        blocks: list[Block] = []
        for rep in range(1, reps + 1):
            order = list(item_ids)
            rng.shuffle(order)
            for item_id in order:
                arm_order = list(arms)
                rng.shuffle(arm_order)
                branch_order = {}
                for arm, names in (branches or {}).items():
                    shuffled = list(names)
                    rng.shuffle(shuffled)
                    branch_order[arm] = tuple(shuffled)
                blocks.append(Block(f"{model}:{item_id}:r{rep}", model, item_id, rep, tuple(arm_order), branch_order))
        per_model[model] = blocks
    interleaved: list[Block] = []
    for index in range(max((len(b) for b in per_model.values()), default=0)):
        for model in models:
            if index < len(per_model[model]):
                interleaved.append(per_model[model][index])
    return interleaved


class Ledger:
    """Append-only record of finished arm runs. A row:
    ``{block_id, attempt, arm, branch, status, ...}``, where status is ``done``,
    ``void`` or ``dropped``. ``arm`` is the label the analysis reads: a branch's
    own name for a branched arm, whose row also records ``unit_arm`` (the arm in
    the config)."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def rows(self) -> list[dict[str, Any]]:
        if not self.path.is_file():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    def append(self, row: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    def attempt(self, block_id: str) -> int:
        """The block's current attempt: 1, plus one per voided attempt."""
        return 1 + sum(1 for r in self.rows() if r["block_id"] == block_id and r["status"] == "void")

    def done_units(self, block_id: str) -> set[tuple[str, str | None]]:
        attempt = self.attempt(block_id)
        return {(r.get("unit_arm", r["arm"]), r.get("branch")) for r in self.rows()
                if r["block_id"] == block_id and r.get("attempt") == attempt and r["status"] == "done"}

    def void_block(self, block_id: str, reason: str) -> int:
        """An outage voids every arm run of the block's current attempt; returns the next attempt."""
        attempt = self.attempt(block_id)
        self.append({"block_id": block_id, "attempt": attempt, "arm": "*", "branch": None, "status": "void",
                     "reason": reason})
        return attempt + 1

    def results(self) -> list[dict[str, Any]]:
        """Finished rows of each block's last attempt: the rows the analysis reads."""
        rows = self.rows()
        voids: dict[str, int] = {}
        for r in rows:
            if r["status"] == "void":
                voids[r["block_id"]] = voids.get(r["block_id"], 0) + 1
        return [r for r in rows if r["status"] == "done" and r.get("attempt") == 1 + voids.get(r["block_id"], 0)]


def pending_blocks(schedule: Iterable[Block], ledger: Ledger, units: dict[str, list[tuple[str, str | None]]]) \
        -> list[Block]:
    """Blocks with an unfinished unit. ``units[block_id]`` lists the (arm, branch) pairs it needs."""
    return [b for b in schedule if set(units[b.block_id]) - ledger.done_units(b.block_id)]
