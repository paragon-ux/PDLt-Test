"""The forms a positive result takes under verified execution (L119, ADR-0030).

- computed: a program in the deliverable computes the result and prints it as the WITNESS line;
- certificate: the Result IR states the result as data (``basis: "certificate"``); the host gives that data to
  every program of the deliverable as ``WITNESS_DATA``, and a program checks it and prints it as the WITNESS line;
- argued: the Result IR states the result with ``basis: "proof"`` and its argument; no program is required, and the
  host publishes it as unverified (it cannot check an argument).

A program that writes out the data it prints (L113) states a result without computing or checking it; the host
returns that as a correction. The host reads the Result IR's fields only (RS-01, ADR-0018); nothing here parses text.
"""
from __future__ import annotations

import json
from typing import Any

CERTIFICATE_VARIABLE = "WITNESS_DATA"


def _positive(result_ir: Any) -> dict[str, Any] | None:
    witness = result_ir.get("witness") if isinstance(result_ir, dict) else None
    if isinstance(witness, dict) and witness.get("polarity", "positive") == "positive":
        return witness
    return None


def declared_certificate(result_ir: Any) -> dict[str, Any] | None:
    """The certificate the Result IR states, or None: a positive witness on the certificate basis with its data."""
    witness = _positive(result_ir)
    if witness and witness.get("basis") == "certificate" and isinstance(witness.get("data"), dict) and witness["data"]:
        return witness["data"]
    return None


def argued_result(witness: Any) -> bool:
    """A positive witness on the proof basis, with its data and a non-empty argument."""
    return (isinstance(witness, dict) and witness.get("polarity", "positive") == "positive"
            and witness.get("basis") == "proof" and isinstance(witness.get("data"), dict) and bool(witness["data"])
            and bool(str(witness.get("argument") or "").strip()))


def with_certificate(source: str, certificate: dict[str, Any] | None) -> str:
    """The program as the host runs it: with a certificate, one first line binds it to WITNESS_DATA."""
    if certificate is None:
        return source
    return f"{CERTIFICATE_VARIABLE} = __import__('json').loads({json.dumps(json.dumps(certificate))})\n" + source
