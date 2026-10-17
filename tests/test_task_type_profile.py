"""L120 B2 D1: task-type profile v1 and verifier profile v1. Registration validates every component and invariant
and names each problem; routing selects by classification, else the safe default. Offline."""
from __future__ import annotations

import pytest

from pdl_taskmaster.extensions import task_types, verifiers
from pdl_taskmaster.extensions.profiles import ProfileViolation
from pdl_taskmaster.extensions.task_types import PROFILE_ID, REGISTRY, register_task_type, select

ROUTE_OPS = sorted(task_types.ROUTES["confirmed"].required | task_types.ROUTES["unconfirmed"].required)


def declaration(**changes):
    """A conforming extension: recognised by a criterion, no witness, no verifier."""
    base = {
        "profile": PROFILE_ID,
        "category": "TABULAR_SUMMARY",
        "prompt": {"classification": {"criterion": "The task asks for a summary laid out as a table of rows."},
                   "instructions": []},
        "witness_forms": [],
        "deliverable": {"body": "text", "result_ir": "not_requested"},
        "route": ["confirmed", "unconfirmed"],
        "operations": ROUTE_OPS,
        "verifier": "none",
    }
    base.update(changes)
    return {k: v for k, v in base.items() if v is not ...}


def problems_of(decl, **kwargs):
    with REGISTRY.scoped(), pytest.raises(ProfileViolation) as caught:
        register_task_type(decl, **kwargs)
    return caught.value.problems


class Sys1:
    """System 1 answering each question by name: {question: (choice, confidence)}; a missing name raises."""

    is_configured = True

    def __init__(self, answers):
        self.answers = answers
        self.asked = []

    def call(self, request):
        (name, question), = request.questions.items()
        self.asked.append(name)
        choice, confidence = self.answers[name]
        other = next(c for c in question.choices if c != choice)
        return {"answers": {name: {"choice": choice, "confidence": confidence,
                                   "probabilities": {choice: confidence, other: round(1 - confidence, 4)}}}}, 1.0


# The built-ins.

def test_the_built_ins_are_registered_through_the_profile():
    assert REGISTRY.names()[:2] == ["VERIFIED_EXECUTION", "STANDARD_EXECUTION"]
    assert REGISTRY.default.category == "STANDARD_EXECUTION"
    verified = REGISTRY.get("VERIFIED_EXECUTION")
    assert verified.verifier == "witness-reproduction" and verified.requires_witness and verified.result_ir
    assert verified.instructions == {"result_ir", "witness"} and verified.witness_forms == set(task_types.WITNESS_FORMS)
    standard = REGISTRY.default
    assert not standard.requires_witness and standard.recipe is None and standard.domain() is None


def test_the_profile_names_its_required_set():
    described = task_types.PROFILE.describe()
    assert described["profile"] == "pdlt.task-type/1"
    assert list(described["components"]) == ["category", "prompt", "witness_forms", "deliverable", "route",
                                              "operations", "verifier"]


# Registration refuses what does not conform, naming each problem.

def test_a_conforming_extension_registers_and_is_frozen():
    with REGISTRY.scoped():
        task_type = register_task_type(declaration())
        assert REGISTRY.get("TABULAR_SUMMARY") is task_type and task_type.recipe.name == "task-type:TABULAR_SUMMARY"
        with pytest.raises(AttributeError):
            task_type.verifier = "witness-reproduction"
    assert "TABULAR_SUMMARY" not in REGISTRY


def test_each_missing_component_is_named():
    problems = problems_of({"profile": PROFILE_ID, "category": "TABULAR_SUMMARY"})
    for name in ("prompt", "witness_forms", "deliverable", "route", "operations", "verifier"):
        assert any(p.startswith(f"{name}: missing") for p in problems), name


def test_each_invalid_component_is_named():
    problems = problems_of(declaration(
        category="lower", prompt={"classification": {"criterion": "short"}, "instructions": ["hint"]},
        witness_forms=["guessed"], deliverable={"body": "binary", "result_ir": "maybe"}, route=[],
        operations=["ANSWER_PROTOCOL_DISCUSSION"], verifier="nowhere", extra="x"))
    for prefix in ("category:", "prompt: classification.criterion", "prompt: instructions: 'hint'",
                   "witness_forms: 'guessed'", "deliverable: body", "deliverable: result_ir", "route:",
                   "operations: 'ANSWER_PROTOCOL_DISCUSSION'", "verifier:", "extra: not a component"):
        assert any(p.startswith(prefix) for p in problems), prefix


def test_the_profile_version_is_checked():
    assert problems_of(declaration(profile="pdlt.task-type/2"))[0].startswith("profile: must be 'pdlt.task-type/1'")


@pytest.mark.parametrize("changes, invariant", [
    ({"prompt": {"classification": None, "instructions": ["result_ir"]}}, "result-ir-channel"),
    ({"witness_forms": ["computed"]}, "witness-binding"),
    ({"verifier": "witness-reproduction"}, "witness-binding"),
    ({"prompt": {"classification": None, "instructions": ["witness"]}, "witness_forms": ["computed"],
      "verifier": "witness-reproduction"}, "witness-in-result-ir"),
    ({"prompt": {"classification": None, "instructions": ["result_ir", "witness"]}, "witness_forms": ["argued"],
      "deliverable": {"body": "text", "result_ir": "required"}, "verifier": "witness-reproduction"}, "reproducible"),
    ({"operations": ["BOOTSTRAP_ANALYSIS", "EXECUTE_UNCONFIRMED"]}, "operations-cover-routes"),
    ({"route": ["unconfirmed"]}, "operations-cover-routes"),  # the confirmed route's operations are stray
])
def test_each_broken_invariant_is_named(changes, invariant):
    assert any(p.startswith(f"invariant {invariant}:") for p in problems_of(declaration(**changes)))


class Recipe:
    name = "lenient"
    min_confidence = 0.1

    def build_request(self, state):
        return task_types.CriterionRecipe("TABULAR_SUMMARY", "x" * 30).build_request(state)

    def parse_response(self, body, *, duration_ms=0.0):
        raise NotImplementedError

    def map_to_wire(self, result):
        return {}


def test_a_recipe_may_select_only_its_own_category_and_never_below_the_core_floor():
    problems = problems_of(declaration(prompt={"classification": {"recipe": Recipe(), "selects": "VERIFIED_EXECUTION"},
                                               "instructions": []}))
    assert any("may select only its own category" in p for p in problems)
    assert any("min_confidence must be in [0.85, 1]" in p for p in problems)


def test_a_category_is_registered_once_unless_replaced():
    with REGISTRY.scoped():
        register_task_type(declaration())
        with pytest.raises(ProfileViolation, match="already registered"):
            register_task_type(declaration())
        register_task_type(declaration(), replace=True)


def test_the_default_must_be_safe():
    assert problems_of(declaration(), default=True) == [f"default: {task_types.SAFE_DEFAULT}"]
    with REGISTRY.scoped():
        register_task_type(declaration(category="PLAIN_ANSWER",
                                       prompt={"classification": None, "instructions": []}), default=True)
        assert REGISTRY.default.category == "PLAIN_ANSWER"
    assert REGISTRY.default.category == "STANDARD_EXECUTION"


# Verifier profile v1.

def test_the_verifier_profile_refuses_a_checker_that_would_stand_alone():
    with verifiers.REGISTRY.scoped(), pytest.raises(ProfileViolation) as caught:
        verifiers.register_verifier({"profile": verifiers.PROFILE_ID, "name": "lenient", "domain": "general",
                                     "checker": object(), "reproduction": "optional"})
    problems = caught.value.problems
    assert any(p.startswith("domain: domain 'general' is already answered") for p in problems)
    assert any(p.startswith("checker:") for p in problems) and any(p.startswith("reproduction:") for p in problems)


def test_the_built_in_verifier_is_the_structural_fallback_under_general():
    assert verifiers.REGISTRY.names() == ["witness-reproduction"]
    assert verifiers.output_verifier().get_checker("general").name == "fallback"


# Routing.

def test_without_system_1_every_request_gets_the_default():
    selection = select("Any request.", None, "confirmed")
    assert (selection.task_type.category, selection.how, selection.classifications) == ("STANDARD_EXECUTION",
                                                                                         "default", [])


@pytest.mark.parametrize("verdict, confidence, expected", [
    ("VERIFIED_EXECUTION", 0.97, "VERIFIED_EXECUTION"),
    ("STANDARD_EXECUTION", 0.97, "STANDARD_EXECUTION"),
    ("VERIFIED_EXECUTION", 0.6, "STANDARD_EXECUTION"),  # below the floor: the default
])
def test_the_built_ins_are_selected_as_before(verdict, confidence, expected):
    sys1 = Sys1({"problem_class": (verdict, confidence)})
    selection = select("Any request.", sys1, "unconfirmed")
    assert selection.task_type.category == expected and sys1.asked == ["problem_class"]
    assert selection.classifications[0]["verdict"] == verdict


def test_an_extension_is_asked_after_the_recipes_registered_before_it():
    with REGISTRY.scoped():
        register_task_type(declaration())
        sys1 = Sys1({"problem_class": ("STANDARD_EXECUTION", 0.97), "task_type": ("TABULAR_SUMMARY", 0.95)})
        selection = select("Any request.", sys1, "confirmed")
        assert (selection.task_type.category, selection.how) == ("TABULAR_SUMMARY", "classified")
        assert sys1.asked == ["problem_class", "task_type"]
        sys1 = Sys1({"problem_class": ("STANDARD_EXECUTION", 0.97), "task_type": ("OTHER", 0.95)})
        assert select("Any request.", sys1, "confirmed").task_type.category == "STANDARD_EXECUTION"


def test_a_failed_classification_selects_nothing():
    selection = select("Any request.", Sys1({}), "confirmed")  # the call raises
    assert selection.task_type.category == "STANDARD_EXECUTION" and selection.classifications == [None]


def test_a_category_without_a_recipe_is_reached_only_by_pinning():
    with REGISTRY.scoped():
        register_task_type(declaration(category="PLAIN_ANSWER", prompt={"classification": None, "instructions": []},
                                       route=["unconfirmed"],
                                       operations=sorted(task_types.ROUTES["unconfirmed"].required)))
        sys1 = Sys1({"problem_class": ("STANDARD_EXECUTION", 0.97)})
        assert select("Any request.", sys1, "unconfirmed").task_type.category == "STANDARD_EXECUTION"
        assert select("Any request.", sys1, "unconfirmed", pinned="PLAIN_ANSWER").how == "pinned"
        with pytest.raises(ValueError, match="does not run on the confirmed route"):
            select("Any request.", sys1, "confirmed", pinned="PLAIN_ANSWER")
    with pytest.raises(KeyError, match="no task-type 'PLAIN_ANSWER'"):
        select("Any request.", None, "confirmed", pinned="PLAIN_ANSWER")
