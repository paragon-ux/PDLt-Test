"""Compare models end to end on catalogue prompts (evaluation plane, live).

For each model and prompt, runs the prompt through the full pipeline with
run_catalogue.py (graded as usual), then reports per model call, from the
session's call-trace.jsonl joined with OpenRouter's generation record: time to
first token, latency, output and reasoning tokens, finish reason, whether the
output schema constrained decoding, and the provider and model actually used.

    python scripts/model_compare.py --models openai/gpt-oss-120b,nvidia/nemotron-3-super-120b-a12b:free \
        --prompts 16-01,16-03,01-03 --label nemotron-vs-gptoss

Writes model-compare/<label>/{results.json,REPORT.md}. Needs OPENROUTER_API_KEY
(on Windows also read from the Machine or User environment, as the REPL does).
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "catalogue-runs"


def api_key() -> str:
    key = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
    if key or sys.platform != "win32":
        return key
    for scope in ("Machine", "User"):
        proc = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command",
                               f"[Console]::Out.Write([Environment]::GetEnvironmentVariable('OPENROUTER_API_KEY','{scope}'))"],
                              capture_output=True, text=True)
        if proc.stdout.strip():
            return proc.stdout.strip()
    return ""


def generation(gen_id: str, key: str) -> dict:
    """OpenRouter's record of one generation (available a few seconds after it ends)."""
    for _ in range(8):
        try:
            req = urllib.request.Request(f"https://openrouter.ai/api/v1/generation?id={gen_id}",
                                         headers={"Authorization": f"Bearer {key}"})
            return json.load(urllib.request.urlopen(req, timeout=30)).get("data") or {}
        except Exception:
            time.sleep(3)
    return {}


def run_prompt(model: str, prompt_id: str, extra: list[str]) -> Path | None:
    """One graded catalogue run of one prompt; returns its run directory."""
    before = set(RUNS.glob("run-*")) if RUNS.is_dir() else set()
    subprocess.run([sys.executable, str(ROOT / "run_catalogue.py"), "--model", model, "--prompt-id", prompt_id, *extra],
                   cwd=ROOT, check=False)
    after = set(RUNS.glob("run-*")) - before
    return max(after, key=lambda p: p.stat().st_mtime) if after else None


def calls_of(result_dir: Path, key: str) -> list[dict]:
    traces = sorted(result_dir.rglob("call-trace.jsonl"))
    calls = []
    for line in (traces[0].read_text(encoding="utf-8").splitlines() if traces else []):
        record = json.loads(line)
        reply = record.get("reply") or {}
        last = (record.get("attempts") or [{}])[-1]
        call = {
            "operation": record.get("operation"), "number": record.get("number"), "final": record.get("final"),
            "error": record.get("error"), "http_retries": record.get("retries"),
            "latency_ms": (last.get("phases_ms") or {}).get("response_complete"),
            "output_tokens": reply.get("output_tokens"), "reasoning_tokens": reply.get("reasoning_tokens"),
            "finish": reply.get("finish") or reply.get("status"),
            "schema_constrained": reply.get("schema_constrained"), "whitespace_stall": reply.get("whitespace_stall"),
        }
        gen_id = reply.get("response_id")
        if gen_id and key:
            gen = generation(gen_id, key)
            call.update(ttft_ms=gen.get("latency"), generation_ms=gen.get("generation_time"),
                        provider=gen.get("provider_name"), served_model=gen.get("model"),
                        native_finish=gen.get("native_finish_reason"))
        calls.append(call)
    return calls


def report(rows: list[dict]) -> str:
    lines = ["| Model | Prompt | Verdict | Grade | EXECUTE calls | Stalls | Turn s | EXECUTE: TTFT ms, s, out tok (reasoning), finish | Provider / model |",
             "|---|---|---|---|---|---|---|---|---|"]
    for row in rows:
        executes = [c for c in row["calls"] if c["operation"] == "EXECUTE"]
        detail = "; ".join(
            f"{c.get('ttft_ms')}, {round((c.get('latency_ms') or 0) / 1000, 1)}, {c.get('output_tokens')} "
            f"({c.get('reasoning_tokens')}), {c.get('native_finish') or c.get('finish')}"
            + ("" if c.get("schema_constrained") is not False else ", no schema")
            for c in executes)
        served = sorted({f"{c.get('provider')} / {c.get('served_model')}" for c in row["calls"] if c.get("provider")})
        lines.append(f"| {row['model']} | {row['prompt']} | {row['verdict']} | {row['grade']} | {len(executes)} | "
                     f"{sum(1 for c in executes if c.get('whitespace_stall'))} | {row['elapsed_s']} | {detail} | "
                     f"{', '.join(served)} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--models", required=True, help="comma-separated model slugs")
    parser.add_argument("--prompts", required=True, help="comma-separated catalogue ids")
    parser.add_argument("--label", default=time.strftime("%Y%m%d-%H%M%S"))
    parser.add_argument("--repeat", type=int, default=1, help="runs per model and prompt")
    args, extra = parser.parse_known_args()
    key = api_key()
    out = ROOT / "model-compare" / args.label
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for model in args.models.split(","):
        for prompt_id in args.prompts.split(","):
            for _ in range(args.repeat):
                run_dir = run_prompt(model, prompt_id, extra)
                results = sorted(run_dir.glob("results/*/result.json")) if run_dir else []
                if not results:
                    rows.append({"model": model, "prompt": prompt_id, "verdict": "NO_RUN", "grade": "-",
                                 "elapsed_s": None, "calls": [], "run_dir": str(run_dir)})
                    continue
                result = json.loads(results[0].read_text(encoding="utf-8"))
                rows.append({"model": model, "prompt": prompt_id, "verdict": result.get("verdict"),
                             "grade": (result.get("ground_truth_grade") or {}).get("grade"),
                             "elapsed_s": result.get("elapsed_seconds"), "run_dir": str(run_dir),
                             "calls": calls_of(results[0].parent, key)})
                (out / "results.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    (out / "REPORT.md").write_text(report(rows), encoding="utf-8")
    print(report(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
