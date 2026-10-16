"""What a published result rests on (L121 flag E-1), so a consumer can tell a result the host established from one
it did not. The host writes it beside the result when it closes a turn (``provenance.json``); the MCP server serves
it with every artifact of the turn, and derives it from the turn's recorded files for turns closed before.

Verification levels:
  host_verified     the host reproduced the result: a program it ran printed the witness (computed or certificate);
  contract_checked  the reply passed the host's contract checks, but no check of the task's own result ran
                    (STANDARD_EXECUTION: for code, the requested behaviour was not tested; ledger L115);
  unverified        published without the host establishing it (CLOSED_UNVERIFIED: a negative claim, a deliverable
                    declaring requirements open, or a result resting on its argument; ADR-0019 amendment, L116).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "pdlt.provenance/1"
STANDARD_CAVEAT = ("The host checked the reply against its contract and ran its programs, but ran no test of the "
                   "behaviour the request asks for; a code deliverable's correctness is not established (ledger L115).")


def witness_form(witness: Any, verification: dict[str, Any] | None) -> str:
    """computed, certificate, argued, negative or none (ADR-0030)."""
    if not isinstance(witness, dict):
        return "none"
    if witness.get("polarity") == "negative":
        return "negative"
    verification = verification or {}
    if verification.get("argued"):
        return "argued"
    if verification.get("certificate_checked"):
        return "certificate"
    return "computed" if verification.get("sandbox_reproduced") else "none"


def verification_basis(status: str, requires_verified_execution: bool | None, verification: dict[str, Any] | None,
                       witness: Any, unverified_reason: str | None) -> dict[str, Any]:
    """None for requires_verified_execution: the turn's routing is not recorded, so the problem class is unknown and
    the level is never host_verified."""
    form = witness_form(witness, verification)
    reproduced = bool((verification or {}).get("sandbox_reproduced")) and form in ("computed", "certificate")
    if status != "CLOSED_SUCCESS":
        level = "unverified"
    elif requires_verified_execution and reproduced and not (verification or {}).get("provisional"):
        level = "host_verified"
    else:
        level = "contract_checked"
    return {
        "level": level,
        "problem_class": ("unknown" if requires_verified_execution is None
                          else "VERIFIED_EXECUTION" if requires_verified_execution else "STANDARD_EXECUTION"),
        "witness_form": form,
        "reproduced_by_host": reproduced,
        "unverified_reason": unverified_reason if status != "CLOSED_SUCCESS" else None,
        "caveat": STANDARD_CAVEAT if level == "contract_checked" else None,
    }


def record(*, status: str, requires_verified_execution: bool, verification: dict[str, Any] | None, witness: Any,
           unverified_reason: str | None, deliverable_sha256: str, closed_at_utc: str, model: Any = None,
           pdlt_version: str | None = None) -> dict[str, Any]:
    """The provenance the host writes when it closes a turn with a result."""
    if pdlt_version is None:
        from pdl_taskmaster import __version__ as pdlt_version
    return {
        "schema": SCHEMA,
        "recorded_by": "host at closure",
        "status": status,
        "verification": verification_basis(status, requires_verified_execution, verification, witness,
                                           unverified_reason),
        "deliverable_sha256": deliverable_sha256,
        "model": model,
        "pdlt_version": pdlt_version,
        "closed_at_utc": closed_at_utc,
    }


def derive(turn: Path) -> dict[str, Any] | None:
    """Provenance for a turn closed before the host recorded it, from the turn's own files (turn.json, routing.json,
    events). The model is not recorded there. A missing routing or event record makes the claim weaker, never
    stronger. None when turn.json cannot be read."""
    try:
        meta = json.loads((turn / "turn.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    try:
        routing: dict[str, Any] | None = json.loads((turn / "routing.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        routing = None
    try:
        events = [json.loads(line) for line in
                  (turn / "events" / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    except (OSError, ValueError):
        events = []
    verification: dict[str, Any] | None = None
    witness: Any = None
    reason: str | None = None
    for event in events:
        payload = event.get("payload") or {}
        if event.get("kind") == "VERIFICATION_PASSED":
            verification = payload
        elif event.get("kind") == "RESULT_IR_VALIDATED":
            witness = (payload.get("ir") or {}).get("witness")
        elif event.get("kind") == "CLOSED_UNVERIFIED":
            reason = payload.get("reason")
    status = str(meta.get("status"))
    return {
        "schema": SCHEMA,
        "recorded_by": "derived from the turn's recorded events (closed before the host recorded provenance)",
        "status": status,
        "verification": verification_basis(
            status, None if routing is None else bool(routing.get("requires_verified_execution")), verification,
            witness, reason),
        "deliverable_sha256": meta.get("deliverable_sha256"),
        "model": None,
        "pdlt_version": None,
        "closed_at_utc": meta.get("updated_at_utc"),
    }
