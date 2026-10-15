"""L110: a negative result is provisional. The host can run a program and see it print 'no result exists',
not check the claim; it labels the result unverified and never reports it as checked."""
from pdl_taskmaster.runtime import presentation
from pdl_taskmaster.runtime.text_blocks import split_published_ir

from test_execution_phase import _ir, _run

SEARCH = ("import json\nprint('WITNESS: ' + json.dumps({'polarity': 'negative', 'basis': 'search', "
          "'search_exhausted': True, 'nodes_explored': 3, 'method': 'backtracking'}))")


def test_a_printed_search_exhausted_claim_is_provisional_and_labelled(tmp_path):
    engine, response, _, events = _run(
        tmp_path, [{"kind": "RESULT", "body": SEARCH, "result_ir": _ir()}], problem_class="VERIFIED_EXECUTION")
    text, ir = split_published_ir(response.text)
    passed = [e["payload"] for e in events if e["kind"] == "VERIFICATION_PASSED"][-1]
    assert passed["provisional"] is True and passed["domain_checked"] is False
    assert passed["negative_claim_unchecked"] is True and passed["sandbox_reproduced"] is True
    assert any(e["kind"] == "NEGATIVE_CLAIM_UNCHECKED" for e in events)
    assert ir["witness"]["provisional"] is True and text.endswith(presentation.negative_claim_note())


def test_a_printed_positive_witness_is_not_affected(tmp_path):
    body = "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'n': sum(range(4))}}))"
    engine, response, _, events = _run(
        tmp_path, [{"kind": "RESULT", "body": body, "result_ir": _ir()}], problem_class="VERIFIED_EXECUTION")
    passed = [e["payload"] for e in events if e["kind"] == "VERIFICATION_PASSED"][-1]
    assert passed["provisional"] is False and passed["negative_claim_unchecked"] is False
    assert not any(e["kind"] == "NEGATIVE_CLAIM_UNCHECKED" for e in events)
