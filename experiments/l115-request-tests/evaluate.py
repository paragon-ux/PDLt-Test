"""L115 feasibility, step 2 (deterministic): run each request-test module against every recorded 04-02/04-03
deliverable that closed CLOSED_SUCCESS (graded PASS or FAIL by the hidden tests), in the sandbox.
Usage: l115_evaluate.py <repo> <corpus.json> <tests_dir> <out.json>."""
import json
import sys
from pathlib import Path

repo, corpus_path, tests_dir, out_path = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4])
sys.path.insert(0, str(repo / "src"))
sys.path.insert(0, str(repo))
import hidden_tests  # noqa: E402  (evaluation plane: deliverable_body only)
from pdl_taskmaster.runtime.session_engine import _python_blocks  # noqa: E402
from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS, ExecutionSandbox  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import PREFIX, RUNNER  # noqa: E402

corpus = [r for r in json.loads(corpus_path.read_text(encoding="utf-8"))
          if r["verdict"] == "CLOSED_SUCCESS" and r["grade"] in ("PASS", "FAIL") and r["deliverable"]]
budget = EXECUTION_BUDGETS["HEAVY_COMPUTE"]
results = []
with ExecutionSandbox(timeout_seconds=budget.timeout_seconds, label="l115-eval") as sandbox:
    for module in sorted(tests_dir.glob("04-0*-s*.py")):
        prompt_id = module.name[:5]
        source = module.read_text(encoding="utf-8")
        for row in (r for r in corpus if r["prompt"] == prompt_id):
            text = Path(row["deliverable"]).read_text(encoding="utf-8")
            blocks = _python_blocks(hidden_tests.deliverable_body(text))
            script = RUNNER.replace("__BLOCKS__", repr(blocks)).replace("__TESTS__", repr(source)) \
                .replace("__PREFIX__", repr(PREFIX))
            run = sandbox.run_code(script, timeout=budget.timeout_seconds, memory_limit=budget.memory_limit_bytes,
                                   step_limit=budget.step_limit)
            line = next((l for l in (run.stdout or "").splitlines() if l.startswith(PREFIX)), None)
            report = json.loads(line[len(PREFIX):]) if line else {
                "incomplete": "step budget" if run.step_budget_exceeded else "timed out" if run.timed_out
                else f"exit {run.exit_code}"}
            results.append({"module": module.name, "prompt": prompt_id, "run": row["run"], "grade": row["grade"],
                            "report": report})
            print(module.name, row["run"][-30:], row["grade"],
                  "fails=" + str(sum(1 for v in report.get("tests", {}).values() if v != "ok")), flush=True)
out_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
