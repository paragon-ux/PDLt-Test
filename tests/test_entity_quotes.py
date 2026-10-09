"""Locating text a model copied from the request (``quotes.RequestText``, ledger L100), which the
request index's checks rely on (tests/test_request_index.py). All offline; no model call."""
from __future__ import annotations

from pydantic import TypeAdapter

from pdl_taskmaster.runtime.quotes import RequestText
from pdl_taskmaster.runtime.wire_payloads import WitnessPayload

# --- locating a copy -------------------------------------------------------------------------

def test_locate_ignores_typography_and_returns_the_requests_own_text():
    text = RequestText("A non-negative integer x in the user’s list, “as written”.")
    # gpt-oss writes U+2011 and U+202F where the request has "-" and " "; quotes and spaces vary
    assert text.locate("non‑negative integer") == "non-negative integer"
    assert text.locate("the user's  list") == "the user’s list"
    assert text.locate('"as written"') == "“as written”"
    assert text.locate("'x'") == "x"
    assert text.locate("integer x.") == "integer x"


def test_locate_reads_an_escaped_quotation_mark_as_the_mark():
    text = RequestText('Trace the domain "api.example.com" from a cold cache.')
    assert text.locate('Trace the domain \\"api.example.com\\" from') == 'Trace the domain "api.example.com" from'


def test_locate_reads_inline_code_as_its_text_and_keeps_the_requests_marks():
    text = RequestText("The feature flag must default to `false`; route all traffic back to v1.")
    assert text.locate("must default to false;") == "must default to `false`;"
    assert text.locate("must default to off;") is None  # formatting only, never a paraphrase


def test_locate_falls_back_to_case_but_never_to_spelling():
    text = RequestText("The recieved Colour codes")
    assert text.locate("colour codes") == "Colour codes"  # case only as a fallback, request's casing kept
    assert text.locate("received") is None  # a corrected spelling is not the user's text
    assert text.locate("Color") is None
    assert text.locate("codes of colour") is None  # not one continuous piece
    assert text.locate("") is None and text.locate("   ") is None and text.locate(None) is None


def test_locate_reads_every_source():
    text = RequestText("Revise the summary.", None, "Earlier deliverable: the Q3 table")
    assert text.locate("Q3 table") == "Q3 table"


def test_witness_polarity_is_untouched():
    """L100 removed polarity from task entities only; the witness union still discriminates on it."""
    adapter = TypeAdapter(WitnessPayload)
    assert type(adapter.validate_python({"polarity": "positive", "data": {"x": 1}})).__name__ == "PositiveWitness"
    negative = adapter.validate_python({"polarity": "negative", "basis": "proof", "argument": "parity"})
    assert type(negative).__name__ == "NegativeWitness"
