from __future__ import annotations

import json
import pytest

from pdl_taskmaster.runtime.result_ir import load_ir_from_deliverable
from pdl_taskmaster.runtime.session_engine import SessionEngine


def test_load_ir_with_witness():
    deliverable = """
YES, the set of 6 integers can be partitioned into 2 sum triples.

```json
{
  "files": [
    {
      "filename": "result.txt",
      "satisfies": ["R1"],
      "evidence": {"path": "execution://body"}
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {"path": "execution://body"}
    }
  ],
  "open_defects": [],
  "witness": {
    "polarity": "positive",
    "evidence": {"path": "execution://witness"},
    "data": {
      "triples": [[1, 2, 3], [4, 5, 9]]
    }
  }
}
```
"""
    ir = load_ir_from_deliverable(deliverable)
    assert ir is not None
    assert "witness" in ir
    assert ir["witness"]["polarity"] == "positive"
    assert ir["witness"]["data"]["triples"] == [[1, 2, 3], [4, 5, 9]]


def test_parse_sandbox_witness_protocol_forms():
    from pdl_taskmaster.runtime.session_engine import _parse_sandbox_witness

    # 1. Whole-stdout JSON object is the printed witness payload
    cand1 = _parse_sandbox_witness('{"items": [[1, 2, 3], [4, 5, 9]]}')
    assert cand1 is not None
    assert cand1["polarity"] == "positive"
    assert cand1["data"]["items"] == [[1, 2, 3], [4, 5, 9]]

    # 2. WITNESS protocol line (last line wins), surrounded by other output
    out2 = 'progress...\nWITNESS: {"answer": 1}\nWITNESS: {"answer": 2}\n'
    cand2 = _parse_sandbox_witness(out2)
    assert cand2["data"] == {"answer": 2}

    # 3. Explicit polarity is preserved
    out3 = 'WITNESS: {"polarity": "negative", "search_exhausted": true, "nodes_explored": 42, "method": "dfs"}'
    cand3 = _parse_sandbox_witness(out3)
    assert cand3["polarity"] == "negative"
    assert cand3["nodes_explored"] == 42


def test_parse_sandbox_witness_does_not_scrape_free_text():
    from pdl_taskmaster.runtime.session_engine import _parse_sandbox_witness

    assert _parse_sandbox_witness("Hamiltonian path found: [0, 1, 2, 3]") is None
    assert _parse_sandbox_witness("[(1, 2, 3), (4, 5, 9)]") is None
    assert _parse_sandbox_witness('note {"triples": [[1, 2, 3]]} embedded in prose') is None
    assert _parse_sandbox_witness("") is None


def test_missing_witness_fails_closed_without_scraping_body():
    from pdl_taskmaster.verification.output_verifier import OutputVerifier

    verdict = OutputVerifier().check(
        None,
        {"prompt_body": "PARTITION the list", "supplied_input": "1, 2, 3, 4, 5, 9, 6, 7, 13"},
        domain="partition_sum_triples",
        body="The solution is (1, 2, 3), (4, 5, 9), and (6, 7, 13).",
    )
    assert verdict.valid is False
    assert "Missing witness in Result IR" in (verdict.diagnostic or "")
