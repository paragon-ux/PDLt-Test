"""Hidden-test grading for the catalogue's coding prompts (evaluation plane).

How a deliverable is graded:
1. Its Python blocks run inside the harness sandbox, loaded into one namespace
   whose ``__name__`` is not ``"__main__"``. The deliverable's own ``if __name__
   == "__main__":`` demos and tests do not run, and its prints are suppressed.
2. The prompt's hidden tests (``prompts/hidden_tests/<id>.py``) then select
   **candidates**: classes or functions found by the operation names the prompt
   states (an interface adapter). Catalogue prompts mostly name operations, not
   classes, so two correct answers can use different class names, constructors
   or return shapes.
3. Every test runs against each candidate, each test with a time limit. The
   grade is PASS if some candidate passes every test, FAIL otherwise.

**Integrity.** The tests are written from the prompt text and a reference
implementation only, never from model outputs. Every test file ships with
answers in ``prompts/hidden_tests/answers/<id>/``:
- ``ref*.py``: correct, must pass;
- ``alt*.py``: correct, with a different interface, must pass;
- ``bug*.py``: wrong, must fail.
``python hidden_tests.py --validate`` checks all of them and writes
``prompts/hidden_tests/VALIDATION.json`` with the hash of every file it read. A
test then checks that the report is current. Once a gate run starts, tests are
measured, never edited (design §12).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
TESTS_DIR = ROOT / "prompts" / "hidden_tests"
VALIDATION = TESTS_DIR / "VALIDATION.json"
TIER = "HEAVY_COMPUTE"
RESULT_PREFIX = "HIDDEN_TESTS: "
PROGRESS_PREFIX = "HIDDEN_TESTS_PROGRESS: "
MAX_CANDIDATES = 6

# Runs inside the sandbox before the test module. Helpers available to tests:
# classes_with, functions_named, find_callable, construct, missing, approx.
_PRELUDE = r'''
import inspect as _inspect, io as _io, json as _json, sys as _sys, threading as _threading, types as _types

# The deliverable's and the tests' output is silenced once, process-wide: stdout
# redirection is global, so a per-thread redirect left behind by a hung test
# would swallow the final report. The report goes to the saved real stdout.
_REAL_STDOUT = _sys.stdout
_sys.stdout = _io.StringIO()
_LOAD_ERRORS = []
NS = {"__name__": "deliverable", "__builtins__": __builtins__}
for _index, _block in enumerate(__BLOCKS__):
    try:
        exec(compile(_block, "<deliverable block %d>" % (_index + 1), "exec"), NS)
    except BaseException as _exc:  # a block that fails to load still leaves the others' definitions
        if isinstance(_exc, KeyboardInterrupt):
            raise
        _LOAD_ERRORS.append("block %d: %s: %s" % (_index + 1, type(_exc).__name__, str(_exc)[:200]))


def _own(obj):
    return getattr(obj, "__module__", None) == "deliverable"


def classes_with(*methods):
    """Classes the deliverable defines that have every named method (exact names first)."""
    found = [v for v in NS.values() if isinstance(v, type) and _own(v)
             and all(callable(getattr(v, m, None)) for m in methods)]
    return sorted(found, key=lambda c: c.__name__)


def functions_named(*names, params=None):
    """Module-level functions whose name is one of ``names`` (case-insensitive), then,
    if ``params`` is given, every other deliverable function taking that many required
    positional parameters."""
    wanted = {n.lower() for n in names}
    funcs = [v for v in NS.values() if isinstance(v, _types.FunctionType) and _own(v)]
    exact = [f for f in funcs if f.__name__.lower() in wanted]
    rest = []
    if params is not None:
        for f in funcs:
            if f in exact:
                continue
            try:
                required = [p for p in _inspect.signature(f).parameters.values()
                            if p.default is p.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)]
            except (TypeError, ValueError):
                continue
            if len(required) == params:
                rest.append(f)
    return exact + sorted(rest, key=lambda f: f.__name__)


def find_callable(name):
    """A module-level function named ``name``, or that method on an instance of the
    first deliverable class that has it (constructed with no arguments)."""
    value = NS.get(name)
    if callable(value):
        return value
    for cls in classes_with(name):
        try:
            return getattr(cls(), name)
        except TypeError:
            continue
    return None


def construct(cls, *args, **kwargs):
    """Build ``cls`` with the given positional values, falling back to the class's
    own defaults when it takes fewer arguments."""
    try:
        return cls(*args, **kwargs)
    except TypeError:
        if args or kwargs:
            return cls()
        raise


def missing(value):
    """The conventional "absent" answers a prompt leaves open: None or -1."""
    return value is None or value == -1


def approx(a, b, tol=1e-9):
    return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))


def _run_test(test, candidate, seconds):
    outcome = {}

    def target():
        try:
            test(candidate)
            outcome["ok"] = True
        except BaseException as exc:  # an assertion or any error fails the test
            outcome["error"] = "%s: %s" % (type(exc).__name__, str(exc)[:300])

    thread = _threading.Thread(target=target, daemon=True)
    thread.start()
    thread.join(seconds)
    if thread.is_alive():
        return "timed out after %ss" % seconds
    return None if outcome.get("ok") else outcome.get("error", "failed")
'''

_POSTLUDE = r'''
_report = {"passed": False, "candidates": [], "load_errors": _LOAD_ERRORS}
try:
    _candidates = list(CANDIDATES())[:__MAX__]
except BaseException as _exc:
    _candidates = []
    _report["select_error"] = "%s: %s" % (type(_exc).__name__, _exc)


def _progress(event):
    _REAL_STDOUT.write(__PROGRESS__ + _json.dumps(event) + "\n")
    _REAL_STDOUT.flush()


# A timed-out test's thread cannot be stopped (native code is denied), and it
# would keep spending the shared step budget and CPU. So the first timeout ends
# this process: the host resumes with the next candidate in a fresh sandbox.
for _index in range(__START__, len(_candidates)):
    _candidate = _candidates[_index]
    _name = getattr(_candidate, "__name__", repr(_candidate))[:80]
    _progress({"start": _index, "name": _name, "total": len(_candidates)})
    _failures, _hung = [], False
    for _test in TESTS:
        _error = _run_test(_test, _candidate, TEST_SECONDS)
        if _error:
            _failures.append("%s: %s" % (_test.__name__, _error))
            if _error.startswith("timed out"):
                _hung = True
                break
    _report["candidates"].append({"name": _name, "failures": _failures[:8]})
    if not _failures:
        _report["passed"] = True
        break
    if _hung:
        if _index + 1 < len(_candidates):
            _report["resume"] = _index + 1
        break
_REAL_STDOUT.write(__PREFIX__ + _json.dumps(_report) + "\n")
_REAL_STDOUT.flush()
'''


def test_path(prompt_id: str) -> Path:
    return TESTS_DIR / f"{prompt_id}.py"


def has_tests(prompt_id: str) -> bool:
    return test_path(prompt_id).is_file()


def deliverable_body(text: str) -> str:
    """The deliverable without the harness's wrapper, its appended Result IR block,
    or [host] notes: the code a human would read."""
    import re

    if text.startswith("UNVERIFIED ANSWER:") and "\n\nCandidate deliverable:\n" in text:
        text = text.split("\n\nCandidate deliverable:\n", 1)[1]
    match = re.search(r"\n*```json\s*\n(\{.*\})\s*\n```\s*\Z", text, re.S)
    if match:
        try:
            block = json.loads(match.group(1))
        except ValueError:
            block = None
        if isinstance(block, dict) and set(block) <= {"files", "reconciliation", "open_defects", "witness"}:
            text = text[: match.start()]
    return "\n".join(line for line in text.splitlines() if not line.startswith("[host] ")).strip()


def build_script(blocks: list[str], test_source: str, start: int = 0) -> str:
    prelude = _PRELUDE.replace("__BLOCKS__", repr(blocks))
    postlude = (_POSTLUDE.replace("__PREFIX__", repr(RESULT_PREFIX)).replace("__PROGRESS__", repr(PROGRESS_PREFIX))
                .replace("__START__", str(int(start))).replace("__MAX__", str(MAX_CANDIDATES)))
    return prelude + "\n# ---- hidden tests ----\n" + test_source + "\n# ---- runner ----\n" + postlude


def run(prompt_id: str, deliverable: str, *, tier: str = TIER) -> dict[str, Any]:
    """Run a prompt's hidden tests against a deliverable's code, in the sandbox."""
    from pdl_taskmaster.runtime.session_engine import _python_blocks
    from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS, ExecutionSandbox

    blocks = _python_blocks(deliverable_body(deliverable))
    if not blocks:
        return {"passed": False, "reason": "the deliverable contains no Python code"}
    source = test_path(prompt_id).read_text(encoding="utf-8")
    budget = EXECUTION_BUDGETS[tier]
    report: dict[str, Any] = {"passed": False, "candidates": [], "sandbox_runs": 0}
    start = 0
    with ExecutionSandbox(timeout_seconds=budget.timeout_seconds, label="hidden-tests") as sandbox:
        # Each candidate that hangs or exhausts the sandbox ends one run; the next
        # run resumes with the following candidate, so at most one run per candidate.
        for _ in range(MAX_CANDIDATES):
            out = sandbox.run_code(build_script(blocks, source, start), timeout=budget.timeout_seconds,
                                   memory_limit=budget.memory_limit_bytes, step_limit=budget.step_limit)
            report["sandbox_runs"] += 1
            final, started = _parse_output(out.stdout or "")
            if final is None:
                detail = "step budget exceeded" if out.step_budget_exceeded else "timed out" if out.timed_out else \
                    f"exit {out.exit_code}: {(out.stderr or '').strip().splitlines()[-1:] if out.stderr else ''}"
                if started is None:
                    report["reason"] = f"the hidden tests did not complete ({detail})"
                    return report
                report["candidates"].append({"name": started["name"], "failures": [f"did not complete ({detail})"]})
                start = started["start"] + 1
                if start >= started["total"]:
                    break
                continue
            report["candidates"].extend(final["candidates"])
            for key in ("load_errors", "select_error"):
                if key in final:
                    report[key] = final[key]
            if final["passed"]:
                report["passed"] = True
                break
            if "resume" not in final:
                break
            start = final["resume"]
    report["reason"] = ("passed every hidden test" if report["passed"] else
                        "; ".join(f"{c['name']}: {', '.join(c['failures'][:3])}" for c in report["candidates"])
                        or report.get("select_error") or "no candidate implements the stated operations")
    return report


def _parse_output(stdout: str) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """The final report, if the run wrote one, and the last candidate it started."""
    final = started = None
    for line in stdout.splitlines():
        if line.startswith(RESULT_PREFIX):
            final = json.loads(line[len(RESULT_PREFIX):])
        elif line.startswith(PROGRESS_PREFIX):
            started = json.loads(line[len(PROGRESS_PREFIX):])
    return final, started


# --------------------------------------------------------------------------- validation

def _answers(prompt_id: str) -> list[Path]:
    return sorted((TESTS_DIR / "answers" / prompt_id).glob("*.py"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def validate(prompt_ids: list[str] | None = None) -> dict[str, Any]:
    """Every answer through its prompt's tests: ref/alt must pass, bug must fail."""
    ids = prompt_ids or sorted(p.stem for p in TESTS_DIR.glob("*.py"))
    report: dict[str, Any] = {"prompts": {}}
    for prompt_id in ids:
        entry: dict[str, Any] = {"tests_sha256": _sha(test_path(prompt_id)), "answers": {}}
        for answer in _answers(prompt_id):
            text = "```python\n" + answer.read_text(encoding="utf-8") + "\n```"
            result = run(prompt_id, text)
            expected = not answer.stem.startswith("bug")
            entry["answers"][answer.name] = {"sha256": _sha(answer), "passed": result["passed"],
                                             "expected": expected, "ok": result["passed"] == expected,
                                             "reason": result.get("reason", "")[:300]}
        entry["ok"] = bool(entry["answers"]) and all(a["ok"] for a in entry["answers"].values()) and \
            any(a["expected"] for a in entry["answers"].values()) and \
            any(not a["expected"] for a in entry["answers"].values())
        report["prompts"][prompt_id] = entry
    report["ok"] = all(e["ok"] for e in report["prompts"].values())
    return report


def stale() -> list[str]:
    """Prompts whose tests or answers changed since VALIDATION.json was written."""
    if not VALIDATION.is_file():
        return ["VALIDATION.json is missing"]
    recorded = json.loads(VALIDATION.read_text(encoding="utf-8"))["prompts"]
    problems = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        entry = recorded.get(path.stem)
        if entry is None or entry["tests_sha256"] != _sha(path):
            problems.append(f"{path.stem}: tests changed since validation")
            continue
        answers = {p.name: _sha(p) for p in _answers(path.stem)}
        if answers != {name: a["sha256"] for name, a in entry["answers"].items()}:
            problems.append(f"{path.stem}: answers changed since validation")
        elif not entry["ok"]:
            problems.append(f"{path.stem}: validation failed")
    return problems


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "src"))
    if sys.argv[1:2] == ["--validate"]:
        result = validate(sys.argv[2:] or None)
        if not sys.argv[2:]:
            VALIDATION.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8", newline="\n")
        for prompt_id, entry in result["prompts"].items():
            bad = [f"{n} ({a['reason'][:120]})" for n, a in entry["answers"].items() if not a["ok"]]
            print(f"{'ok  ' if entry['ok'] else 'FAIL'} {prompt_id} {len(entry['answers'])} answers"
                  + (f": {'; '.join(bad)}" if bad else ""))
        sys.exit(0 if result["ok"] else 1)
    print("usage: python hidden_tests.py --validate [prompt ids]")
    sys.exit(2)
