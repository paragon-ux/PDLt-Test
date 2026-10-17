"""Extension samples for the L124 tests: written for the tests, derived from no benchmark prompt.

- LABELLED_LIST: recognised by a criterion, no witness, no verifier.
- ROW_TOTALS: an outside task type with its own verifier; the conformance kit's sample external type.
- Misbehaving verifiers: lenient (accepts anything and tries to rewrite the witness), raising, and one answering
  with a bool.
"""
from __future__ import annotations

from pdl_taskmaster.extensions import task_types, verifiers
from pdl_taskmaster.verification.checkers.base import VerificationVerdict

MARKER = "lists whose every item carries a short label"
ROUTE_OPERATIONS = sorted(task_types.ROUTES["confirmed"].required | task_types.ROUTES["unconfirmed"].required)


def no_witness_type(category: str = "LABELLED_LIST", **changes) -> dict:
    declaration = {
        "profile": task_types.PROFILE_ID,
        "category": category,
        "prompt": {"classification": {"criterion": f"The task asks for {MARKER}."}, "instructions": []},
        "witness_forms": [],
        "deliverable": {"body": "text", "result_ir": "not_requested"},
        "route": ["confirmed", "unconfirmed"],
        "operations": ROUTE_OPERATIONS,
        "verifier": "none",
    }
    declaration.update(changes)
    return declaration


def witness_type(category: str, verifier: str, forms=("computed",), **changes) -> dict:
    declaration = no_witness_type(category,
                                  prompt={"classification": None, "instructions": ["result_ir", "witness"]},
                                  witness_forms=list(forms),
                                  deliverable={"body": "text", "result_ir": "required"}, verifier=verifier)
    declaration.update(changes)
    return declaration


def verifier(name: str, checker, domain: str | None = None) -> dict:
    return {"profile": verifiers.PROFILE_ID, "name": name, "domain": domain or f"{name}-domain", "checker": checker,
            "reproduction": "required"}


class RowTotalsChecker:
    """The witness gives rows of numbers and their totals; each total must be its row's sum."""

    name = "row-totals"

    def check(self, witness, constraints, *, body=None):
        data = witness.get("data") if isinstance(witness, dict) else None
        rows = data.get("rows") if isinstance(data, dict) else None
        totals = data.get("totals") if isinstance(data, dict) else None
        valid = (isinstance(rows, list) and isinstance(totals, list) and len(rows) == len(totals) > 0
                 and all(isinstance(r, list) and sum(r) == t for r, t in zip(rows, totals)))
        return VerificationVerdict(valid=valid, diagnostic=None if valid else "each total must equal its row's sum")


ROW_TOTALS_VERIFIER = verifier("row-totals", RowTotalsChecker(), domain="row-totals")
ROW_TOTALS = no_witness_type(
    "ROW_TOTALS",
    prompt={"classification": {"criterion": "The task gives rows of numbers and asks for the total of each row."},
            "instructions": ["result_ir", "witness"]},
    witness_forms=["computed"], deliverable={"body": "text", "result_ir": "required"}, verifier="row-totals")
ROW_TOTALS_PROGRAM = ("import json\nrows = [[2, 3, 5], [7, 11], [13]]\ntotals = [sum(r) for r in rows]\n"
                      "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'rows': rows, "
                      "'totals': totals}}))")
IR = {"files": [], "reconciliation": [
    {"requirement": "R1", "status": "satisfied", "evidence": {"path": "execution://body"}}], "open_defects": []}
ROW_TOTALS_SAMPLE = {"body": f"```python\n{ROW_TOTALS_PROGRAM}\n```", "result_ir": IR}

POSITIVE_PROGRAM = ("import json\nvalues = [a * b for a in range(2, 5) for b in range(3, 6)]\n"
                    "print('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'largest': max(values)}}))")
POSITIVE_SAMPLE = {"body": f"```python\n{POSITIVE_PROGRAM}\n```", "result_ir": IR}


class Lenient:
    """Accepts every witness, and tries to rewrite the one it is given."""

    name = "lenient"

    def __init__(self):
        self.arguments = []

    def check(self, witness, constraints, *, body=None):
        self.arguments.append((witness, constraints, body))
        if isinstance(witness, dict):
            witness["data"] = {"rewritten": True}
            witness["provisional"] = False
        return VerificationVerdict(valid=True, details={"claims": "host_verified"})


class Raising:
    name = "raising"

    def check(self, witness, constraints, *, body=None):
        raise RuntimeError("the checker broke")


class AnswersBool:
    name = "answers-bool"

    def check(self, witness, constraints, *, body=None):
        return True
