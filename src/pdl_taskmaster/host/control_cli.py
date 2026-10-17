"""Direct unharnessed control runner (single-turn raw completion).

Bypasses all protocol/review/pseudocode machinery and queries the model
directly with the raw prompt text, saving the output in standard workspace
stages so it can be evaluated by the exact same sandboxed grading pipeline.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any

from pdl_taskmaster.host.console import COLOR_NAMES, THEME_NAMES, paint, resolve_colors
from pdl_taskmaster.providers.api_worker import ApiWorker


def main() -> int:
    parser = argparse.ArgumentParser(description="PDLt Direct Control Runner")
    parser.add_argument("--prompt-file", required=True, type=Path)
    parser.add_argument("--session-id", default="control-session")
    parser.add_argument("--transcript", type=Path, default=None)
    parser.add_argument("--workspace-root", required=True, type=Path)
    parser.add_argument("--workdir", type=Path, default=None)
    parser.add_argument("--model", default="openai/gpt-oss-120b")
    parser.add_argument("--api-reasoning-effort", default=None)
    parser.add_argument("--max-output-tokens", type=int, default=16384)
    parser.add_argument("--api-providers", default=None)
    parser.add_argument("--non-interactive", action="store_true")
    parser.add_argument("--exit-on-close", action="store_true")
    parser.add_argument("--dev", action="store_true")
    parser.add_argument("--new-session", action="store_true")
    parser.add_argument("--api-structured-output", action="store_true")
    parser.add_argument(
        "--sandbox",
        choices=["auto", "native", "container", "audit-only"],
        default=None,
        help="confinement mode for execution sandbox parity (default: auto)",
    )
    parser.add_argument(
        "--theme",
        choices=THEME_NAMES,
        default=None,
        help="color theme for console output (default: $PDLT_THEME)",
    )
    parser.add_argument(
        "--user-color",
        choices=COLOR_NAMES,
        default=None,
        help="override user prompt color",
    )
    parser.add_argument(
        "--assistant-color",
        choices=COLOR_NAMES,
        default=None,
        help="override assistant response color",
    )

    args, _ = parser.parse_known_args()

    if args.sandbox:
        os.environ["PDLT_SANDBOX"] = args.sandbox

    prompt_text = args.prompt_file.read_text(encoding="utf-8-sig")

    providers = [p.strip() for p in args.api_providers.split(",")] if args.api_providers else None
    provider_pinning = {"order": providers, "allow_fallbacks": False} if providers else None

    worker = ApiWorker(
        repo_root=Path.cwd(),
        model=args.model,
        max_output_tokens=args.max_output_tokens,
        provider_pinning=provider_pinning,
    )

    body: dict[str, Any] = {
        "model": worker.model,
        "input": prompt_text,
    }
    if worker.max_output_tokens:
        body["max_output_tokens"] = worker.max_output_tokens
    if args.api_reasoning_effort:
        body["reasoning"] = {"effort": args.api_reasoning_effort}
    # The harness sends this same provider order (ApiWorker.build_request_body). Without it OpenRouter picks
    # any provider, and the control is no longer the same model served the same way.
    if worker.provider_pinning:
        body["provider"] = worker.provider_pinning

    trace = worker.begin_call("CONTROL_DIRECT")
    t0 = time.perf_counter()
    data = None
    try:
        request = worker._responses_request(body, worker._resolve_api_key())
        data = worker._send_json_with_retries(request, time.monotonic() + worker.max_call_seconds)
        trace.final = "completed"
        output_text = ApiWorker._extract_output_text(data)
    except Exception as exc:
        trace.final = "failed"
        trace.error = str(exc)
        output_text = f"Error during model completion: {exc}"
    finally:
        worker.end_call(trace)

    latency = time.perf_counter() - t0

    # Console display with color/theme support when run interactively
    if not args.non_interactive:
        try:
            colors = resolve_colors(args.theme, args.user_color, args.assistant_color)
            print(paint(f"USER> {prompt_text}", "user", colors))
            print(paint(f"ASSISTANT> {output_text}", "assistant", colors))
        except Exception:
            print(f"USER> {prompt_text}")
            print(f"ASSISTANT> {output_text}")

    # Ensure stage directories match standard execution deliverable paths
    out_dir = args.workspace_root / "stages" / "50_execution" / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "current.md").write_text(output_text, encoding="utf-8")
    (out_dir / "current.json").write_text(
        json.dumps({"kind": "RESULT", "body": output_text}, indent=2), encoding="utf-8"
    )

    # Record event log for call_accounting
    events_dir = args.workspace_root / "turns" / "turn_001"
    events_dir.mkdir(parents=True, exist_ok=True)
    usage = (data or {}).get("usage") or {}
    event = {
        "kind": "MODEL_OUTPUT_RECORDED",
        "payload": {
            "operation": "CONTROL_EXECUTE",
            "model": args.model,
            "latency_s": round(latency, 3),
            "input_tokens": usage.get("input_tokens", 0),
            "output_tokens": usage.get("output_tokens", 0),
            "reasoning_tokens": (usage.get("output_tokens_details") or {}).get("reasoning_tokens", 0),
            "cached_tokens": (usage.get("input_tokens_details") or {}).get("cached_tokens", 0),
            "response_id": (data or {}).get("id"),
        },
    }
    (events_dir / "events.jsonl").write_text(json.dumps(event) + "\n", encoding="utf-8")

    # Record transcript
    if args.transcript:
        args.transcript.parent.mkdir(parents=True, exist_ok=True)
        transcript_content = (
            f"USER> {prompt_text}\n\n"
            f"ASSISTANT> {output_text}\n"
        )
        args.transcript.write_text(transcript_content, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
