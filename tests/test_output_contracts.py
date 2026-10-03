"""ADR-0028 Phase 0: the tests that define the provider-boundary fix.

- Rule 1: the schema an operation shows the model and the grammar the provider
  enforces describe the same structure, in every form a provider can get. Seven
  operations disagreed before phase 1 (IMPL-0001); the EXECUTE `witness` case was
  the whitespace stall.
- The descriptions the model is shown today survive verbatim (snapshot).
- Rule 5: a provider that cannot take an operation's schema still serves it,
  with a weaker constraint, and the host validates the reply.
- Only reviewed text is shown: no Pydantic docstring reaches the model.
- The OpenRouter metadata fixtures carry what Phases 2-3 read.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT / "src", ROOT / "tests"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from contract_shapes import descriptions, differences  # noqa: E402
from pdl_taskmaster.providers.api_worker import ApiWorker, _SEMANTIC_READ_OPERATIONS  # noqa: E402
from pdl_taskmaster.runtime.context_compiler import _AUTO_SYMBOLS, ContextCompiler  # noqa: E402
from pdl_taskmaster.runtime.operation_bridge import OperationBridge  # noqa: E402
from pdl_taskmaster.runtime.output_contracts import UNION_WRAPPER, ContractForm, grammar_schema  # noqa: E402
from pdl_taskmaster.runtime.wire_payloads import OPERATION_PAYLOAD_MODELS  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
COMPILER = ContextCompiler(ROOT)
CONTRACT_OPERATIONS = COMPILER.execution_contract["operations"]

# Operations that send a grammar today: every payload-modelled operation in the
# contract except the free-text semantic reads.
GRAMMAR_OPERATIONS = sorted(
    op for op in OPERATION_PAYLOAD_MODELS if op in CONTRACT_OPERATIONS and op not in _SEMANTIC_READ_OPERATIONS
)

# Every schema form a provider can get: the default; strict (Groq); strict with
# closed objects only (Cerebras).
FORMS = {
    "default": ContractForm(),
    "strict": ContractForm(strict_all_required=True),
    "strict-closed": ContractForm(strict_all_required=True, free_form_objects=False),
}


def shown_schema(operation: str, form: ContractForm | None = None) -> dict:
    """The output_schema the model reads, from the real compiler."""
    spec = CONTRACT_OPERATIONS[operation]
    values = {symbol: "x" for symbol in set(spec["include"]) - _AUTO_SYMBOLS}
    return COMPILER.compile(operation, values, contract_form=form).document["output_schema"]


@pytest.mark.parametrize("form", list(FORMS))
@pytest.mark.parametrize("operation", GRAMMAR_OPERATIONS)
def test_the_grammar_enforces_only_what_the_model_is_shown(operation, form) -> None:
    """ADR-0028 rule 1. A key the grammar required but the prompt never showed
    (EXECUTE's result_ir.witness) left Nemotron unable to close the object: it
    emitted whitespace until the output cap (IMPL-0001)."""
    assert differences(shown_schema(operation, FORMS[form]), grammar_schema(operation, FORMS[form])) == []


def test_a_top_level_union_is_shown_wrapped_when_the_grammar_wraps_it() -> None:
    """The model is shown the {"outcome": ...} wrapper exactly when it is enforced."""
    assert list(shown_schema("DRAFT_PROMPT")["properties"]) == [UNION_WRAPPER]
    assert "properties" not in shown_schema("DRAFT_PROMPT", ContractForm(grammar="json"))
    assert grammar_schema("EXECUTE", ContractForm(grammar="json")) is None


def test_optional_fields_stay_optional_unless_the_provider_needs_all_required() -> None:
    """The default form keeps result_ir.witness optional, so the model can close
    result_ir after open_defects; strict providers get it required and nullable,
    and the model is shown that too."""
    def result_ir(schema: dict) -> dict:
        result = next(v for v in schema["properties"][UNION_WRAPPER]["anyOf"] if "result_ir" in v["properties"])
        spec = result["properties"]["result_ir"]
        return next(b for b in spec.get("anyOf", [spec]) if b.get("type") == "object")

    assert "witness" not in result_ir(shown_schema("EXECUTE"))["required"]
    assert "witness" in result_ir(shown_schema("EXECUTE", FORMS["strict"]))["required"]


def test_every_shown_description_survives_verbatim() -> None:
    """The descriptions steer the model (showing the grammar without them moved
    5/8 EXECUTE replies to REQUEST_INPUT): generated schemas keep each one."""
    snapshot = json.loads((FIXTURES / "prompt_schema_descriptions.json").read_text(encoding="utf-8"))["operations"]
    assert sum(len(texts) for paths in snapshot.values() for texts in paths.values()) == 39
    lost = []
    for operation, paths in snapshot.items():
        unwrapped = descriptions(shown_schema(operation, ContractForm(grammar="json")))
        wrapped = {text for texts in descriptions(shown_schema(operation)).values() for text in texts}
        for path, texts in paths.items():
            lost += [f"{operation} {path}: {text[:60]}" for text in texts if text not in unwrapped.get(path, [])]
            lost += [f"{operation} (wrapped): {text[:60]}" for text in texts if text not in wrapped]
    assert lost == []


def test_only_reviewed_descriptions_are_shown() -> None:
    """Pydantic turns docstrings into descriptions; none may reach the model. Every
    description shown is one of the reviewed texts (the snapshot)."""
    snapshot = json.loads((FIXTURES / "prompt_schema_descriptions.json").read_text(encoding="utf-8"))["operations"]
    reviewed = {text for paths in snapshot.values() for texts in paths.values() for text in texts}
    shown = {text for op in CONTRACT_OPERATIONS for texts in descriptions(shown_schema(op)).values() for text in texts}
    assert shown <= reviewed


class _Reply:
    def __init__(self, payload: dict):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def _completed(text: str) -> dict:
    return {"status": "completed",
            "output": [{"type": "message", "content": [{"type": "output_text", "text": text}]}]}


@pytest.mark.parametrize("operation, reply, parse", [
    ("EXECUTE",
     {"kind": "RESULT", "body": "answer", "result_ir": {"files": [], "reconciliation": [], "open_defects": []}},
     "parse_execution"),
    ("EMIT_RESULT_IR",
     {"result_ir": {"files": [], "reconciliation": [], "open_defects": []}},
     "parse_result_ir_repair"),
])
def test_a_provider_that_rejects_the_schema_still_serves_the_operation(monkeypatch, operation, reply, parse) -> None:
    """Groq rejects the EXECUTE and EMIT_RESULT_IR schemas. It is adapted to,
    not excluded: the operation goes to Groq with a weaker constraint (JSON mode
    or none), and the host validates the reply against the Pydantic contract."""
    from pdl_taskmaster.providers import api_worker as module

    sent: list[dict] = []

    def replay(req, timeout=None):
        sent.append(json.loads(req.data))
        return _Reply(_completed(json.dumps(reply)))

    monkeypatch.setattr(module.urllib.request, "urlopen", replay)
    monkeypatch.setenv("OPENROUTER_API_KEY", "stub")
    worker = ApiWorker(model="m", repo_root=ROOT, provider_pinning={"order": ["Groq"], "allow_fallbacks": False})

    class Request:
        prompt = "SYSTEM\n\nUSER"
        manifest = {}
        projection = None

    Request.operation = operation
    text = worker.call(Request()).text
    assert sent[0]["provider"]["order"] == ["Groq"]
    assert (sent[0].get("text") or {}).get("format", {}).get("type") in (None, "json_object")
    getattr(OperationBridge(ROOT), parse)(text)  # host validation accepts it


def test_openrouter_metadata_fixtures_carry_what_the_adapter_reads() -> None:
    """Offline copies of OpenRouter's model and endpoint records (Phases 2-3)."""
    models = {m["id"]: m for m in json.loads((FIXTURES / "openrouter" / "models.json").read_text(encoding="utf-8"))["data"]}
    nemotron = models["nvidia/nemotron-3-super-120b-a12b:free"]
    gpt_oss = models["openai/gpt-oss-120b"]
    assert nemotron["reasoning"]["supported_efforts"] == ["medium", "low"]
    assert nemotron["reasoning"]["supports_max_tokens"] is True
    assert {"structured_outputs", "temperature", "top_p", "reasoning"} <= set(nemotron["supported_parameters"])
    assert "high" in gpt_oss["reasoning"]["supported_efforts"]

    def endpoints(name: str) -> list[dict]:
        return json.loads((FIXTURES / "openrouter" / name).read_text(encoding="utf-8"))["data"]["endpoints"]

    assert [e["provider_name"] for e in endpoints("endpoints-nvidia--nemotron-3-super-120b-a12b--free.json")] == ["Nvidia"]
    gpt_oss_hosts = {e["provider_name"].lower() for e in endpoints("endpoints-openai--gpt-oss-120b.json")}
    assert {"baseten", "crusoe"} <= gpt_oss_hosts  # spelled "BaseTen" in the metadata
