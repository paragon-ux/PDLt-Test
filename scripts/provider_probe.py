"""Probe each provider individually with the harness's own request builder.

For every provider and operation, one request is sent through ApiWorker exactly as
the harness would send it (same schema transform, output cap, reasoning effort),
pinned to that single provider with no fallbacks. The raw request body and the raw
response or error are written to runs/provider-probe/<timestamp>/, and a one-line
verdict per (provider, operation) is printed.

    python scripts/provider_probe.py --providers Cerebras,Groq,SambaNova
    python scripts/provider_probe.py --providers Groq --operations EXECUTE --reasoning high
    python scripts/provider_probe.py --providers Groq --operations EXECUTE_WITNESS

EXECUTE_WITNESS is an EXECUTE call whose correct reply carries a positive witness
with task-chosen data keys in result_ir; it passes only when the provider accepts
the generation and the host parses the witness from it.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdl_taskmaster.providers.api_worker import ApiWorker, ProviderError  # noqa: E402

_INPUTS = {
    "BOOTSTRAP_ANALYSIS": "Summarize the task: add 2 and 3.",
    "DRAFT_PROMPT": "Draft Prompt Pseudocode for: add 2 and 3.",
    "DRAFT_PLAN": "CONFIRMED_PROMPT_BODY: COMPUTE the sum of 2 and 3",
    "EXECUTE": "CONFIRMED_PROMPT_BODY: COMPUTE the sum of 2 and 3\nCONFIRMED_PLAN_BODY: ADD 2 and 3\nRETURN the sum",
}

# Probe cases that reuse an operation's schema with another input: label -> operation.
_OPERATION_OF = {"EXECUTE_WITNESS": "EXECUTE"}


def _witness_input() -> str:
    """A verified-execution EXECUTE input whose correct reply carries a positive
    witness in result_ir, with data keys the task chooses (not declared by any schema)."""
    from pdl_taskmaster.runtime.result_ir import render_instructions

    return (
        "CONFIRMED_PROMPT_BODY: COMPUTE the prime factorization of 360\nRETURN the factors and their exponents\n"
        "CONFIRMED_PLAN_BODY: FACTOR 360 into primes\nEMIT the factors and their exponents\n"
        "RESULT_IR_INSTRUCTIONS: " + render_instructions(repo_root=ROOT, requires_verified_execution=True) + "\n"
        "Also write the same witness object into result_ir.witness, with \"data\" holding the keys "
        "\"prime_factors\" and \"exponents\"."
    )


_INPUTS["EXECUTE_WITNESS"] = _witness_input()


def _host_witness_problem(text: str) -> str | None:
    """Why the host would not accept the reply as a RESULT carrying a positive
    witness with data, or None when it does."""
    from pdl_taskmaster.runtime.operation_bridge import OperationBridge, WireError

    try:
        outcome = OperationBridge(ROOT).parse_execution(text)
    except WireError as exc:
        return f"host rejected the reply: {exc.reason}: {exc.operator_feedback or exc}"
    witness = (getattr(outcome, "result_ir", None) or {}).get("witness") or {}
    if outcome.kind != "RESULT" or witness.get("polarity") != "positive" or not witness.get("data"):
        return f"reply carries no positive witness with data (kind={outcome.kind}, witness={witness or None})"
    return None


class _Recording(ApiWorker):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent: dict | None = None
        self.received: dict | None = None

    def _send_json_with_retries(self, req, deadline=None):
        self.sent = json.loads(req.data)
        self.received = super()._send_json_with_retries(req, deadline)
        return self.received


class _Request:
    def __init__(self, operation: str, text: str):
        self.operation = operation
        self.prompt = f"You are a stateless operation worker.\n\n{text}"
        self.manifest = {}
        self.projection = None


def main() -> int:
    if sys.platform == "win32":
        # Provider messages can hold any character; the ANSI code page cannot.
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--providers", required=True, help="comma-separated, e.g. Cerebras,Groq,SambaNova")
    parser.add_argument("--operations", default=",".join(_INPUTS),
                        help=f"comma-separated operations or probe cases (default: {','.join(_INPUTS)})")
    parser.add_argument("--model", default="nvidia/nemotron-3-super-120b-a12b:free")
    parser.add_argument("--reasoning", default="low")
    parser.add_argument("--max-output-tokens", type=int, default=4096)
    args = parser.parse_args()

    out_dir = ROOT / "runs" / "provider-probe" / datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    failures = 0
    for provider in [p.strip() for p in args.providers.split(",") if p.strip()]:
        for operation in [o.strip() for o in args.operations.split(",") if o.strip()]:
            worker = _Recording(
                model=args.model, repo_root=ROOT, reasoning_effort=args.reasoning,
                max_output_tokens=args.max_output_tokens, max_call_seconds=120,
                provider_pinning={"order": [provider], "allow_fallbacks": False},
            )
            record: dict = {"provider": provider, "operation": operation}
            started = time.perf_counter()
            try:
                result = worker.call(_Request(_OPERATION_OF.get(operation, operation),
                                              _INPUTS.get(operation, "Respond.")))
                problem = _host_witness_problem(result.text) if operation == "EXECUTE_WITNESS" else None
                if problem is None:
                    record.update(verdict="OK", text=result.text[:2000], metadata=result.metadata)
                    line = f"OK      {(result.text or '')[:80]!r}"
                else:
                    failures += 1
                    record.update(verdict="ERROR", text=result.text[:4000], metadata=result.metadata,
                                  error={"category": "HOST_REJECTED_REPLY", "message": problem})
                    line = f"ERROR   {problem[:200]}"
            except ProviderError as exc:
                failures += 1
                record.update(verdict="ERROR", error=exc.as_record(),
                              response_body=getattr(exc, "response_body", None))
                line = f"ERROR   {exc.category} {exc.status}: {' '.join(str(exc).split())[:200]}"
                if exc.failed_generation:
                    line += f" [failed_generation: {len(exc.failed_generation)} chars in the record]"
            except Exception as exc:  # anything else is reported, never hidden
                failures += 1
                record.update(verdict="ERROR", error={"category": "HARNESS_EXCEPTION", "message": f"{type(exc).__name__}: {exc}"})
                line = f"ERROR   {type(exc).__name__}: {str(exc)[:200]}"
            record["seconds"] = round(time.perf_counter() - started, 2)
            record["request_body"] = worker.sent
            record.setdefault("response_body", worker.received)
            (out_dir / f"{provider}-{operation}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False),
                                                                 encoding="utf-8")
            print(f"{provider:12s} {operation:20s} {record['seconds']:6.1f}s  {line}", flush=True)
    print(f"\nRaw requests and responses: {out_dir}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
