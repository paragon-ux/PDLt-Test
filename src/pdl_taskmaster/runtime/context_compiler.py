from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any
import json

from pdl_taskmaster.runtime.output_contracts import (
    ABLATE_ENTITIES_MODE,
    ABLATE_FRAMING_MODE,
    ABLATE_NORMATIVE_MODE,
    ABLATION_OPERATION,
    DEFAULT_FORM,
    EARLIER_STAGE_OPERATIONS,
    EXECUTION_CONTEXT_SYMBOLS,
    NL_REPRESENTATION_MODE,
    WITHHOLD_EXECUTION_MODE,
    ContractForm,
    prompt_schema,
)
from pdl_taskmaster.runtime.representation import is_format_clause, nl_terms
from pdl_taskmaster.runtime.standard_registry import StandardRegistry


_AUTO_SYMBOLS = {"OPERATION_ID", "APPLICABLE_STANDARD_CLAUSES", "HIGHER_PRIORITY_CONSTRAINTS"}


@dataclass(frozen=True)
class CompiledProjection:
    operation: str
    output_kind: str
    output_fields: tuple[str, ...]
    document: dict[str, Any]
    manifest: dict[str, Any]

    def render(self, bootstrap: str, *, compact: bool = False) -> str:
        """Render bootstrap + projection document.

        compact=True serializes the document without indentation (~23% smaller);
        the parsed JSON is identical, so semantics are unchanged. Fixture replay
        hashes the full rendered prompt, so recorded fixtures must keep the
        default pretty rendering.
        """
        if compact:
            body = json.dumps(self.document, ensure_ascii=False, separators=(",", ":"))
        else:
            body = json.dumps(self.document, ensure_ascii=False, indent=2)
        return bootstrap.rstrip() + "\n\n" + body + "\n"


class ContextCompiler:
    def __init__(self, repo_root: str | Path, standards_root: str | Path | None = None):
        self.repo_root = Path(repo_root)
        from pdl_taskmaster.runtime.normative_store import NormativeStore
        self.standards_root = Path(standards_root) if standards_root else NormativeStore.resolve_standards_root(self.repo_root)
        contract_path = NormativeStore.resolve_contract(self.repo_root, "EXECUTION_CONTRACT.json")
        if not contract_path.is_file():
            contract_path = self.repo_root / "contracts" / "EXECUTION_CONTRACT.json"
        self.execution_contract = json.loads(contract_path.read_text(encoding="utf-8"))
        self.registry = StandardRegistry(self.repo_root, standards_root=self.standards_root)

    def compile(
        self,
        operation: str,
        values: dict[str, Any],
        *,
        higher_priority_constraints: Any = None,
        contract_form: ContractForm | None = None,
        modes: frozenset[str] = frozenset(),
    ) -> CompiledProjection:
        """``contract_form`` is how the worker will constrain this operation's output;
        the output_schema shown is generated in that same form (ADR-0028 rule 1).
        ``modes`` are the host modes active for this call (output_contracts.RESULT_IR_MODE):
        a clause or output field that applies only in a mode is shown only in it."""
        operations = self.execution_contract["operations"]
        if operation not in operations:
            raise ValueError(f"operation:{operation}")
        spec = operations[operation]
        include = tuple(spec["include"])
        # L148 A/B: the stages before EXECUTE without EXECUTE's environment and clauses.
        withheld = set(EXECUTION_CONTEXT_SYMBOLS if WITHHOLD_EXECUTION_MODE in modes
                       and operation in EARLIER_STAGE_OPERATIONS else ())
        drop_exec_clauses = bool(withheld)
        # L149 ablation (a measurement): EXECUTE_UNCONFIRMED without its standard clauses, or its execution framing.
        if operation == ABLATION_OPERATION and ABLATE_NORMATIVE_MODE in modes:
            withheld.add("APPLICABLE_STANDARD_CLAUSES")
        if operation == ABLATION_OPERATION and ABLATE_ENTITIES_MODE in modes:
            withheld.add("TASK_ENTITIES")
        if operation == ABLATION_OPERATION and ABLATE_FRAMING_MODE in modes:
            withheld |= EXECUTION_CONTEXT_SYMBOLS
            drop_exec_clauses = True
        include = tuple(symbol for symbol in include if symbol not in withheld)
        # Optional symbols (Phase 9 S4): supplied by the engine only when the
        # session provides them (e.g. PREVIOUS_DELIVERABLE on chained turns);
        # absent optional symbols are omitted from the projection entirely so
        # single-turn projections stay byte-identical (fixture replay safe).
        optional = tuple(spec.get("optional_include", ()))
        expected = set(include) - _AUTO_SYMBOLS
        provided = set(values) - withheld
        missing = expected - provided
        extra = (provided - expected) - set(optional)
        if missing:
            raise ValueError(f"missing_symbols:{sorted(missing)}")
        if extra:
            raise ValueError(f"extra_symbols:{sorted(extra)}")

        requirement_ids = list(spec["requirements"]) + [
            requirement_id
            for mode, ids in (spec.get("mode_requirements") or {}).items() if mode in modes
            for requirement_id in ids
        ]
        if drop_exec_clauses:
            requirement_ids = [rid for rid in requirement_ids if not rid.startswith("EXEC-")]
        nl = NL_REPRESENTATION_MODE in modes
        if nl:
            # The natural-language arm (representation.py): no notation clauses, artifacts named as prose.
            requirement_ids = [rid for rid in requirement_ids if not is_format_clause(rid)]
        clauses = self.registry.select(requirement_ids)
        clause_values = [
            {"requirement_id": clause.requirement_id, "clause": nl_terms(clause.text) if nl else clause.text}
            for clause in clauses
        ]
        ordered_inputs: dict[str, Any] = {}
        for symbol in include:
            if symbol == "OPERATION_ID":
                ordered_inputs[symbol] = operation
            elif symbol == "APPLICABLE_STANDARD_CLAUSES":
                ordered_inputs[symbol] = clause_values
            elif symbol == "HIGHER_PRIORITY_CONSTRAINTS":
                ordered_inputs[symbol] = higher_priority_constraints
            else:
                ordered_inputs[symbol] = values[symbol]
        for symbol in optional:
            if symbol in provided and values[symbol] is not None:
                ordered_inputs[symbol] = values[symbol]

        # One output contract per operation (IMPL-0001): generated from the payload model.
        output_schema = prompt_schema(operation, contract_form or DEFAULT_FORM, modes)
        if output_schema is None:
            raise ValueError(f"output_contract_missing:{operation}")
        schema_text = json.dumps(output_schema, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

        document: dict[str, Any] = {
            "operation": operation,
            "output_kind": spec["output_kind"],
            "output_schema": output_schema,
            "operation_inputs": ordered_inputs,
        }
        if spec.get("artifact_kind"):
            document["artifact_kind"] = nl_terms(spec["artifact_kind"]) if nl else spec["artifact_kind"]

        clause_digests = {
            value["requirement_id"]: sha256(value["clause"].encode("utf-8")).hexdigest()
            for value in clause_values
        }
        manifest = {
            "operation": operation,
            "included_symbols": list(include),
            "excluded_symbols": list(spec.get("exclude", [])),
            "requirement_ids": requirement_ids,
            "clause_sha256": clause_digests,
            "output_kind": spec["output_kind"],
            "output_fields": list(spec.get("output_fields", [])),
            "output_schema": f"wire_payloads:{operation}",
            "output_schema_sha256": sha256(schema_text.encode("utf-8")).hexdigest(),
        }
        if modes:
            manifest["modes"] = sorted(modes)
        manifest["projection_sha256"] = sha256(
            json.dumps(document, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
        return CompiledProjection(
            operation=operation,
            output_kind=spec["output_kind"],
            output_fields=tuple(spec.get("output_fields", [])),
            document=document,
            manifest=manifest,
        )
