"""Stage-scope recipe (Sys1, L148): does an artifact stay inside the scope of the stage that produced it?

An artifact is conclusive when it holds content outside its stage's scope: a prompt that names a plan, a plan that
names an answer, a bootstrap analysis that does anything but extract the request's entities faithfully. System 1 is
asked which out-of-scope content the artifact contains, if any: one of its scope's out-of-scope categories, or NONE
(the user, after calibration 1: ask what is present). Each category belongs to another stage, or to the bootstrap's
own; the host sums System 1's probabilities. The artifact is conclusive when the out-of-scope total reaches GATE, or
when the content of any other stage reaches STAGE_FILTER (the user's deterministic filter, its threshold
calibrated); in scope when NONE reaches GATE; uncertain otherwise.

Adheres to GUARD-01, GUARD-02, GUARD-04: no regex pattern matching, no task keywords, System 1 decisions only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pdl_taskmaster.providers.sys1.recipes.base import Sys1Recipe, as_decision_instruction
from pdl_taskmaster.providers.sys1.schema import RecipeResult, Sys1Question, Sys1Request

GATE = 0.80  # the user's gate on the out-of-scope total and on NONE (L148)
STAGE_FILTER: float | None = 0.55  # any other stage's content at this mass halts (L148: calibration 2, pre-registered rule)
CONCLUSIVE, IN_SCOPE, UNCERTAIN = "CONCLUSIVE", "IN_SCOPE", "UNCERTAIN"
NONE = "NONE"
PROMPT, PLAN, EXECUTE, OWN = "PROMPT", "PLAN", "EXECUTE", "OWN"


@dataclass(frozen=True)
class Scope:
    name: str
    role: str
    in_scope: str  # what the artifact may contain (the NONE criterion)
    out_of_scope: dict[str, str]  # category -> criterion
    stage_of: dict[str, str]  # category -> the stage whose content it is (OWN: the artifact's own stage, done wrong)

    @property
    def choices(self) -> list[str]:
        return [*self.out_of_scope, NONE]


SCOPES: dict[str, Scope] = {
    "prompt": Scope(
        name="prompt",
        role="a prompt: it states what the task is, what is asked and under which constraints; the method and the "
             "result belong to later stages",
        in_scope="It contains only a restatement of the task, what is asked, and the constraints the request sets.",
        out_of_scope={
            "NAMES_METHOD": "It names a method, procedure, algorithm or plan for doing the task.",
            "STATES_RESULT": "It states the result the task asks for: an answer, value, choice, verdict or object.",
            "ASSUMES_RESULT": "It assumes or presupposes the result, or a fact that settles it, without stating it.",
        },
        stage_of={"NAMES_METHOD": PLAN, "STATES_RESULT": EXECUTE, "ASSUMES_RESULT": EXECUTE},
    ),
    "plan": Scope(
        name="plan",
        role="a plan: it states the method that will produce the deliverable; the result belongs to the deliverable",
        in_scope="It contains only the task as given, the method, steps or tools, and what will be checked.",
        out_of_scope={
            "STATES_RESULT": "It states the result the task asks for: an answer, value, choice, verdict or object.",
            "ASSUMES_RESULT": "It assumes or presupposes the result, or plans as if it were already known.",
            "PREVIEWS_PARTIAL": "It states part of the result before the deliverable: a defect's location, an "
                                "invariant, an intermediate value or fact that settles the answer.",
        },
        stage_of={"STATES_RESULT": EXECUTE, "ASSUMES_RESULT": EXECUTE, "PREVIEWS_PARTIAL": EXECUTE},
    ),
    "bootstrap": Scope(
        name="bootstrap",
        role="a bootstrap analysis: it extracts the request's entities and requirements faithfully, as the request "
             "states them; interpretation, method and result belong to later stages",
        in_scope="It records only what the request states, with each entity read correctly.",
        out_of_scope={
            "ADDS_UNSTATED_FACT": "It adds a fact, relation or inference the request does not state.",
            "RESOLVES_TARGET": "It gives the value or answer of something the request asks for.",
            "MISREADS_ENTITY": "It reads an entity wrongly, e.g. lists something given as asked for, or the reverse.",
            "NAMES_METHOD": "It names a method, procedure or plan for doing the task.",
        },
        stage_of={"ADDS_UNSTATED_FACT": PROMPT, "RESOLVES_TARGET": EXECUTE, "MISREADS_ENTITY": OWN,
                  "NAMES_METHOD": PLAN},
    ),
}


@dataclass(frozen=True)
class Item:
    """One artifact to judge: its key in the request state, its stage scope and its text."""

    key: str
    scope: str
    text: str


def verdict_from(answer: dict[str, Any], scope: Scope, stage_filter: float | None = None) -> dict[str, Any]:
    """The gate and the stage filter (L148). An answer outside the choices or without probabilities is UNCERTAIN."""
    stage_filter = STAGE_FILTER if stage_filter is None else stage_filter
    probabilities = answer.get("probabilities") if isinstance(answer, dict) else None
    choice = answer.get("choice") if isinstance(answer, dict) else None
    if not isinstance(probabilities, dict) or choice not in scope.choices:
        return {"verdict": UNCERTAIN, "category": choice, "out_total": None, "none": None, "stages": {},
                "probabilities": {}}
    known = {c: float(probabilities.get(c) or 0.0) for c in scope.choices}
    out_total = sum(known[c] for c in scope.out_of_scope)
    stages: dict[str, float] = {}
    for category, stage in scope.stage_of.items():
        if stage != OWN:
            stages[stage] = stages.get(stage, 0.0) + known[category]
    filtered = stage_filter is not None and any(mass >= stage_filter for mass in stages.values())
    verdict = (CONCLUSIVE if out_total >= GATE or filtered
               else IN_SCOPE if known[NONE] >= GATE else UNCERTAIN)
    return {"verdict": verdict, "category": choice, "out_total": round(out_total, 4), "none": round(known[NONE], 4),
            "stages": {k: round(v, 4) for k, v in stages.items()}, "filtered": filtered,
            "probabilities": {c: round(p, 4) for c, p in known.items()}}


class StageScopeRecipe(Sys1Recipe):
    """One question per artifact: which out-of-scope content it contains, if any."""

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
                    f"The supplied '{item.key}' is {scope.role}. Compare it with the user's source request. Which "
                    f"content outside the stage's scope does it contain, if any? Any amount counts, even one clause "
                    f"in an otherwise in-scope text. Choose that category, or {NONE} if it contains none."
                ),
                criteria={**scope.out_of_scope, NONE: scope.in_scope},
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
