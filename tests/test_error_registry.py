"""The verification error registry: a fixed, task-neutral table of the findings
System 2 sees after a failed output."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from pdl_taskmaster.verification.error_registry import REGISTRY, Finding, finding_codes

ROOT = Path(__file__).resolve().parents[1]

_FACTS = {"block": 1, "step_limit": 10_000_000, "timeout_seconds": 30.0, "memory_mb": 256, "exit_code": 1,
          "stderr": "", "detail": "R1 is not reconciled", "diagnostic": "the witness is missing.",
          "host_observation": "python block 1 exited 0 and printed nothing", "count": 2}


@pytest.mark.parametrize("code", sorted(REGISTRY))
def test_every_entry_states_observation_rule_and_next_attempt(code):
    text = Finding(code, **_FACTS)
    assert text.code == code and text.startswith(f"[{code}] ")
    assert " Rule: " in text and " Next attempt: " in text
    assert "{" not in text  # every placeholder filled


def test_findings_are_plain_strings_with_codes():
    finding = Finding("STEP_BUDGET_EXCEEDED", block=2, step_limit=100_000)
    assert isinstance(finding, str) and json.loads(json.dumps(finding)) == str(finding)
    assert "stopped after 100,000 steps" in finding and "same budget of 100,000 steps" in finding
    assert finding_codes([finding, "legacy text"]) == ["STEP_BUDGET_EXCEEDED", "UNREGISTERED"]


def test_registry_names_no_method():
    """GUARD-03/04: entries state the environment and contract, never a method.
    (Catalogue vocabulary is covered for every src file by the contamination scan.)"""
    text = " ".join(f"{s.observed} {s.rule} {s.next_attempt}" for s in REGISTRY.values()).lower()
    for method in ("backtrack", "prun", "dynamic programming", "memoiz", "greedy", "branch", "heuristic",
                   "partition", "triple", "sort", "cache", "recurs"):
        assert method not in text, method


def test_every_engine_finding_is_registered():
    """The engine builds findings only through the registry."""
    source = (ROOT / "src/pdl_taskmaster/runtime/session_engine.py").read_text(encoding="utf-8")
    used = set(re.findall(r'Finding\(\s*"([A-Z_]+)"', source))
    assert used and used <= set(REGISTRY)
    assert "Substantive verification error" not in source
