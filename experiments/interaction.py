"""The interaction groups (design §6.6): the ambiguity group A and the multi-turn group M.

**A: ambiguity.** Each item (`prompts/ambiguity/A-NN.{txt,json}`) has:
- a request with several plausible readings;
- the intended reading, fixed before any run and never shown to the model;
- one written correction.

The **scripted reviewer** decides from the artifact under review, never from the
run's outcome. The judges grade the artifact against the item's review rubric
(`rubrics/A-NN-review.json`):
- both say the intended reading -> `/confirm`;
- otherwise -> `/revise <correction>`, at most once per run (after a revision,
  the next artifact is confirmed whatever it says, so a run cannot loop).

The plain-call and ultrafast arms get the same correction as a **follow-up** when
the judges say their answer took another reading (`rubrics/A-NN-answer.json`).

**M: multi-turn.** Category 10's own scripts:
- the protocol arm gets them as piped review commands and turns;
- the plain-call arms get them as follow-up messages.

10-06 (switching the result mode at plan review) has no plain-call equivalent:
it stays a protocol-only check and is not compared across arms.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from experiments import judge as judges

AMBIGUITY = Path(__file__).resolve().parent / "prompts" / "ambiguity"


@dataclass(frozen=True)
class AmbiguityItem:
    id: str
    request: str
    intended: str
    correction: str

    @property
    def review_rubric(self) -> str:
        return f"{self.id}-review"

    @property
    def answer_rubric(self) -> str:
        return f"{self.id}-answer"


def ambiguity_items() -> dict[str, AmbiguityItem]:
    out = {}
    for meta in json.loads((AMBIGUITY / "MANIFEST.json").read_text(encoding="utf-8")):
        request = (AMBIGUITY / meta["file"]).read_text(encoding="utf-8").strip()
        out[meta["id"]] = AmbiguityItem(meta["id"], request, meta["intended"], meta["correction"])
    return out


def review_reply(item: AmbiguityItem, artifact: str, specs: list[judges.JudgeSpec], send: judges.Sender, *,
                 revised: bool) -> tuple[str, dict[str, Any]]:
    """The scripted reviewer's reply at one review gate, and the judges' verdicts.

    Every artifact is judged (the log shows whether a revision fixed the reading).
    Only the first non-PASS artifact of a run gets the correction; after that the
    reviewer confirms, so a run cannot loop."""
    verdicts = judges.judge(judges.load_rubric(item.review_rubric), item.request, artifact, specs, send)
    if revised or judges.settled(verdicts) == "PASS":
        return "/confirm", verdicts
    return f"/revise {item.correction}", verdicts


def needs_followup(item: AmbiguityItem, answer: str, specs: list[judges.JudgeSpec],
                   send: judges.Sender) -> tuple[bool, dict[str, Any]]:
    """True when the answer did not settle on the intended reading (a disagreement counts as not settled)."""
    verdicts = judges.judge(judges.load_rubric(item.answer_rubric), item.request, answer, specs, send)
    return judges.settled(verdicts) != "PASS", verdicts


# --------------------------------------------------------------------------- M: category 10 scripts

@dataclass(frozen=True)
class MultiTurnScript:
    id: str
    protocol_stdin: str          # piped lines for the protocol arm, exactly one per review gate or turn
    followups: tuple[str, ...]   # follow-up messages for the plain-call and ultrafast arms
    exit_on_close: bool = True   # False when the script opens a second instance after the first closes
    compared: bool = True        # False: protocol-only check, not compared across arms


def _lines(*lines: str) -> str:
    return "".join(line + "\n" for line in lines)


_PRIMES = "Only find primes up to 100, and also return the count of twin primes found."
_STDLIB = "Don't use requests or beautifulsoup; use only the standard library html.parser module."
_CLI = "Actually, build a CLI tool that wraps the JSONPlaceholder API instead of a library."
_EMAIL = ("Also validate that the domain has at least one dot",
          "Add support for plus-addressing (user+tag@domain.com)",
          "Return a structured result with {valid: bool, local_part: str, domain: str, tag: str|None}")
_ROT13 = "Implement a ROT13 encoder."
_FIZZ = "Now explain the time complexity of your FizzBuzz implementation and whether it could be optimized."

MULTI_TURN: dict[str, MultiTurnScript] = {
    # Revise at prompt review, then confirm the prompt and the plan.
    "10-01": MultiTurnScript("10-01", _lines(f"/revise {_PRIMES}", "/confirm", "/confirm"), (_PRIMES,)),
    # Confirm the prompt, revise the plan, confirm the revised plan.
    "10-02": MultiTurnScript("10-02", _lines("/confirm", f"/revise {_STDLIB}", "/confirm"), (_STDLIB,)),
    # Confirm the prompt; at plan review, change the requirement; confirm what follows.
    "10-03": MultiTurnScript("10-03", _lines("/confirm", f"/revise {_CLI}", "/confirm", "/confirm"), (_CLI,)),
    # Three revisions of the prompt in sequence, then confirm the prompt and the plan.
    "10-04": MultiTurnScript("10-04", _lines(*(f"/revise {r}" for r in _EMAIL), "/confirm", "/confirm"), _EMAIL),
    # Stop at prompt review and start a different task in the same session.
    "10-05": MultiTurnScript("10-05", _lines("/stop", _ROT13, "/confirm", "/confirm"), (_ROT13,), exit_on_close=False),
    # Result-mode switch at plan review: protocol only.
    "10-06": MultiTurnScript("10-06", _lines("/confirm", "/confirm"), (), compared=False),
    # A follow-up turn after the first closes (a direct answer ends the piped lines).
    "10-07": MultiTurnScript("10-07", _lines("/confirm", "/confirm", _FIZZ, "/confirm", "/confirm"), (_FIZZ,),
                             exit_on_close=False),
}


def conversation(request: str, exchanges: list[tuple[str, str]]) -> list[dict[str, str]]:
    """The /responses input for a plain call's next turn: the request, then each
    (the model's answer, the user's follow-up) exchange so far."""
    messages = [{"role": "user", "content": request}]
    for answer, followup in exchanges:
        messages += [{"role": "assistant", "content": answer}, {"role": "user", "content": followup}]
    return messages
