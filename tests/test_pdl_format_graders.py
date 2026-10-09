"""The PDL pilot's graders (ledger L97), frozen before any pilot output was read.

- Task 1: the reference implementation passes every criterion, and each broken variant fails
  exactly what it breaks (runs in the grader sandbox).
- Judging: packets carry no arm, repeat or path; the mechanical checks read YAML and the timeline.
"""
from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "src"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from experiments.pdl_format import grade_t1, judge_pilot  # noqa: E402

REFERENCE = (ROOT / "experiments" / "pdl_format" / "reference" / "reconcile.py").read_text(encoding="utf-8")
SAVED = "(Decimal(totals[(acct, day)]) * price).quantize(Decimal(\"0.01\"), rounding=ROUND_HALF_UP)"
VARIANTS = {
    "reference": (REFERENCE, set()),
    "binary floating point": (REFERENCE.replace(SAVED, "f'{round(totals[(acct, day)] * float(price), 2):.2f}'"),
                              {"T1-10"}),
    "last record wins": (REFERENCE.replace("if len({k for _, _, k in group}) > 1:", "if False:")
                         .replace("n, rec, _ = group[0]", "n, rec, _ = group[-1]"), {"T1-04", "T1-05", "T1-12"}),
    "local date": (REFERENCE.replace("day = ts.astimezone(timezone.utc).date().isoformat()",
                                     "day = rec['occurred_at'][:10]").replace("if ts.tzinfo is None:", "if False:"),
                   {"T1-03", "T1-12"}),
    "secrets column": (REFERENCE.replace(r"amount_usd\n", r"amount_usd,api_token\n")
                       .replace(r"{amount}\n", r"{amount},\n"), {"T1-11", "T1-12", "T1-15"}),
}


@pytest.mark.parametrize("name", VARIANTS)
def test_the_task_1_suite_passes_the_reference_and_catches_each_defect(name) -> None:
    program, must_fail = VARIANTS[name]
    assert name == "reference" or program != REFERENCE
    report, note = grade_t1.run_program(program)
    assert note is None
    failed = {criterion for criterion, passed in grade_t1.score(report, program).items() if not passed}
    assert must_fail <= failed if must_fail else failed == set()


def test_the_cli_program_is_picked_from_the_deliverable() -> None:
    deliverable = ("Usage:\n\n```python\nprint('example')\n```\n\n```python\n" + REFERENCE + "```\n\n"
                   "```python\nimport subprocess  # sample run\n```\n")
    assert grade_t1.candidate_program(deliverable) == REFERENCE.strip("\n") + "\n"
    assert grade_t1.candidate_program("no code here") is None
    assert grade_t1.score({}, None)["T1-01"] is False


@pytest.mark.parametrize("shape", ["unfenced, README after", "header line, untagged fence", "UNVERIFIED banner"])
def test_the_program_is_found_in_every_shape_both_arms_published(shape) -> None:
    readme = "\n# README.md\n\n`reconcile.py` reconciles usage ‑ events.\n\n```bash\npython reconcile.py --events e\n```\n"
    body = {"unfenced, README after": REFERENCE + readme,
            "header line, untagged fence": "--- reconcile.py ---\n```\n" + REFERENCE + "```\n" + readme,
            "UNVERIFIED banner": "UNVERIFIED ANSWER: Substantive verification was not completed. Reason: [PROGRAM_FAILED]"
                                 "\n\nAttempt 1: PROGRAM_FAILED" + grade_t1.CANDIDATE_MARK + REFERENCE + readme}[shape]
    program = grade_t1.candidate_program(body)
    assert program is not None and ast.dump(ast.parse(program)) == ast.dump(ast.parse(REFERENCE))
    assert "UNVERIFIED" not in program and "reconciles usage" not in program


def test_judge_packets_are_blind_to_arm_repeat_and_path(tmp_path, monkeypatch) -> None:
    for name in ("T2-P-r1", "T2-N-r1"):
        stage = tmp_path / name / "trunk" / "session" / "W-x" / "turns" / "turn_001" / "stages"
        (stage / "10_prompt" / "output").mkdir(parents=True)
        (stage / "30_plan" / "output").mkdir(parents=True)
        (stage / "10_prompt" / "output" / "current.md").write_text("Prepare the rollout plan.", encoding="utf-8")
        (stage / "30_plan" / "output" / "current.md").write_text("Write the runbook.", encoding="utf-8")
    monkeypatch.setattr(judge_pilot, "SESSIONS", tmp_path)
    monkeypatch.setattr(judge_pilot, "ROOT", tmp_path)
    packets = judge_pilot.items()
    assert len(packets) == 4 and len({p["id"] for p in packets}) == 4
    for packet in packets:
        shown = judge_pilot.judge.judge_prompt(packet["rubric"], "task", packet["text"])
        for leak in ("T2-P", "T2-N", "-r1", "arm", str(tmp_path)):
            assert leak not in shown and leak not in packet["id"]
        assert packet["rubric"].criteria[-1].id == "X-INVENTED"
        assert len(packet["rubric"].criteria) == 15  # Task 2's 14 criteria and the invented-requirement check


def test_the_mechanical_checks_read_the_yaml_and_the_timeline() -> None:
    runbook = "Total 225 minutes.\n\n```yaml\nflag:\n  name: v2_route\n  default: false\n```\n"
    assert judge_pilot.mechanical("T2", runbook) == {"yaml_blocks": 1, "yaml_parses": True, "states_225_minutes": True}
    assert judge_pilot.mechanical("T2", "```yaml\n: [\n```\n")["yaml_parses"] is False
    rows = ["2026-10-06T14:02:00Z,deploy,deploy record,observed", "2026-10-06T14:03:00Z,5xx above 4%,monitor,observed",
            "2026-10-06T14:05:00Z,alert acked,pager,observed", "2026-10-06T14:08:00Z,cache 91% to 63%,metrics,observed",
            "2026-10-06T14:11:00Z,rollback started,deploy,observed", "2026-10-06T14:14:00Z,rollback done,deploy,observed",
            "2026-10-06T14:16:00Z,5xx at baseline,monitor,observed"]
    report = "```csv\ntimestamp_utc,event,source,evidence_status\n" + "\n".join(rows) + "\n```\n"
    checks = judge_pilot.mechanical("T3", report)
    assert checks["header_exact"] and checks["all_utc"] and checks["sorted"] and checks["required_times_present"]
    unsorted = "```csv\ntimestamp_utc,event,source,evidence_status\n" + "\n".join(reversed(rows)) + "\n```\n"
    assert judge_pilot.mechanical("T3", unsorted)["sorted"] is False
    assert judge_pilot.mechanical("T3", "no table")["timeline_csv"] is False
    assert json.dumps(checks)  # recorded as JSON beside the judges' marks
