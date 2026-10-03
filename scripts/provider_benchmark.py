"""Measure streaming latency and throughput per OpenRouter provider.

Each provider gets the same streamed chat request, pinned to that provider with no
fallbacks, repeated --runs times. Per run it records time to first token (reasoning
or content), time to first content token, total time, output and reasoning tokens
from the provider's usage, throughput after the first token, the provider OpenRouter
reports as having served the request, and any error. Results go to
runs/provider-bench/<timestamp>/results.json and a median summary is printed.

    python scripts/provider_benchmark.py --providers Groq,Cerebras,DeepInfra
    python scripts/provider_benchmark.py --providers Groq --runs 5 --reasoning high

This measures the provider, not the protocol: scripts/provider_probe.py checks that a
provider accepts the harness's own requests and schemas.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
URL = "https://openrouter.ai/api/v1/chat/completions"
PROMPT = (
    "Write a Python function that returns the n-th Fibonacci number iteratively, with a docstring, "
    "followed by five pytest test functions for it. Reply with the code only."
)


def _run_once(key: str, model: str, provider: str, reasoning: str, max_tokens: int, timeout: float) -> dict:
    body = {
        "model": model,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": True,
        "max_tokens": max_tokens,
        "reasoning": {"effort": reasoning},
        "provider": {"order": [provider], "allow_fallbacks": False},
        "usage": {"include": True},
    }
    request = urllib.request.Request(
        URL, data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    record: dict = {"provider_requested": provider, "ok": False}
    started = time.perf_counter()
    first_any = first_content = None
    usage: dict = {}
    served_by = None
    finish = None
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            record["http_status"] = response.status
            record["headers_s"] = round(time.perf_counter() - started, 3)
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                chunk = json.loads(data)
                if "error" in chunk:
                    record["error"] = chunk["error"]
                    break
                served_by = chunk.get("provider") or served_by
                usage = chunk.get("usage") or usage
                for choice in chunk.get("choices") or []:
                    delta = choice.get("delta") or {}
                    now = time.perf_counter() - started
                    if delta.get("reasoning") and first_any is None:
                        first_any = now
                    if delta.get("content"):
                        first_any = now if first_any is None else first_any
                        first_content = now if first_content is None else first_content
                    finish = choice.get("finish_reason") or finish
    except urllib.error.HTTPError as exc:
        record["http_status"] = exc.code
        record["error"] = exc.read().decode("utf-8", "replace")[:800]
    except Exception as exc:  # timeouts and connection errors are results, not crashes
        record["error"] = f"{type(exc).__name__}: {exc}"
    total = time.perf_counter() - started
    output = usage.get("completion_tokens")
    reasoning_tokens = (usage.get("completion_tokens_details") or {}).get("reasoning_tokens")
    record.update(
        served_by=served_by, finish_reason=finish, total_s=round(total, 3),
        ttft_s=round(first_any, 3) if first_any is not None else None,
        first_content_s=round(first_content, 3) if first_content is not None else None,
        output_tokens=output, reasoning_tokens=reasoning_tokens, prompt_tokens=usage.get("prompt_tokens"),
    )
    if output and first_any is not None and total > first_any:
        record["throughput_tps"] = round(output / (total - first_any), 1)
    record["ok"] = "error" not in record and bool(output) and served_by is not None
    return record


def _median(values: list) -> float | None:
    values = [v for v in values if v is not None]
    return round(statistics.median(values), 2) if values else None


def main() -> int:
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--providers", required=True, help="comma-separated OpenRouter provider names")
    parser.add_argument("--model", default="openai/gpt-oss-120b")
    parser.add_argument("--reasoning", default="low")
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--api-key-env", default="OPENROUTER_API_KEY")
    args = parser.parse_args()
    key = os.environ.get(args.api_key_env, "").strip()
    if not key:
        print(f"{args.api_key_env} is not set", file=sys.stderr)
        return 2

    out_dir = ROOT / "runs" / "provider-bench" / datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    conditions = {"model": args.model, "reasoning": args.reasoning, "runs": args.runs, "max_tokens": args.max_tokens,
                  "prompt": PROMPT, "started": datetime.now().astimezone().isoformat(timespec="seconds")}
    results: list[dict] = []
    print(f"{'provider':14s} {'ok':>5s} {'ttft':>6s} {'1st txt':>7s} {'total':>6s} {'out tok':>7s} "
          f"{'reason':>6s} {'tok/s':>6s}  served by / errors")
    failures = 0
    for provider in [p.strip() for p in args.providers.split(",") if p.strip()]:
        runs = [_run_once(key, args.model, provider, args.reasoning, args.max_tokens, args.timeout)
                for _ in range(args.runs)]
        results.extend({**r, "run": i + 1} for i, r in enumerate(runs))
        good = [r for r in runs if r["ok"]]
        failures += len(runs) - len(good)
        errors = sorted({str(r.get("error"))[:120] for r in runs if not r["ok"]})
        served = sorted({str(r.get("served_by")) for r in good})
        print(f"{provider:14s} {len(good)}/{len(runs):<3d} {_median([r['ttft_s'] for r in good]) or '-':>6} "
              f"{_median([r['first_content_s'] for r in good]) or '-':>7} {_median([r['total_s'] for r in good]) or '-':>6} "
              f"{_median([r['output_tokens'] for r in good]) or '-':>7} {_median([r['reasoning_tokens'] for r in good]) or '-':>6} "
              f"{_median([r.get('throughput_tps') for r in good]) or '-':>6}  {','.join(served)} {' | '.join(errors)}",
              flush=True)
    (out_dir / "results.json").write_text(json.dumps({"conditions": conditions, "results": results}, indent=2),
                                          encoding="utf-8")
    print(f"\nRaw results: {out_dir / 'results.json'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
