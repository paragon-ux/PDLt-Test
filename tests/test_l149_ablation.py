"""L149: the ablation of what EXECUTE_UNCONFIRMED receives (the user, 2026-10-22), a measurement that ships nothing.
Each part changes only its own piece of that one call: normative (no standard clauses, no guidance block), framing
(no execution environment, EXEC-* clauses, or code, tool and witness wording), notation (the working notes in plain
prose), order (the deliverable before the working notes). Without the flag every request is unchanged (the parity
goldens hold). Offline; the worker and System 1 are scripted."""
from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import run_catalogue
from pdl_taskmaster.host import repl
from pdl_taskmaster.providers.api_worker import ApiWorker
from pdl_taskmaster.runtime.run_settings import RunSettings
from pdl_taskmaster.runtime.session_engine import SessionEngine

ROOT = Path(__file__).resolve().parents[1]
REQUEST = "Two numbers x and y satisfy x + y = 10 and x - y = 2. Find x and explain why."
MODEL = "openai/gpt-oss-120b"


class Sys1:
    is_configured = True
    model = "fake-sys1"

    def call(self, request):
        name = next(iter(request.questions))
        choice = "APPLY_PROTOCOL" if name == "route" else "STANDARD_EXECUTION"
        other = "BYPASS" if name == "route" else "VERIFIED_EXECUTION"
        return {"answers": {name: {"choice": choice, "confidence": 0.97,
                                   "probabilities": {choice: 0.97, other: 0.03}}}}, 1.0


def _requests(root: Path, parts: tuple[str, ...] = ()) -> dict:
    requests: list = []

    def model_call(req):
        requests.append(req)
        if req.operation == "BOOTSTRAP_ANALYSIS":
            return json.dumps({"kind": "ANALYSIS", "task_summary": "Find x.", "approach_notes": "",
                               "risk_notes": "", "task_entities": []})
        return json.dumps({"kind": "RESULT", "interpretation": "DETERMINE x", "approach": "SOLVE for x",
                           "body": "x = 6"})

    engine = SessionEngine(ROOT, model_call, workspace_root=root, sys1_client=Sys1(), no_review=True)
    engine.ablate_unconfirmed = parts
    engine.handle_user_message(REQUEST)
    return {r.operation: r for r in requests}


def _body(request) -> dict:
    return ApiWorker(model=MODEL, repo_root=ROOT).build_request_body(request)[0]


def _schema(request) -> dict:
    return request.projection.document["output_schema"]


def _branches(schema: dict) -> list[dict]:
    return [b for b in _walk(schema) if "interpretation" in b.get("properties", {})]


def _walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from _walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk(value)


@pytest.fixture(scope="module")
def baseline(tmp_path_factory):
    return _requests(tmp_path_factory.mktemp("base"))


@pytest.mark.parametrize("part", ["normative", "framing", "notation", "order", "entities"])
def test_only_execute_unconfirmed_changes(tmp_path: Path, baseline, part):
    ablated = _requests(tmp_path, (part,))
    assert ablated["BOOTSTRAP_ANALYSIS"].prompt == baseline["BOOTSTRAP_ANALYSIS"].prompt
    assert _body(ablated["BOOTSTRAP_ANALYSIS"]) == _body(baseline["BOOTSTRAP_ANALYSIS"])
    assert _body(ablated["EXECUTE_UNCONFIRMED"]) != _body(baseline["EXECUTE_UNCONFIRMED"])


def test_normative_removes_the_clauses_and_the_guidance(tmp_path: Path, baseline):
    base, cut = baseline["EXECUTE_UNCONFIRMED"], _requests(tmp_path, ("normative",))["EXECUTE_UNCONFIRMED"]
    assert "UNC-03 — Working notes" in base.prompt and "APPLICABLE_STANDARD_CLAUSES" in base.prompt
    assert "UNC-03 — Working notes" not in cut.prompt and "APPLICABLE_STANDARD_CLAUSES" not in cut.prompt
    assert "AVAILABLE_EXECUTION_TOOLS" in cut.prompt and _schema(cut) == _schema(base)
    assert "NORMATIVE GUIDELINES" in _body(base)["instructions"]
    assert "NORMATIVE GUIDELINES" not in _body(cut).get("instructions", "")


def test_framing_removes_the_environment_and_the_code_wording(tmp_path: Path, baseline):
    base, cut = baseline["EXECUTE_UNCONFIRMED"], _requests(tmp_path, ("framing",))["EXECUTE_UNCONFIRMED"]
    assert "AVAILABLE_EXECUTION_TOOLS" not in cut.prompt
    assert '"requirement_id": "EXEC-01"' in base.prompt  # UNC-04's own text still names EXEC-01
    assert '"requirement_id": "EXEC-01"' not in cut.prompt and '"requirement_id": "EXEC-05"' not in cut.prompt
    assert "UNC-03 — Working notes" in cut.prompt
    branches = _branches(_schema(cut))
    assert branches and all("description" not in b for b in branches)
    assert all(b["properties"]["body"].get("description", "The complete deliverable content.")
               == "The complete deliverable content." for b in branches)
    guidance = _body(cut)["instructions"]
    assert "WITNESS" not in guidance and "REQUEST_INPUT" not in guidance and "AVAILABLE_EXECUTION_TOOLS" not in guidance
    assert "Deliver the substantive result in `body`." in guidance and "(UNC-03)" in guidance


def test_notation_asks_for_prose_notes(tmp_path: Path, baseline):
    base, cut = baseline["EXECUTE_UNCONFIRMED"], _requests(tmp_path, ("notation",))["EXECUTE_UNCONFIRMED"]
    for branch in _branches(_schema(cut)):
        for name in ("interpretation", "approach"):
            assert "in plain prose" in branch["properties"][name]["description"]
            assert "PDL" not in branch["properties"][name]["description"]
    assert "in plain prose" in _body(cut)["instructions"] and "using PDL notation" not in _body(cut)["instructions"]
    assert "using PDL notation" in _body(base)["instructions"]
    assert cut.prompt.replace("in plain prose", "in PDL pseudocode notation") == base.prompt


def test_order_puts_the_deliverable_first(tmp_path: Path, baseline):
    cut = _requests(tmp_path, ("order",))["EXECUTE_UNCONFIRMED"]
    for branch in _branches(_schema(cut)):
        assert list(branch["properties"])[:2] == ["kind", "body"]
        assert branch["required"].index("body") < branch["required"].index("interpretation")
    guidance = _body(cut)["instructions"]
    assert guidance.index("`kind`, `body`, `interpretation`, `approach`") < guidance.index("Deliver the substantive")
    assert guidance.index("Deliver the substantive") < guidance.index("Write your working understanding")


def test_entities_withholds_the_bootstrap_extraction(tmp_path: Path, baseline):
    base, cut = baseline["EXECUTE_UNCONFIRMED"], _requests(tmp_path, ("entities",))["EXECUTE_UNCONFIRMED"]
    assert "TASK_ENTITIES" in base.prompt and "TASK_ENTITIES" not in cut.prompt
    assert "SOURCE_REQUEST" in cut.prompt and _body(cut)["instructions"] == _body(base)["instructions"]


def test_every_part_together_leaves_the_request(tmp_path: Path):
    cut = _requests(tmp_path, ("normative", "framing", "notation", "order", "entities"))["EXECUTE_UNCONFIRMED"]
    for symbol in ("TASK_ENTITIES", "AVAILABLE_EXECUTION_TOOLS", "APPLICABLE_STANDARD_CLAUSES"):
        assert symbol not in cut.prompt
    assert "SOURCE_REQUEST" in cut.prompt and "NORMATIVE GUIDELINES" not in _body(cut).get("instructions", "")


def test_parts_combine_and_unknown_parts_are_refused(tmp_path: Path):
    both = _requests(tmp_path, ("framing", "notation"))["EXECUTE_UNCONFIRMED"]
    assert "AVAILABLE_EXECUTION_TOOLS" not in both.prompt and "in plain prose" in _body(both)["instructions"]
    engine = SimpleNamespace()
    with pytest.raises(ValueError):
        RunSettings(ablate_unconfirmed=("notes",))
    with pytest.raises(ValueError):
        RunSettings(ablate_unconfirmed="order")
    RunSettings(ablate_unconfirmed=("order",)).apply(engine)
    assert engine.ablate_unconfirmed == ("order",)
    assert RunSettings().ablate_unconfirmed == ()


def test_the_flag_reaches_the_harness_on_protocol_routes_only(tmp_path: Path):
    def cmd(**settings):
        return run_catalogue.build_harness_command(tmp_path / "p.txt", "s", tmp_path / "t.txt", tmp_path / "d", "m",
                                                   "low", run_settings=settings)
    args = repl._build_parser().parse_args(cmd(route="unconfirmed", ablate_unconfirmed=["framing", "order"])[3:])
    assert repl._ablation_parts(args.ablate_unconfirmed) == ("framing", "order")
    assert "--ablate-unconfirmed" not in cmd(route="control", ablate_unconfirmed=["order"])
    assert repl._ablation_parts(repl._build_parser().parse_args([]).ablate_unconfirmed) == ()
