"""Probe each provider individually with the harness's own request builder.

For every provider and operation, one request is sent through ApiWorker exactly as
the harness would send it (same schema transform, output cap, reasoning effort),
pinned to that single provider with no fallbacks. The raw request body and the raw
response or error are written to runs/provider-probe/<timestamp>/, and a one-line
verdict per (provider, operation) is printed.

    python scripts/provider_probe.py --providers Cerebras,Groq,SambaNova
    python scripts/provider_probe.py --providers Groq --operations EXECUTE --reasoning high
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
    parser.add_argument("--operations", default=",".join(_INPUTS), help="comma-separated operations")
    parser.add_argument("--model", default="openai/gpt-oss-120b")
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
                result = worker.call(_Request(operation, _INPUTS.get(operation, "Respond.")))
                record.update(verdict="OK", text=result.text[:2000], metadata=result.metadata)
                line = f"OK      {(result.text or '')[:80]!r}"
            except ProviderError as exc:
                failures += 1
                record.update(verdict="ERROR", error=exc.as_record(),
                              response_body=getattr(exc, "response_body", None))
                line = f"ERROR   {exc.category} {exc.status}: {str(exc)[:200]}"
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
