"""Task types (task-type profile v1, ``pdlt.task-type/1``; L120 B2).

A task type is a category of request and what the host does with it, declared as data against the fixed stages:

    profile        "pdlt.task-type/1"
    category       the problem class, e.g. VERIFIED_EXECUTION
    prompt         classification: how System 1 recognises the category (a recipe, a criterion, or none);
                   instructions: which host-rendered instruction channels EXECUTE receives (result_ir, witness)
    witness_forms  the witness forms accepted (ADR-0030: computed, certificate, argued, negative); may be empty
    deliverable    body "text"; result_ir "required" or "not_requested"
    route          the fixed routes it runs on: confirmed, unconfirmed
    operations     the contract operations it uses: every required one of each route, plus optional ones
    verifier       a registered verifier's name, or "none"

No component carries text to the solver: a task type selects among channels the host renders, and its
classification text goes to System 1 only (GUARD-01). Stages, review gates and execution modes are not part of a
task type. Every task type, the built-ins included, enters through register_task_type().

Routing (select()): a pinned task type is used as given. Otherwise each task type with a classification recipe that
runs on the turn's route is asked in registration order; the first whose recipe chooses its category, passing the
gate and the core confidence floor, is selected. Anything else (no System 1, an error, a verdict below the floor, a
verdict naming no registered category) goes to the default task type, which must be safe: no verifier, no witness,
both routes, no recipe. A category with no recipe is reachable only by pinning.
"""
from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from pdl_taskmaster.extensions import verifiers
from pdl_taskmaster.extensions.profiles import Component, Invariant, Profile, Registry, unique_strings

PROFILE_ID = "pdlt.task-type/1"
CATEGORY = re.compile(r"^[A-Z][A-Z0-9_]{2,63}$")
OTHER = "OTHER"  # the criterion recipe's other choice; not a category
CLASSIFICATION_FLOOR = 0.85  # the core floor a classification must reach, whatever the recipe declares
CRITERION_CHARS = (20, 600)

INSTRUCTIONS = ("result_ir", "witness")
WITNESS_FORMS = ("computed", "certificate", "argued", "negative")
REPRODUCIBLE = frozenset({"computed", "certificate"})  # the forms a program the host runs can print
RESULT_IR = ("required", "not_requested")
BODIES = ("text",)


@dataclass(frozen=True)
class RouteOperations:
    required: frozenset[str]
    optional: frozenset[str]


_REVIEWS = frozenset({"BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "INTERPRET_PROMPT_REVIEW", "REVISE_PROMPT", "DRAFT_PLAN",
                      "INTERPRET_PLAN_REVIEW", "REVISE_PLAN", "EXECUTE", "INTERPRET_EXECUTION_INPUT"})
# The fixed routes and the operations their stages call (runtime/session_engine.py). Session-level operations
# (INTERPRET_ACTIVATION, ANSWER_PROTOCOL_DISCUSSION) belong to no task type.
ROUTES: dict[str, RouteOperations] = {
    "confirmed": RouteOperations(required=_REVIEWS, optional=frozenset({"DRAFT_EXECUTE"})),
    "unconfirmed": RouteOperations(
        required=frozenset({"BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED", "INTERPRET_EXECUTION_INPUT"}),
        optional=frozenset({"DRAFT_EXECUTE"})),
}


@dataclass(frozen=True)
class TaskType:
    category: str
    recipe: Any  # a System 1 recipe (providers/sys1/recipes/base.py Sys1Recipe), or None
    selects: str | None
    instructions: frozenset[str]
    witness_forms: frozenset[str]
    result_ir: bool
    routes: frozenset[str]
    operations: frozenset[str]
    verifier: str  # a registered verifier's name, or "none"
    profile: str = PROFILE_ID
    # The declaration as registered (a copy: later changes to the caller's mapping do not reach it).
    declaration: Any = field(default=None, compare=False, repr=False)

    @property
    def requires_witness(self) -> bool:
        return self.verifier != "none"

    def domain(self) -> Any:
        """The verification domain of a turn of this type: the bound verifier's, or None."""
        if not self.requires_witness:
            return None
        from pdl_taskmaster.verification.checkers.base import ProblemDomain

        domain = verifiers.REGISTRY.get(self.verifier).domain
        return ProblemDomain.from_string(domain) or domain


class CriterionRecipe:
    """System 1 recognises a category from its criterion: one question, the category or OTHER. The instruction is
    the host's; only the criterion text is the task type's."""

    def __init__(self, category: str, criterion: str):
        self.category = category
        self.criterion = criterion

    @property
    def name(self) -> str:
        return f"task-type:{self.category}"

    @property
    def min_confidence(self) -> float:
        return CLASSIFICATION_FLOOR

    def build_request(self, state: dict[str, Any], **kwargs: Any) -> Any:
        from pdl_taskmaster.providers.sys1.recipes.base import as_decision_instruction
        from pdl_taskmaster.providers.sys1.schema import Sys1Question, Sys1Request

        question = Sys1Question(
            instructions=as_decision_instruction(
                "Classify whether this task belongs to the category the criteria describe."),
            criteria={self.category: self.criterion, OTHER: "The task does not meet the criterion above."},
            choices=[self.category, OTHER],
        )
        return Sys1Request(state={"request": state.get("request", "")}, questions={"task_type": question})

    def parse_response(self, response_body: dict[str, Any], *, duration_ms: float = 0.0) -> Any:
        from pdl_taskmaster.providers.sys1.gating import evaluate_confidence_gate
        from pdl_taskmaster.providers.sys1.schema import RecipeResult

        answer = response_body.get("answers", {}).get("task_type", {})
        gating = evaluate_confidence_gate(answer, confidence_floor=self.min_confidence)
        return RecipeResult(status="ready" if gating.passed else "review", verdict=gating.choice or OTHER,
                            confidence=gating.confidence, margin=gating.margin, entropy=gating.entropy,
                            passed_gating=gating.passed, probabilities=gating.probabilities,
                            duration_ms=duration_ms, metadata=response_body.get("metadata", {}))

    def map_to_wire(self, result: Any) -> dict[str, Any]:
        return {"category": self.category if result.verdict == self.category else None,
                "confidence": result.confidence}


# ---- the profile: components ------------------------------------------------------------------------------------

def _category(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    if not isinstance(value, str) or not CATEGORY.match(value):
        return [f"upper-case letters, digits and underscores, 3-64 characters, are required, got {value!r}"]
    return [f"{OTHER!r} is reserved"] if value == OTHER else []


def _classification(value: Any, category: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Mapping):
        return [f"classification: None, {{'criterion': text}} or {{'recipe': recipe, 'selects': category}} is "
                f"required, got {value!r}"]
    if set(value) == {"criterion"}:
        text = value["criterion"]
        low, high = CRITERION_CHARS
        if not isinstance(text, str) or not low <= len(text.strip()) <= high:
            return [f"classification.criterion: text of {low}-{high} characters is required"]
        return []
    if set(value) != {"recipe", "selects"}:
        return [f"classification: keys must be 'criterion', or 'recipe' and 'selects', got {sorted(value)}"]
    recipe, selects = value["recipe"], value["selects"]
    problems = []
    if selects != category:
        problems.append(f"classification.selects: a recipe may select only its own category {category!r}, "
                        f"got {selects!r}")
    for method in ("build_request", "parse_response", "map_to_wire"):
        if not callable(getattr(recipe, method, None)):
            problems.append(f"classification.recipe: {method}() is missing")
    if not isinstance(getattr(recipe, "name", None), str):
        problems.append("classification.recipe: a string name is required")
    floor = getattr(recipe, "min_confidence", None)
    if not isinstance(floor, (int, float)) or not CLASSIFICATION_FLOOR <= floor <= 1:
        problems.append(f"classification.recipe: min_confidence must be in [{CLASSIFICATION_FLOOR}, 1], got {floor!r}")
    if problems:
        return problems
    try:
        request = recipe.build_request({"request": "A request to classify."})
        choices = [c for q in request.questions.values() for c in (q.choices or list(q.criteria))]
    except Exception as exc:
        return [f"classification.recipe: build_request() failed ({type(exc).__name__}: {exc})"]
    return [] if selects in choices else [
        f"classification.recipe: its question never offers {selects!r} (choices: {choices})"]


def _prompt(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    if not isinstance(value, Mapping) or set(value) != {"classification", "instructions"}:
        return [f"keys 'classification' and 'instructions' are required, got {value!r}"]
    return (_classification(value["classification"], declaration.get("category"))
            + [f"instructions: {p}" for p in unique_strings(value["instructions"], INSTRUCTIONS)])


def _witness_forms(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    return unique_strings(value, WITNESS_FORMS)


def _deliverable(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    if not isinstance(value, Mapping) or set(value) != {"body", "result_ir"}:
        return [f"keys 'body' and 'result_ir' are required, got {value!r}"]
    problems = [] if value["body"] in BODIES else [f"body: must be one of {list(BODIES)}, got {value['body']!r}"]
    if value["result_ir"] not in RESULT_IR:
        problems.append(f"result_ir: must be one of {list(RESULT_IR)}, got {value['result_ir']!r}")
    return problems


def _route(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    return unique_strings(value, tuple(ROUTES), non_empty=True)


def _operations(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    known = frozenset().union(*(r.required | r.optional for r in ROUTES.values()))
    return unique_strings(value, known, non_empty=True)


def _verifier(value: Any, declaration: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    if value == "none" or value in verifiers.REGISTRY:
        return []
    return [f"'none' or a registered verifier is required, got {value!r} (registered: {verifiers.REGISTRY.names()})"]


# ---- the profile: invariants ------------------------------------------------------------------------------------

def _result_ir_channel(d: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    channel = "result_ir" in d["prompt"]["instructions"]
    required = d["deliverable"]["result_ir"] == "required"
    return [] if channel == required else [
        "the result_ir instruction is sent exactly when the deliverable requires a Result IR"]


def _witness_binding(d: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    channel = "witness" in d["prompt"]["instructions"]
    forms = bool(d["witness_forms"])
    bound = d["verifier"] != "none"
    if channel == forms == bound:
        return []
    return ["a witness is asked for (instruction 'witness'), accepted (witness_forms) and checked (verifier) "
            f"together or not at all; got instruction={channel}, forms={forms}, verifier={d['verifier']!r}"]


def _witness_in_result_ir(d: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    instructions = d["prompt"]["instructions"]
    return [] if "witness" not in instructions or "result_ir" in instructions else [
        "the witness travels in the Result IR: instruction 'witness' needs instruction 'result_ir'"]


def _reproducible(d: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    if d["verifier"] == "none" or REPRODUCIBLE & set(d["witness_forms"]):
        return []
    return [f"a bound verifier needs a form the host can reproduce ({sorted(REPRODUCIBLE)}) among the accepted forms"]


def _operations_cover_routes(d: Mapping[str, Any], registry: Registry[Any]) -> list[str]:
    operations = set(d["operations"])
    problems = [f"route {r!r} needs {sorted(ROUTES[r].required - operations)}"
                for r in d["route"] if ROUTES[r].required - operations]
    allowed = frozenset().union(*(ROUTES[r].required | ROUTES[r].optional for r in d["route"]))
    stray = sorted(operations - allowed)
    if stray:
        problems.append(f"{stray} belong to no declared route")
    return problems


PROFILE = Profile(
    kind="task-type",
    version=1,
    components=(
        Component("category", "the problem class this task type answers for", _category),
        Component("prompt", "classification (recipe, criterion or None) and the host-rendered instruction channels "
                            "EXECUTE receives", _prompt),
        Component("witness_forms", "the accepted witness forms (ADR-0030); may be empty", _witness_forms),
        Component("deliverable", "the deliverable form: body 'text'; result_ir 'required' or 'not_requested'",
                  _deliverable),
        Component("route", "the fixed routes it runs on", _route),
        Component("operations", "the contract operations it uses", _operations),
        Component("verifier", "a registered verifier, or 'none'", _verifier),
    ),
    invariants=(
        Invariant("result-ir-channel", "the result_ir instruction matches the deliverable", _result_ir_channel),
        Invariant("witness-binding", "a witness is asked for, accepted and checked together", _witness_binding),
        Invariant("witness-in-result-ir", "the witness travels in the Result IR", _witness_in_result_ir),
        Invariant("reproducible", "a bound verifier has a reproducible form to check", _reproducible),
        Invariant("operations-cover-routes", "each declared route's operations are all declared",
                  _operations_cover_routes),
    ),
)

SAFE_DEFAULT = ("the default task type is what an unclassified request gets: no verifier, no witness forms, "
                "both routes, and no classification recipe")


def _snapshot(value: Any) -> Any:
    """Mappings and lists copied all the way down; any other object (a recipe) kept as it is."""
    if isinstance(value, Mapping):
        return {k: _snapshot(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_snapshot(v) for v in value]
    return value


def _build(d: Mapping[str, Any]) -> TaskType:
    classification = d["prompt"]["classification"]
    recipe, selects = None, None
    if classification is not None and "criterion" in classification:
        recipe, selects = CriterionRecipe(d["category"], classification["criterion"].strip()), d["category"]
    elif classification is not None:
        recipe, selects = classification["recipe"], classification["selects"]
    return TaskType(category=d["category"], recipe=recipe, selects=selects,
                    instructions=frozenset(d["prompt"]["instructions"]), witness_forms=frozenset(d["witness_forms"]),
                    result_ir=d["deliverable"]["result_ir"] == "required", routes=frozenset(d["route"]),
                    operations=frozenset(d["operations"]), verifier=d["verifier"], declaration=_snapshot(d))


class TaskTypeRegistry(Registry[TaskType]):
    def __init__(self) -> None:
        super().__init__(PROFILE, key="category", build=_build)
        self._default: str | None = None

    def register(self, declaration: Mapping[str, Any], *, replace: bool = False,
                 default: bool = False) -> TaskType:
        if default:
            from pdl_taskmaster.extensions.profiles import ProfileViolation

            problems = self.profile.problems(declaration, self)
            if not problems and not _safe_default(declaration):
                raise ProfileViolation(self.profile.id, declaration.get("category"), [f"default: {SAFE_DEFAULT}"])
        item = super().register(declaration, replace=replace)
        if default:
            self._default = item.category
        return item

    @property
    def default(self) -> TaskType:
        if self._default is None or self._default not in self:
            raise LookupError("no default task type is registered")
        return self.get(self._default)

    def classified(self, route: str) -> list[TaskType]:
        return [t for t in self.items() if t.recipe is not None and route in t.routes]

    def _state(self) -> Any:
        return dict(self._items), self._default

    def _restore(self, state: Any) -> None:
        self._items, self._default = state


def _safe_default(d: Mapping[str, Any]) -> bool:
    return (d["verifier"] == "none" and not d["witness_forms"] and set(d["route"]) == set(ROUTES)
            and d["prompt"]["classification"] is None)


REGISTRY = TaskTypeRegistry()


def register_task_type(declaration: Mapping[str, Any], *, replace: bool = False, default: bool = False) -> TaskType:
    """Validate ``declaration`` against task-type profile v1 and register it; a non-conforming one is refused with
    every problem named (ProfileViolation)."""
    return REGISTRY.register(declaration, replace=replace, default=default)


# ---- routing ----------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class Selection:
    task_type: TaskType
    how: str  # "pinned", "classified" or "default"
    # One entry per recipe asked, in order: its verdict and gate figures, or None when the call failed.
    classifications: list[dict[str, Any] | None] = field(default_factory=list)


def select(request: str, sys1_client: Any, route: str, *, pinned: str | None = None,
           registry: TaskTypeRegistry | None = None) -> Selection:
    registry = registry or REGISTRY
    if pinned is not None:
        task_type = registry.get(pinned)
        if route not in task_type.routes:
            raise ValueError(f"task type {pinned!r} does not run on the {route} route")
        return Selection(task_type, "pinned")
    asked: list[dict[str, Any] | None] = []
    if sys1_client and getattr(sys1_client, "is_configured", False):
        for task_type in registry.classified(route):
            try:
                request_body = task_type.recipe.build_request({"request": request})
                body, duration_ms = sys1_client.call(request_body)
                result = task_type.recipe.parse_response(body, duration_ms=duration_ms)
                asked.append({"verdict": result.verdict, "confidence": round(result.confidence, 4),
                              "passed_gating": result.passed_gating, "margin": round(result.margin, 4),
                              "entropy": round(result.entropy, 4),
                              "distribution": {k: round(v, 4) for k, v in result.probabilities.items()}})
            except Exception:
                asked.append(None)  # a failed classification selects nothing
                continue
            if (result.passed_gating and result.confidence >= CLASSIFICATION_FLOOR
                    and result.verdict == task_type.selects):
                return Selection(task_type, "classified", asked)
    return Selection(registry.default, "default", asked)


# ---- the built-ins, through the same path ---------------------------------------------------------------------

def _builtin() -> None:
    from pdl_taskmaster.providers.sys1.recipes.problem_class import ProblemClassRecipe

    every_operation = sorted(frozenset().union(*(r.required | r.optional for r in ROUTES.values())))
    register_task_type({
        "profile": PROFILE_ID,
        "category": "VERIFIED_EXECUTION",
        "prompt": {"classification": {"recipe": ProblemClassRecipe(), "selects": "VERIFIED_EXECUTION"},
                   "instructions": ["result_ir", "witness"]},
        "witness_forms": ["computed", "certificate", "argued", "negative"],
        "deliverable": {"body": "text", "result_ir": "required"},
        "route": ["confirmed", "unconfirmed"],
        "operations": every_operation,
        "verifier": "witness-reproduction",
    })
    register_task_type({
        "profile": PROFILE_ID,
        "category": "STANDARD_EXECUTION",
        "prompt": {"classification": None, "instructions": []},
        "witness_forms": [],
        "deliverable": {"body": "text", "result_ir": "not_requested"},
        "route": ["confirmed", "unconfirmed"],
        "operations": every_operation,
        "verifier": "none",
    }, default=True)


_builtin()
