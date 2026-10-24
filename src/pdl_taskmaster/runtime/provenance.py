"""What a published result rests on (L121 flag E-1), so a consumer can tell a result the host established from one
it did not. The host writes it beside the result when it closes a turn (``provenance.json``); the MCP server serves
it with every artifact of the turn, and derives it from the turn's recorded files for turns closed before.

Verification levels:
  host_verified     the host reproduced the result: a program it ran printed the witness (computed or certificate);
                    with no domain checker registered it does not judge that witness correct (L140)
  contract_checked  the reply passed the host's contract checks, but no check of the task's own result ran
                    (STANDARD_EXECUTION: for code, the requested behaviour was not tested; ledger L115); it closes
                    CLOSED_UNVERIFIED with the reason contract_checked (L164);
  unverified        published without the host establishing it (CLOSED_UNVERIFIED: a negative claim, a deliverable
                    declaring requirements open, or a result resting on its argument; ADR-0019 amendment, L116).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA = "pdlt.provenance/1"
# L164: the reason a result the host checked only against its contract closes CLOSED_UNVERIFIED (exit 0 means
# host-verified, ADR-0019 amendment).
CONTRACT_ONLY = "contract_checked"
STANDARD_CAVEAT = ("The host checked the reply against its contract and ran its programs, but ran no test of the "
                   "behaviour the request asks for; a code deliverable's correctness is not established (ledger L115).")
# L140: added when programs the host ran failed or were stopped and the reply was published without that being fed
# back to the model (standard execution feeds back only a program's own failures under Tier D1).
NOT_FED_BACK_CAVEAT = ("Programs the host ran did not succeed ({codes}), and this was not returned to the model "
                       "before the result was published.")


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


def host_established(requires_verified_execution: bool | None, verification: dict[str, Any] | None, witness: Any,
                     *, verifier: str | None = None) -> bool:
    """Whether the host reproduced the result (the level host_verified): a verified task whose bound verifier is not
    "none", with a computed or certificate witness a program the host ran printed, not provisional."""
    reproduced = (bool((verification or {}).get("sandbox_reproduced"))
                  and witness_form(witness, verification) in ("computed", "certificate"))
    return bool(requires_verified_execution and verifier != "none" and reproduced
                and not (verification or {}).get("provisional"))


def verification_basis(status: str, requires_verified_execution: bool | None, verification: dict[str, Any] | None,
                       witness: Any, unverified_reason: str | None, *, task_type: str | None = None,
                       verifier: str | None = None,
                       run_failures_not_fed_back: list[str] | None = None) -> dict[str, Any]:
    """None for requires_verified_execution: the turn's routing is not recorded, so the problem class is unknown and
    the level is never host_verified. ``task_type`` names the problem class (L124); a task type bound to no verifier
    ("none") is never host_verified, whatever the verification record says. ``run_failures_not_fed_back`` (L140):
    the registry codes of programs that failed or were stopped without that being fed back; when there are any they
    are listed and the caveat says so. Turns closed before L140 do not record them."""
    form = witness_form(witness, verification)
    reproduced = bool((verification or {}).get("sandbox_reproduced")) and form in ("computed", "certificate")
    if status != "CLOSED_SUCCESS":
        level = "contract_checked" if unverified_reason == CONTRACT_ONLY else "unverified"
    elif host_established(requires_verified_execution, verification, witness, verifier=verifier):
        level = "host_verified"
    else:  # closed before L164, when a contract-checked result closed CLOSED_SUCCESS
        level = "contract_checked"
    return {
        "level": level,
        "problem_class": (task_type if task_type is not None else "unknown" if requires_verified_execution is None
                          else "VERIFIED_EXECUTION" if requires_verified_execution else "STANDARD_EXECUTION"),
        "witness_form": form,
        "reproduced_by_host": reproduced,
        "unverified_reason": unverified_reason if status != "CLOSED_SUCCESS" else None,
        "caveat": _caveat(level, run_failures_not_fed_back),
        **({"run_failures_not_fed_back": list(run_failures_not_fed_back)} if run_failures_not_fed_back else {}),
        # A registered domain checker judged the witness (L124); the structural fallback is not named.
        **({"checker": (verification or {})["checker"]} if (verification or {}).get("checker") else {}),
    }


def _caveat(level: str, run_failures_not_fed_back: list[str] | None) -> str | None:
    parts = [STANDARD_CAVEAT] if level == "contract_checked" else []
    if run_failures_not_fed_back:
        parts.append(NOT_FED_BACK_CAVEAT.format(codes=", ".join(run_failures_not_fed_back)))
    return " ".join(parts) or None


def record(*, status: str, requires_verified_execution: bool, verification: dict[str, Any] | None, witness: Any,
           unverified_reason: str | None, deliverable_sha256: str, closed_at_utc: str, model: Any = None,
           pdlt_version: str | None = None, task_type: str | None = None,
           verifier: str | None = None, run_failures_not_fed_back: list[str] | None = None) -> dict[str, Any]:
    """The provenance the host writes when it closes a turn with a result."""
    if pdlt_version is None:
        from pdl_taskmaster import __version__ as pdlt_version
    return {
        "schema": SCHEMA,
        "recorded_by": "host at closure",
        "status": status,
        "verification": verification_basis(status, requires_verified_execution, verification, witness,
                                           unverified_reason, task_type=task_type, verifier=verifier,
                                           run_failures_not_fed_back=run_failures_not_fed_back),
        "deliverable_sha256": deliverable_sha256,
        "model": model,
        "pdlt_version": pdlt_version,
        "closed_at_utc": closed_at_utc,
    }


def _bound_verifier(task_type: str | None) -> str | None:
    """The verifier a task type registered here binds; None when the turn names no task type, or one not
    registered here (the witness requirement in its routing still bounds the level)."""
    if task_type is None:
        return None
    from pdl_taskmaster.extensions import task_types

    return task_types.REGISTRY.get(task_type).verifier if task_type in task_types.REGISTRY else None


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
            witness, reason, task_type=(routing or {}).get("task_type"),
            verifier=_bound_verifier((routing or {}).get("task_type"))),
        "deliverable_sha256": meta.get("deliverable_sha256"),
        "model": None,
        "pdlt_version": None,
        "closed_at_utc": meta.get("updated_at_utc"),
    }
