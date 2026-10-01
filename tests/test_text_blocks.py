"""String-only readers for model and program text (no regular expressions)."""
from __future__ import annotations

import ast
from pathlib import Path

from pdl_taskmaster.runtime.text_blocks import fenced_blocks, split_published_ir, unfence_json, witness_payload

ROOT = Path(__file__).resolve().parents[1]


def test_fenced_blocks_by_language():
    text = "Intro\n```python\nprint(1)\n```\nmid\n```json\n{}\n```\n```py\nx = 2```\n"
    assert fenced_blocks(text, ("python", "py")) == ["print(1)\n", "x = 2\n"]
    assert fenced_blocks(text, ("json",)) == ["{}\n"]
    assert fenced_blocks("```python\nunterminated", ("python",)) == []


def test_witness_payload_and_unfence():
    assert witness_payload("  WITNESS: {\"a\": 1}  ") == '{"a": 1}'
    assert witness_payload("no witness here") is None
    assert unfence_json('```json\n{"a": 1}\n```') == '{"a": 1}' and unfence_json('{"a": 1}') == '{"a": 1}'


def test_split_published_ir_reads_only_the_appended_host_block():
    assert split_published_ir('Answer 5.\n\n```json\n{"witness": null}\n```') == ("Answer 5.", {"witness": None})
    assert split_published_ir("Answer 5.") == ("Answer 5.", None)
    assert split_published_ir("text\n```json\nnot json\n```")[1] is None


def test_model_facing_runtime_code_uses_no_regex():
    """What the harness reads from model responses and program output is read with
    exact string operations (text_blocks); regex remains only in the input
    quarantine, the notation lint, invocation parsing and internal file names."""
    for name in ("runtime/session_engine.py", "runtime/result_ir.py", "runtime/operation_bridge.py",
                 "runtime/text_blocks.py", "runtime/workspace.py"):
        tree = ast.parse((ROOT / "src/pdl_taskmaster" / name).read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and isinstance(n.func.value, ast.Name) and n.func.value.id == "re"]
        allowed = {"runtime/session_engine.py": 2, "runtime/workspace.py": 1}  # invocation prefix; turn_NNN dir names
        assert len(calls) <= allowed.get(name, 0), (name, [ast.unparse(c)[:60] for c in calls])
