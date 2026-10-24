"""L151 step 3 (the user, 2026-10-22): the plaininput part, a measurement that ships nothing. EXECUTE_UNCONFIRMED
receives its projection as indented plain text instead of a JSON document, every key and value kept, and the worker
instructions without their two role lines. With freetext as well, nothing in the call is JSON. Without the part every
request is unchanged (the parity goldens hold). Offline; the worker and System 1 are scripted."""
from __future__ import annotations

import json

import pytest

from pdl_taskmaster.providers import api_worker
from pdl_taskmaster.providers.api_worker import plain_document
from test_l149_ablation import _body, _requests


@pytest.fixture(scope="module")
def calls(tmp_path_factory):
    return {parts: _requests(tmp_path_factory.mktemp("p"), parts)
            for parts in ((), ("plaininput",), ("freetext", "plaininput"))}


def _strings(node):
    if isinstance(node, dict):
        for key, value in node.items():
            yield key
            yield from _strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _strings(value)
    elif isinstance(node, str):
        yield node


def test_only_the_form_of_execute_unconfirmed_changes(calls):
    base, plain = calls[()], calls[("plaininput",)]
    assert _body(plain["BOOTSTRAP_ANALYSIS"]) == _body(base["BOOTSTRAP_ANALYSIS"])
    assert plain["EXECUTE_UNCONFIRMED"].prompt == base["EXECUTE_UNCONFIRMED"].prompt


def test_the_input_is_plain_text_with_every_value(calls):
    request = calls[("plaininput",)]["EXECUTE_UNCONFIRMED"]
    document = request.projection.document
    sent = _body(request)["input"]
    rendered = sent[:-len(api_worker._JSON_ONLY_SUFFIX)]
    assert sent.endswith(api_worker._JSON_ONLY_SUFFIX)  # the reply is still JSON without freetext
    assert not rendered.lstrip().startswith("{") and '"operation_inputs"' not in rendered
    for text in _strings(document):
        for line in text.split("\n"):
            assert line in rendered
    assert rendered == plain_document(json.dumps(document, ensure_ascii=False))


def test_the_role_lines_are_left_out(calls):
    base = _body(calls[()]["EXECUTE_UNCONFIRMED"])["instructions"]
    plain = _body(calls[("plaininput",)]["EXECUTE_UNCONFIRMED"])["instructions"]
    assert api_worker._BOOTSTRAP_ROLE_LINES in base and api_worker._BOOTSTRAP_ROLE_LINES not in plain
    assert plain == base.replace(api_worker._BOOTSTRAP_ROLE_LINES, "")


def test_with_freetext_nothing_in_the_call_is_json(calls):
    body = _body(calls[("freetext", "plaininput")]["EXECUTE_UNCONFIRMED"])
    assert "text" not in body and not body["input"].endswith(api_worker._JSON_ONLY_SUFFIX)
    assert not body["input"].lstrip().startswith("{")
    assert "JSON object" not in body["instructions"] and "stateless operation worker" not in body["instructions"]
    assert api_worker._BOOTSTRAP_FREETEXT_LINES in body["instructions"]


def test_the_renderer_keeps_structure_readable():
    text = plain_document(json.dumps({"a": "x\ny", "b": [{"c": 1, "d": None}, "e"], "f": {}, "g": True}))
    assert text == "a: x\n  y\nb:\n  - c: 1\n    d: none\n  - e\nf: (empty)\ng: true"
