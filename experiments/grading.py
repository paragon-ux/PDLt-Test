"""Grading for the acceptance gate: every arm graded the same way.

What differs from ``graders.grade`` (the catalogue path), and why
(gate design, §12):
- **One code budget for every arm.** ``graders.build_corpus`` re-runs code under
  the budget the run recorded. A control run has no events, so it gets no step
  limit, while a protocol run gets its routed tier. Here every arm's code runs
  under HEAVY_COMPUTE, the most generous budget the protocol can grant, so the
  grader's budget fails no arm.
- **Text in, grade out.** Controls never write a workspace, so grading takes the
  published text and its outcome kind directly.
- **P-first.** ``first_attempt`` reads the first EXECUTE attempt's saved reply,
  not the newest published deliverable.
- **The headless outcome is derived, not run.** Fast mode auto-confirms exactly
  the reviews whose artifact has no host findings, so ``headless_stop`` reads
  those findings from a force-confirmed run's events.
- **BYPASS replies** are graded on the transcript, where the user saw them,
  instead of failing as "no published deliverable".
- **MANUAL is never a pass:** adjudication sheets are exported blind
  (``export_adjudication``).

The catalogue graders in ``graders.py`` are used unchanged.
"""
from __future__ import annotations

import csv
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

import graders
from experiments import graders_gen

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "prompts"
GENERATED = Path(__file__).resolve().parent / "prompts"
COMMON_TIER = "HEAVY_COMPUTE"

# Generated families whose catalogue grader reads the instance from the prompt.
_PROMPT_GRADERS: dict[str, Callable[[str, str], tuple[str, str]]] = {
    "SS": graders.grade_subset_sum,
    "LS": graders.grade_latin_square,
    "HP": graders.grade_hamiltonian_path,
}
_SOLUTION_GRADERS: dict[str, Callable[[str, dict[str, Any]], tuple[str, str]]] = {
    "KK": graders_gen.grade_knights,
    "HG": graders_gen.grade_house_owner,
}


@dataclass(frozen=True)
class Item:
    """One prompt the gate can grade: a catalogue entry or a generated item."""

    id: str
    source: str  # "catalogue", "gate" or "dev"
    prompt_text: str
    grade_corpus: Callable[[str], tuple[str, str]] | None  # corpus -> (grade, reason); None: no grader
    hidden_tests: bool = False  # graded by the prompt's hidden tests on the published text (no corpus)

    def grade(self, corpus: str) -> tuple[str, str]:
        if self.grade_corpus is None:
            return graders.NA, "no ground truth required"
        return self.grade_corpus(corpus)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def catalogue_items() -> dict[str, Item]:
    items: dict[str, Item] = {}
    for line in _read(CATALOGUE / "CATALOGUE_MANIFEST.jsonl").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        text = _read(CATALOGUE / entry["file"])
        verified = entry.get("ground_truth_status") == "verified"
        if verified and entry.get("hidden_tests"):
            items[entry["id"]] = Item(entry["id"], "catalogue", text, None, hidden_tests=True)
            continue
        fn = graders.GRADERS.get(entry["id"]) if verified else None
        grade = (lambda corpus, fn=fn, text=text: fn(corpus, text)) if fn else None
        items[entry["id"]] = Item(entry["id"], "catalogue", text, grade)
    return items


def generated_items(name: str) -> dict[str, Item]:
    items: dict[str, Item] = {}
    root = GENERATED / name
    for line in _read(root / "MANIFEST.jsonl").splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        text = _read(GENERATED / entry["file"])
        family = entry["family"]
        if family in _PROMPT_GRADERS:
            fn = _PROMPT_GRADERS[family]
            grade = lambda corpus, fn=fn, text=text: fn(corpus, text)  # noqa: E731
        else:
            solution = json.loads(_read(GENERATED / entry["solution_file"]))
            fn2 = _SOLUTION_GRADERS[family]
            grade = lambda corpus, fn2=fn2, solution=solution: fn2(corpus, solution)  # noqa: E731
        items[entry["id"]] = Item(entry["id"], name, text, grade)
    return items


def ambiguity_items() -> dict[str, Item]:
    """The ambiguity group A (design §6.6): judged after the run, never machine-graded."""
    from experiments import interaction

    return {i.id: Item(i.id, "ambiguity", i.request, None) for i in interaction.ambiguity_items().values()}


def all_items() -> dict[str, Item]:
    return {**catalogue_items(), **generated_items("gate"), **generated_items("dev")}


# --------------------------------------------------------------------------- grading text

def corpus(kind: str, text: str | None, *, run_code: bool = True, tier: str = COMMON_TIER) -> str | None:
    """The corpus a grader reads, as graders.build_corpus builds it, but with one
    code budget for every arm: the deliverable's last Python block re-run under
    ``tier`` (HEAVY_COMPUTE by default), its exit status and stdout appended."""
    if text is None:
        return None
    if run_code and kind == "RESULT":
        # The code is found in the deliverable body, without the appended Result IR
        # and host notes. A deliverable that is whole Python source is run as a
        # script, as the host runs it; with the IR block appended it would no
        # longer read as source, and only fenced code (a plain call's) would run.
        blocks = graders._python_blocks(strip_for_adjudication(text))
        if blocks:
            from pdl_taskmaster.verification.sandbox import EXECUTION_BUDGETS, ExecutionSandbox

            budget = EXECUTION_BUDGETS[tier]
            with ExecutionSandbox(timeout_seconds=budget.timeout_seconds, label="gate-grader") as sandbox:
                out = sandbox.run_code(blocks[-1], timeout=budget.timeout_seconds,
                                       memory_limit=budget.memory_limit_bytes, step_limit=budget.step_limit)
            text += f"\n\n[GRADER: deliverable code exit {out.exit_code}]"
            if out.stdout:
                text += "\n[GRADER: deliverable code stdout]\n" + out.stdout
    return f"[OUTCOME: {kind}]\n{text.translate(graders._TYPOGRAPHY)}"


def grade_text(item: Item, kind: str, text: str | None, *, run_code: bool = True,
               tier: str = COMMON_TIER) -> dict[str, str]:
    """Grade one published text. Never raises: a grader bug is an ERROR, never a pass.

    A prompt with hidden tests is graded by them, on the published text, at their
    own fixed budget (hidden_tests.TIER) for every arm."""
    try:
        if item.hidden_tests:
            return graders.grade_hidden(item.id, kind, text, run_code=run_code)
        built = corpus(kind, text, run_code=run_code, tier=tier)
        if built is None:
            return {"grade": graders.FAIL, "reason": "no published deliverable"}
        grade, reason = item.grade(built)
        return {"grade": grade, "reason": reason}
    except Exception as exc:  # a grader bug must never mask a run
        return {"grade": "ERROR", "reason": f"{type(exc).__name__}: {exc}"}


# --------------------------------------------------------------------------- reading protocol runs

def _events(result_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for path in sorted(Path(result_dir).rglob("events.jsonl")):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                events.append(json.loads(line))
            except ValueError:
                continue
    return events


def published(result_dir: Path) -> tuple[str, str | None, bool]:
    """(outcome kind, published text, bypassed). A BYPASS-routed run published no
    execution outcome: its reply is the transcript's, graded as a RESULT."""
    kind, text = graders.published_outcome(Path(result_dir))
    if kind != "NONE":
        return kind, text, False
    if any(e.get("kind") == "DIRECT_ANSWER_ROUTED" for e in _events(result_dir)):
        transcript = Path(result_dir) / "transcript.txt"
        lines = transcript.read_text(encoding="utf-8", errors="replace").splitlines() if transcript.is_file() else []
        said = [line[len("ASSISTANT> "):] for line in lines if line.startswith("ASSISTANT> ")]
        if said:
            return "RESULT", "\n".join(said), True
    return kind, text, False


_EXECUTE_DIR = re.compile(r"^(\d+)-execute(?:_unconfirmed)?$")


def first_attempt(result_dir: Path, repo_root: Path = ROOT) -> dict[str, Any]:
    """The first EXECUTE attempt as the model returned it (P-first).

    status is one of:
    - ``reply``: parsed; kind and text are set;
    - ``output_limit``: cut off at the cap;
    - ``malformed``: no reply the contract accepts;
    - ``not_reached``: the run never executed (a refusal, a stop, a failure before EXECUTE).
    """
    dirs = sorted(
        (p for p in Path(result_dir).rglob("*") if p.is_dir() and _EXECUTE_DIR.match(p.name)
         and p.parent.match("*/stages/50_execution/output")),
        key=lambda p: int(_EXECUTE_DIR.match(p.name).group(1)),
    )
    if not dirs:
        return {"status": "not_reached", "kind": None, "text": None}
    first = dirs[0]
    if (first / "model-response.truncated.txt").is_file():
        return {"status": "output_limit", "kind": None, "text": None}
    reply = first / "model-response.txt"
    if not reply.is_file():
        return {"status": "malformed", "kind": None, "text": None}
    from pdl_taskmaster.runtime.operation_bridge import OperationBridge
    from pdl_taskmaster.runtime.session_engine import _attach_result_ir

    try:
        outcome = OperationBridge(repo_root).parse_execution(reply.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"status": "malformed", "kind": None, "text": None, "reason": f"{type(exc).__name__}: {exc}"}
    text = outcome.body
    ir = getattr(outcome, "result_ir", None)
    if outcome.kind == "RESULT" and isinstance(ir, dict) and ir:
        text = _attach_result_ir(text, ir)  # published the same way P-final's is
    return {"status": "reply", "kind": outcome.kind, "text": text}


HOST_FINDING_EVENTS = frozenset({"PLAN_ADVANCEMENT_UNRESOLVED", "PLAN_LINT_UNRESOLVED", "PROMPT_LINT_UNRESOLVED"})


def headless_stop(result_dir: Path) -> bool:
    """Whether fast mode would have stopped this run at a review: an artifact was
    published with host findings (AUTH-05 keeps those from advance confirmation)."""
    return any(e.get("kind") in HOST_FINDING_EVENTS and (e.get("payload") or {}).get("host_note")
               for e in _events(result_dir))


def system1_verdicts(result_dir: Path) -> dict[str, Any]:
    """Every System 1 decision a run recorded, for the breakdowns (§8.5)."""
    wanted = {"ACTIVATION_ROUTED", "PROBLEM_CLASS_CLASSIFIED", "EXECUTION_PROFILE_ROUTED", "PLAN_PROFILE_ROUTED",
              "PLAN_ADVANCEMENT", "BUDGET_REFUSAL", "PROTOCOL_REFUSED", "DIRECT_ANSWER_ROUTED"}
    found: dict[str, list[Any]] = {}
    for event in _events(result_dir):
        if event.get("kind") in wanted:
            found.setdefault(event["kind"], []).append(event.get("payload"))
    return found


# --------------------------------------------------------------------------- blind adjudication

_IR_KEYS = {"files", "reconciliation", "open_defects", "witness"}
_TRAILING_IR = re.compile(r"\n*```json\s*\n(\{.*\})\s*\n```\s*\Z", re.S)


def strip_for_adjudication(text: str | None) -> str:
    """The deliverable as an adjudicator should see it: no harness wrapper, no
    appended Result IR block, no [host] notes. Arm identity can still leak through
    style; that limit is stated in the design (§12.4)."""
    if not text:
        return ""
    if text.startswith("UNVERIFIED ANSWER:") and "\n\nCandidate deliverable:\n" in text:
        text = text.split("\n\nCandidate deliverable:\n", 1)[1]
    match = _TRAILING_IR.search(text)
    if match:
        try:
            block = json.loads(match.group(1))
        except ValueError:
            block = None
        if isinstance(block, dict) and set(block) <= _IR_KEYS:
            text = text[: match.start()]
    return "\n".join(line for line in text.splitlines() if not line.startswith("[host] ")).strip()


def export_adjudication(rows: list[dict[str, Any]], out_dir: Path, *, seed: int) -> tuple[Path, Path]:
    """Write a blind sheet (random ids, prompt, stripped deliverable) and a separate
    key mapping each id back to its model, arm and repetition.
    rows: [{"model", "item_id", "rep", "arm", "text"}]."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    order = list(rows)
    random.Random(seed).shuffle(order)
    sheet, key = out_dir / "adjudication_sheet.csv", out_dir / "adjudication_key.jsonl"
    with sheet.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["review_id", "item_id", "deliverable", "verdict (PASS/FAIL)", "note"])
        with key.open("w", encoding="utf-8", newline="\n") as key_handle:
            for n, row in enumerate(order, 1):
                review_id = f"R-{n:04d}"
                writer.writerow([review_id, row["item_id"], strip_for_adjudication(row.get("text")), "", ""])
                key_handle.write(json.dumps({"review_id": review_id, "model": row["model"], "arm": row["arm"],
                                             "rep": row["rep"], "item_id": row["item_id"]}) + "\n")
    return sheet, key
