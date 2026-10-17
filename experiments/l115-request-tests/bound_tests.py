"""L115 option 1 (the user, 2026-10-15): tests written from the request plus the deliverable's public signatures
(names and parameter names only: no code, defaults, docstrings or annotations), one call per recorded deliverable,
then run deterministically against that deliverable.

Usage: bound_tests.py <repo> <corpus.json> <out_dir> <model> [workers]
Writes <out_dir>/<index>.py per deliverable and <out_dir>/results.json. Prints status only; never the key."""
from __future__ import annotations

import ast
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

repo, corpus_path, out_dir, model = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), sys.argv[4]
workers = int(sys.argv[5]) if len(sys.argv) > 5 else 3
sys.path.insert(0, str(repo / "src"))
sys.path.insert(0, str(repo))
import hidden_tests  # noqa: E402  (evaluation plane: deliverable_body only)
from pdl_taskmaster.providers.api_worker import ApiWorker  # noqa: E402
from pdl_taskmaster.runtime.session_engine import _python_blocks  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import PREFIX, RUNNER  # noqa: E402

PROMPTS = {"04-02": "04_parsers_and_compilers/json_streaming_parser.txt",
           "04-03": "04_parsers_and_compilers/regex_to_nfa_thompson.txt"}
INSTRUCTIONS = """Write a Python test module for the programming request below. Do not write a solution.
The tests check only behaviour the request states: the examples it gives and properties it states explicitly.
Reach that behaviour through the public interface listed under SIGNATURES: those names and parameters are all you know about the implementation.
Where the request allows more than one reading (for example which of several callbacks fire, or a return shape it does not fix), do not test that point.
Each test is a function named test_<what_it_checks> that takes no arguments and uses assert with a message.
The functions and classes under test are already defined in the module's namespace; do not define or import them.
Import only the standard library.
Return only the Python module, with no prose and no code fence."""


def _params(args: ast.arguments) -> str:
    names = [a.arg for a in args.posonlyargs + args.args]
    if args.vararg:
        names.append("*" + args.vararg.arg)
    elif args.kwonlyargs:
        names.append("*")
    names += [a.arg for a in args.kwonlyargs]
    if args.kwarg:
        names.append("**" + args.kwarg.arg)
    return ", ".join(names)


def signatures(blocks: list[str]) -> str:
    """Public top-level functions and classes with their public methods: names and parameter names only. The
    deliverable's own tests (test_* functions, TestCase classes) and main are left out."""
    lines: list[str] = []
    for block in blocks:
        try:
            tree = ast.parse(block)
        except SyntaxError:
            continue
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not node.name.startswith(("_", "test")) and node.name != "main":
                    lines.append(f"def {node.name}({_params(node.args)})")
            elif isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
                bases = [getattr(b, "attr", getattr(b, "id", "")) for b in node.bases]
                if "TestCase" in bases or node.name.startswith("Test"):
                    continue
                lines.append(f"class {node.name}:")
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
                            item.name == "__init__" or not item.name.startswith("_")):
                        lines.append(f"    def {item.name}({_params(item.args)})")
    return "\n".join(lines) or "(no public functions or classes)"


def main() -> None:
    corpus = [r for r in json.loads(corpus_path.read_text(encoding="utf-8"))
              if r["verdict"] == "CLOSED_SUCCESS" and r["grade"] in ("PASS", "FAIL") and r["deliverable"]]
    out_dir.mkdir(parents=True, exist_ok=True)
    requests = {k: (repo / "prompts" / v).read_text(encoding="utf-8-sig") for k, v in PROMPTS.items()}
    worker = ApiWorker(model=model, repo_root=repo)
    key = worker._resolve_api_key()
    items = []
    for index, row in enumerate(corpus):
        blocks = _python_blocks(hidden_tests.deliverable_body(Path(row["deliverable"]).read_text(encoding="utf-8")))
        items.append((index, row, blocks, signatures(blocks)))

    def write(item):
        index, row, _, sigs = item
        path = out_dir / f"{index:03d}.py"
        if path.is_file() and path.stat().st_size:
            return index, "cached"
        body = {"model": model, "instructions": INSTRUCTIONS, "max_output_tokens": 16384,
                "input": f"REQUEST:\n{requests[row['prompt']]}\n\nSIGNATURES:\n{sigs}"}
        for attempt in (1, 2):
            try:
                data = worker._send_json_with_retries(worker._responses_request(body, key), time.monotonic() + 300)
            except Exception as exc:  # recorded and retried once; a second failure leaves the item out
                text, note = "", f"error {type(exc).__name__}"
            else:
                text, note = worker._extract_output_text(data), "ok"
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0]
            if text.strip():
                path.write_text(text, encoding="utf-8")
                return index, f"{note} attempt {attempt}"
        return index, "empty"

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for index, status in pool.map(write, items):
            print(f"write {index:03d} {status} {time.perf_counter() - started:.0f}s", flush=True)

    from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS, ExecutionSandbox

    budget = EXECUTION_BUDGETS["HEAVY_COMPUTE"]
    results = []
    with ExecutionSandbox(timeout_seconds=budget.timeout_seconds, label="l115-bound") as sandbox:
        for index, row, blocks, sigs in items:
            module = out_dir / f"{index:03d}.py"
            if not module.is_file():
                results.append({"index": index, "prompt": row["prompt"], "grade": row["grade"], "report": {"missing": True}})
                continue
            script = RUNNER.replace("__BLOCKS__", repr(blocks)).replace(
                "__TESTS__", repr(module.read_text(encoding="utf-8"))).replace("__PREFIX__", repr(PREFIX))
            run = sandbox.run_code(script, timeout=budget.timeout_seconds, memory_limit=budget.memory_limit_bytes,
                                   step_limit=budget.step_limit)
            line = next((l for l in (run.stdout or "").splitlines() if l.startswith(PREFIX)), None)
            report = json.loads(line[len(PREFIX):]) if line else {
                "incomplete": "step budget" if run.step_budget_exceeded else "timed out" if run.timed_out
                else f"exit {run.exit_code}"}
            results.append({"index": index, "module": f"{index:03d}.py", "prompt": row["prompt"], "run": row["run"],
                            "grade": row["grade"], "signatures": sigs, "report": report})
            print(f"eval {index:03d} {row['prompt']} {row['grade']} "
                  f"fails={sum(1 for v in report.get('tests', {}).values() if v != 'ok')}", flush=True)
    (out_dir / "results.json").write_text(json.dumps(results, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
