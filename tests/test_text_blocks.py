"""CommonMark code extraction and literal wire/output readers."""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

from pdl_taskmaster.runtime.text_blocks import fenced_blocks, split_published_ir, unfence_json, witness_payload

ROOT = Path(__file__).resolve().parents[1]


def test_fenced_blocks_by_language():
    text = "Intro\n```python\nprint(1)\n```\nmid\n```json\n{}\n```\n```py\nx = 2\n```\n"
    assert fenced_blocks(text, ("python", "py")) == ["print(1)\n", "x = 2\n"]
    assert fenced_blocks(text, ("json",)) == ["{}\n"]
    assert fenced_blocks("```python\nunterminated", ("python",)) == ["unterminated"]


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


def test_info_strings_inside_an_open_fence_do_not_reopen_it():
    text = "Notes\n```text\nexplanation\n```python\nprint(1)\n```\nmore\n```python\nprint(2)\n```\n"
    assert fenced_blocks(text, ("python",)) == ["print(2)\n"]
    assert fenced_blocks(text, ("text",)) == ["explanation\n```python\nprint(1)\n"]
    assert fenced_blocks("```python\nA = 1\n```python\nB = 2\n```\n", ("python",)) == [
        "A = 1\n```python\nB = 2\n"]


def test_a_line_that_mentions_a_fence_does_not_end_a_block_that_is_closed_later():
    code = ('```python\n"""Converts text.\n    7. Code blocks: indented or fenced with ```\n"""\n'
            "def convert(text):\n    return text\n```\n")
    assert fenced_blocks(code, ("python",)) == [
        '"""Converts text.\n    7. Code blocks: indented or fenced with ```\n"""\ndef convert(text):\n    return text\n']


def test_a_fence_attached_to_code_is_literal_content():
    assert fenced_blocks("```py\nx = 2```\n", ("py",)) == ["x = 2```\n"]


@pytest.mark.parametrize("indent", range(4))
def test_opening_fence_indentation_is_removed_without_dedenting_code(indent):
    pad = " " * indent
    text = f'{pad}```python\n{pad}if True:\n{pad}    print("ok")\n```\n'
    assert fenced_blocks(text, ("python",)) == ['if True:\n    print("ok")\n']


@pytest.mark.parametrize("text,expected", [
    ("    ```python\n    print(1)\n    ```\n", []),
    ("\t```python\n\tprint(1)\n\t```\n", []),
    ("~~~Py extra\nprint(1)\n~~~~\n", ["print(1)\n"]),
    ("````python\n```\nprint(1)\n````\n", ["```\nprint(1)\n"]),
    ("```python\n~~~\nprint(1)\n```\n", ["~~~\nprint(1)\n"]),
    ("- Example:\n\n  ```python\n  if True:\n      print(1)\n  ```\n", ["if True:\n    print(1)\n"]),
    ("1. Example:\n\n   > ~~~py\n   > print(1)\n   > ~~~\n", ["print(1)\n"]),
    ("```python\n\tprint(1)\n```\n", ["\tprint(1)\n"]),
    ('```python\ns = """first\n  second\n"""\n```\n', ['s = """first\n  second\n"""\n']),
])
def test_commonmark_fence_and_container_rules(text, expected):
    assert fenced_blocks(text, ("python", "py")) == expected


def test_whole_python_modules_are_not_rewritten_as_markdown():
    from pdl_taskmaster.runtime.session_engine import _python_blocks

    source = 'if True:\n    print("literal ```python")\n'
    assert _python_blocks(source) == [source]
    broken = 'import sys\nif True:\nprint("indentation error")\n'
    assert _python_blocks(broken) == [broken]
