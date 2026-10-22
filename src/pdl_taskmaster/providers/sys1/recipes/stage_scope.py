"""Stage-scope recipe (Sys1, L148): does an artifact stay inside the scope of the stage that produced it?

An artifact is conclusive when it holds content outside its stage's scope: a prompt that names a plan, a plan that
names an answer, a bootstrap analysis that does anything but extract the request's entities faithfully. System 1
picks a category for each artifact; the categories are split into in-scope and out-of-scope reasons, and the host
sums System 1's probability over each set (a split between two out-of-scope reasons is still conclusive). The
categories and the gate were fixed by the user before any calibration (L148).

Adheres to GUARD-01, GUARD-02, GUARD-04: no regex pattern matching, no task keywords, System 1 decisions only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

GATE = 0.80
CONCLUSIVE, IN_SCOPE, UNCERTAIN = "CONCLUSIVE", "IN_SCOPE", "UNCERTAIN"


@dataclass(frozen=True)
class Scope:
    role: str
    in_scope: dict[str, str]
    out_of_scope: dict[str, str]

    @property
    def choices(self) -> list[str]:
        return [*self.in_scope, *self.out_of_scope]


SCOPES: dict[str, Scope] = {
    "prompt": Scope(
        role="a prompt: it states what the task is, what is asked and under which constraints; the method and the "
             "result belong to later stages",
        in_scope={
            "RESTATES_TASK": "It restates the task, its subjects and its givens as the request states them.",
            "NAMES_TARGET": "It names what is to be found, determined or produced, without its value.",
            "STATES_CONSTRAINT": "It states a constraint, condition or requirement the request sets.",
        },
        out_of_scope={
            "NAMES_METHOD": "It names a method, procedure, algorithm or plan for doing the task.",
            "STATES_RESULT": "It states the result the task asks for: an answer, value, choice, verdict or object.",
            "ASSUMES_RESULT": "It assumes or presupposes the result, or a fact that settles it, without stating it.",
        },
    ),
    "plan": Scope(
        role="a plan: it states the method that will produce the deliverable; the result belongs to the deliverable",
        in_scope={
            "RESTATES_TASK": "It restates the task, its subjects and its givens as the request states them.",
            "NAMES_METHOD": "It names the method, steps, procedure or tools that will produce the result.",
            "NAMES_CHECK": "It names what will be checked, tested or verified, without the outcome.",
        },
        out_of_scope={
            "STATES_RESULT": "It states the result the task asks for: an answer, value, choice, verdict or object.",
            "ASSUMES_RESULT": "It assumes or presupposes the result, or plans as if it were already known.",
            "PREVIEWS_PARTIAL": "It states part of the result before the deliverable: a defect's location, an "
                                "invariant, an intermediate value or fact that settles the answer.",
        },
    ),
    "bootstrap": Scope(
        role="a bootstrap analysis: it extracts the request's entities and requirements faithfully, as the request "
             "states them; interpretation, method and result belong to later stages",
        in_scope={
            "FAITHFUL_EXTRACTION": "It records only what the request states, with each entity read correctly.",
        },
        out_of_scope={
            "ADDS_UNSTATED_FACT": "It adds a fact, relation or inference the request does not state.",
            "RESOLVES_TARGET": "It gives the value or answer of something the request asks for.",
            "MISREADS_ENTITY": "It reads an entity wrongly, e.g. lists something given as asked for, or the reverse.",
            "NAMES_METHOD": "It names a method, procedure or plan for doing the task.",
        },
    ),
}


@dataclass(frozen=True)
class Item:
    """One artifact to judge: its key in the request state, its stage scope and its text."""

    key: str
    scope: str
    text: str


def verdict_from(answer: dict[str, Any], scope: Scope) -> dict[str, Any]:
    """The gate (L148): the out-of-scope total at least GATE is CONCLUSIVE, the in-scope total at least GATE is
    IN_SCOPE, anything else (a real split, or an answer outside the categories) is UNCERTAIN."""
    probabilities = answer.get("probabilities") if isinstance(answer, dict) else None
    choice = answer.get("choice") if isinstance(answer, dict) else None
    if not isinstance(probabilities, dict) or choice not in scope.choices:
        return {"verdict": UNCERTAIN, "category": choice, "out_total": None, "in_total": None, "probabilities": {}}
    known = {c: float(probabilities.get(c) or 0.0) for c in scope.choices}
    out_total = sum(known[c] for c in scope.out_of_scope)
    in_total = sum(known[c] for c in scope.in_scope)
    verdict = CONCLUSIVE if out_total >= GATE else IN_SCOPE if in_total >= GATE else UNCERTAIN
    return {"verdict": verdict, "category": choice, "out_total": round(out_total, 4), "in_total": round(in_total, 4),
            "probabilities": {c: round(p, 4) for c, p in known.items()}}


class StageScopeRecipe(Sys1Recipe):
    """One question per artifact; each answered with a category of its stage's scope."""

    def __init__(self, items: list[Item]) -> None:
        unknown = [item.scope for item in items if item.scope not in SCOPES]
        if unknown or not items:
            raise ValueError(f"stage scope: unknown or no scopes {unknown}")
        self.items = items

    @property
    def name(self) -> str:
        return "stage-scope"

    @property
    def min_confidence(self) -> float:
        return GATE

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Sys1Request:
        questions = {}
        for item in self.items:
            scope = SCOPES[item.scope]
            questions[f"{item.key}_scope"] = Sys1Question(
                instructions=as_decision_instruction(
                    f"The supplied '{item.key}' is {scope.role}. Compare it with the user's source request and "
                    f"choose the one category that best describes its content. Choose a category of content outside "
                    f"the stage's scope whenever any part of it is outside that scope."
                ),
                criteria={**scope.in_scope, **scope.out_of_scope},
                choices=scope.choices,
            )
        return Sys1Request(
            state={"source_request": state.get("source_request", ""),
                   **({"confirmed_prompt": state["confirmed_prompt"]} if state.get("confirmed_prompt") else {}),
                   **{item.key: item.text for item in self.items}},
            questions=questions,
        )

    def parse_response(self, response_body: dict[str, Any], *, duration_ms: float = 0.0) -> RecipeResult:
        answers = response_body.get("answers") or {}
        per_item = {item.key: {"scope": item.scope,
                               **verdict_from(answers.get(f"{item.key}_scope") or {}, SCOPES[item.scope])}
                    for item in self.items}
        verdicts = [d["verdict"] for d in per_item.values()]
        verdict = CONCLUSIVE if CONCLUSIVE in verdicts else UNCERTAIN if UNCERTAIN in verdicts else IN_SCOPE
        totals = [d["out_total"] for d in per_item.values() if d["out_total"] is not None]
        top = max(totals) if totals else 0.0
        return RecipeResult(
            status="ready" if verdict != UNCERTAIN else "review",
            verdict=verdict,
            confidence=top if verdict == CONCLUSIVE else 1.0 - top if totals else 0.0,
            margin=0.0,
            entropy=0.0,
            passed_gating=verdict != UNCERTAIN,
            duration_ms=duration_ms,
            labels={"items": per_item},
            metadata=response_body.get("metadata", {}),
        )

    def map_to_wire(self, result: RecipeResult) -> dict[str, Any]:
        return {"verdict": result.verdict, "items": (result.labels or {}).get("items", {})}
