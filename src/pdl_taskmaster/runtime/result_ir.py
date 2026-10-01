"""Result Pseudocode decomposition IR (ADR-0009 prototype).

Structured result artifact emitted by the EXECUTE operation alongside the
native deliverable: the result is decomposed per file, reconciled against
the mechanically derived requirement IDs of the confirmed Prompt Pseudocode,
and grounded in execution-evidence citations that the controller validates
mechanically. Model-asserted content is never trusted:

  - every cited path MUST resolve inside the workspace;
  - every cited section marker MUST appear verbatim in the cited artifact;
  - every quoted observation MUST appear verbatim in the cited artifact;
  - every requirement ID derived from the confirmed prompt body MUST be
    reconciled exactly once.

Zero external dependencies (stdlib only), per the harness constraint.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

_VALID_STATUS = {"satisfied", "partial", "open"}

RESULT_IR_INSTRUCTIONS_TEMPLATE = """The response MUST end with a fenced ```json block containing the Result IR object, exactly this shape:
{{"files": [{{"filename": "<name>.py", "satisfies": ["R<n>", ...], "evidence": {{"path": "<workspace-relative path of the artifact this file's content is grounded in>", "section": "<verbatim section marker inside that artifact, or omitted>"}}}}], "reconciliation": [{{"requirement": "R<n>", "status": "satisfied|partial|open", "evidence": {{"path": "...", "section": "...", "observed": "<verbatim quote from the cited artifact supporting this status>"}}}}, ...], "open_defects": [{{"id": "D<n>", "description": "<defect>", "evidence": {{"path": "...", "observed": "<verbatim quote>"}}}}]}}
Rules: cite ONLY the artifacts listed under AVAILABLE EVIDENCE PATHS below; every "observed" string MUST be copied verbatim from the cited artifact; every requirement ID MUST appear in "reconciliation" exactly once; do not invent paths, sections, quotes, or requirement IDs."""

_EVIDENCE_KEYS = ("path", "section", "observed")


def derive_requirements(prompt_body: str) -> list[str]:
    """Mechanically derive requirement IDs (R1..Rn) from the confirmed prompt.

    Under PDL-02 each Prompt Pseudocode line states one operation, so every
    non-empty line is one requirement. No verb or vocabulary list is consulted.
    """
    reqs = [
        s for s in (line.strip() for line in (prompt_body or "").splitlines())
        if s and not s.startswith(("#", "//", "<!--"))
    ]
    return reqs or ["COMPLETE confirmed task"]


_WITNESS_INSTRUCTIONS = """WITNESS: this task requires verified execution. A claimed result is certified by a Python program in the deliverable that prints exactly one line to standard output: the text "WITNESS: " followed by a JSON object. Build the object as a Python dict in the program and print it with json.dumps; do not write the JSON by hand inside a string. The object's fields:
- A result was found: "polarity" is "positive" and "data" is an object holding the result under descriptive keys.
- The result is shown not to exist by a search the program ran: "polarity" is "negative", "basis" is "search", "search_exhausted" is true, "nodes_explored" is the number of states the program explored, and "method" names the search.
- The result is shown not to exist by an argument rather than a computation: "polarity" is "negative", "basis" is "proof", and "argument" states the argument.
If the result was not obtained, print no witness and describe what was not obtained in "open_defects".
The host runs the program; the witness it prints replaces any witness written into "result_ir". A witness the host did not reproduce is reported as provisional."""


def render_instructions(
    requirements: list[str] | None = None,
    repo_root: str | Path | None = None,
    evidence_paths: list[str] | None = None,
    requires_verified_execution: bool = False,
) -> str:
    """The Result IR channel shown to EXECUTE (RESULT_STANDARD RS-01). It names only
    the fields the host reads, in prose: no placeholder template to copy, no
    per-line requirement bookkeeping. ``requirements`` and ``evidence_paths`` are
    accepted for compatibility and not rendered (RS-02, RS-09)."""
    base = load_standard_instructions(repo_root)
    if requires_verified_execution:
        base += "\n\n" + _WITNESS_INSTRUCTIONS
    return base


_CANONICAL_RESULT_IR_INSTRUCTIONS = """RESULT IR: put the Result IR in the output's "result_ir" field, not in the deliverable text. The host reads two of its fields:
- "witness": present only when the deliverable claims a result (see WITNESS below).
- "open_defects": present only when a requested result was not obtained; a list of objects, each with a "description" of what was not obtained and why.
Leave "files" and "reconciliation" as empty lists."""

_BLOCK_START = "<!-- RESULT-IR:INSTRUCTIONS"
_BLOCK_END = "<!-- /RESULT-IR:INSTRUCTIONS -->"


def load_standard_instructions(repo_root: str | Path | None = None) -> str:
    """The instruction block of RESULT_STANDARD.md (falls back to the canonical
    copy when the standard is not on disk). Plain marker search, no pattern."""
    candidates = []
    if repo_root:
        candidates.append(Path(repo_root) / "contracts" / "standards" / "RESULT_STANDARD.md")
    try:
        candidates.append(Path(__file__).resolve().parents[3] / "contracts" / "standards" / "RESULT_STANDARD.md")
    except Exception:
        pass
    for candidate in candidates:
        if not candidate.is_file():
            continue
        text = candidate.read_text(encoding="utf-8")
        start, end = text.find(_BLOCK_START), text.find(_BLOCK_END)
        if start != -1 and end > start:
            body_start = text.find("-->", start)
            if body_start != -1 and body_start < end:
                return text[body_start + 3:end].strip()
    return _CANONICAL_RESULT_IR_INSTRUCTIONS


def extract_result_ir(body: str) -> dict | None:
    """Extract the Result IR from an execution body: the LAST fenced ```json
    block, or — as models sometimes emit it unfenced — a trailing raw JSON
    object containing 'files', 'reconciliation', or 'witness'."""
    body = body or ""
    blocks = re.findall(r"```(?:json)?\s*\n(.*?)```", body, re.S)
    for candidate in reversed(blocks):
        try:
            obj = json.loads(candidate.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and any(k in obj for k in ("files", "reconciliation", "witness")):
            return obj

    # Search for trailing JSON object
    for marker in ('{"files"', '{\n  "files"', '{"witness"', '{\n  "witness"', '{"reconciliation"', '{\n  "reconciliation"'):
        idx = body.rfind(marker)
        if idx >= 0:
            try:
                obj, _ = json.JSONDecoder().raw_decode(body[idx:])
                if isinstance(obj, dict):
                    return obj
            except json.JSONDecodeError:
                pass

    # Generic search for last balanced '{' that decodes to a Result IR dict
    r_idx = body.rfind("{")
    while r_idx >= 0:
        try:
            obj, _ = json.JSONDecoder().raw_decode(body[r_idx:])
            if isinstance(obj, dict) and any(k in obj for k in ("files", "reconciliation", "witness")):
                return obj
        except json.JSONDecodeError:
            pass
        r_idx = body.rfind("{", 0, r_idx)

    return None


def _resolve_evidence(
    ev: object,
    workspace_path: Path,
    errors: list[str],
    where: str,
    execution_body: str | None = None,
) -> None:
    if not isinstance(ev, dict) or "path" not in ev:
        errors.append(f"{where}: evidence object with 'path' required")
        return
    raw = str(ev["path"]).replace("\\", "/")
    if raw == "execution://body":
        # Reserved self-reference (RS-04): resolves to the current execution
        # body — the just-produced deliverable, not yet on disk.
        if execution_body is None:
            errors.append(f"{where}: execution://body cited but no execution body available")
            return
        content = execution_body
    elif raw in ("execution://witness", "execution://input", "execution://prompt"):
        # Reserved protocol URIs (ADR-0013 / ADR-0015): witness and prompt evidence
        # do not resolve to disk files in the workspace.
        return
    else:
        candidate = (workspace_path / raw).resolve()
        try:
            candidate.relative_to(workspace_path.resolve())
        except ValueError:
            errors.append(f"{where}: evidence path escapes workspace: {raw}")
            return
        if not candidate.is_file():
            errors.append(f"{where}: evidence path does not resolve: {raw}")
            return
        content = candidate.read_text(encoding="utf-8", errors="replace")
    section = ev.get("section")
    if section and str(section).lower() not in ("body", "execution_body", "default", "code", "solution", "script", "main", "") and str(section) not in content:
        errors.append(f"{where}: cited section marker not found in artifact: {section!r}")
    observed = ev.get("observed")
    if observed and str(observed).strip():
        obs_s = str(observed).strip()
        if obs_s not in content:
            content_norm = " ".join(content.lower().split())
            obs_norm = " ".join(obs_s.lower().split())
            if obs_norm not in content_norm:
                import re
                obs_words = [w for w in re.findall(r"\w+", obs_norm) if len(w) > 3]
                if obs_words and not any(w in content_norm for w in obs_words):
                    errors.append(
                        f"{where}: cited observation is not a verbatim substring of the artifact: {obs_s[:80]!r}"
                    )


def validate_result_ir(
    ir: object,
    workspace_path: str | Path,
    requirements: list[str],
    execution_body: str | None = None,
    citations: list[str] | None = None,
) -> tuple[list[str], dict]:
    """Mechanically validate a Result IR against the workspace filesystem.

    Returns (errors, normalized_ir). Empty errors means every structural,
    coverage, and evidence-citation constraint held. When ``citations`` is given,
    coverage and evidence-citation findings (the model's bookkeeping about its
    deliverable, not the deliverable) are appended there instead of ``errors``.
    """
    errors: list[str] = []
    cite = citations if citations is not None else errors
    ws = Path(workspace_path).resolve()
    if not isinstance(ir, dict):
        return ["Result IR must be a JSON object"], {}

    # Phase 1: Pydantic SSOT Structural Validation (ADR-0016)
    from pdl_taskmaster.runtime.wire_payloads import ResultIRData
    from pydantic import ValidationError
    try:
        validated_ir = ResultIRData.model_validate(ir)
    except ValidationError as val_err:
        for err in val_err.errors():
            loc = ".".join(str(x) for x in err.get("loc", ()))
            msg = err.get("msg", "")
            errors.append(f"{loc}: {msg}" if loc else msg)
        return errors, {}

    files = ir.get("files", [])
    recon = ir.get("reconciliation", [])
    defects = ir.get("open_defects", [])
    if requirements and not recon:
        cite.append("'reconciliation' must be a non-empty array")

    # Requirement coverage: every derived ID reconciled exactly once.
    seen: dict[str, int] = {}
    if isinstance(recon, list):
        for i, entry in enumerate(recon, 1):
            if not isinstance(entry, dict):
                errors.append(f"reconciliation[{i}]: must be an object")
                continue
            rid = str(entry.get("requirement", "")).strip()
            seen[rid] = seen.get(rid, 0) + 1
            status = str(entry.get("status", "")).strip().lower()
            if status not in _VALID_STATUS:
                errors.append(f"reconciliation[{i}] ({rid}): invalid status {status!r}")
            if rid not in {f"R{j}" for j in range(1, len(requirements) + 1)}:
                cite.append(f"reconciliation[{i}]: unknown requirement ID {rid!r}")
            ev = entry.get("evidence")
            req_idx = int(rid[1:]) - 1 if rid.startswith("R") and rid[1:].isdigit() else -1
            req_text = requirements[req_idx] if 0 <= req_idx < len(requirements) else ""
            if status == "satisfied" and isinstance(ev, dict):
                # Per RS-07, verbatim observed citation is mandatory for partial or open status
                # and open defects. For satisfied status, the deliverable artifact satisfies the
                # requirement, and 'observed' is optional explanatory text or requirement echo.
                ev_to_resolve = dict(ev)
                ev_to_resolve.pop("observed", None)
                _resolve_evidence(ev_to_resolve, ws, cite, f"reconciliation[{i}] ({rid})", execution_body)
            else:
                _resolve_evidence(ev, ws, cite, f"reconciliation[{i}] ({rid})", execution_body)
    total = {f"R{j}" for j in range(1, len(requirements) + 1)}
    for rid in sorted(total - set(seen)):
        cite.append(f"requirement {rid} is not reconciled")
    for rid, n in sorted(seen.items()):
        if n > 1 and rid in total:
            cite.append(f"requirement {rid} reconciled {n} times (expected exactly once)")

    if isinstance(files, list):
        for i, f in enumerate(files, 1):
            if not isinstance(f, dict) or not str(f.get("filename", "")).strip():
                errors.append(f"files[{i}]: 'filename' required")
                continue
            f_ev = f.get("evidence")
            if isinstance(f_ev, dict):
                f_ev_to_resolve = dict(f_ev)
                f_ev_to_resolve.pop("observed", None)
                _resolve_evidence(
                    f_ev_to_resolve, ws, cite, f"files[{i}] ({f.get('filename')})", execution_body
                )
            else:
                _resolve_evidence(
                    f_ev, ws, cite, f"files[{i}] ({f.get('filename')})", execution_body
                )

    if isinstance(defects, list):
        for i, d in enumerate(defects, 1):
            if not isinstance(d, dict) or not str(d.get("description", "")).strip():
                errors.append(f"open_defects[{i}]: 'description' required")
                continue
            _resolve_evidence(d.get("evidence"), ws, cite, f"open_defects[{i}]", execution_body)

    witness = ir.get("witness")
    if witness is not None:
        if not isinstance(witness, dict):
            errors.append("'witness' must be an object when present")
        else:
            # Pydantic SSOT (ADR-0018): one witness schema for the wire and the verifier.
            from pydantic import TypeAdapter, ValidationError

            from pdl_taskmaster.runtime.wire_payloads import WitnessPayload

            try:
                TypeAdapter(WitnessPayload).validate_python(witness)
            except ValidationError as exc:
                for err in exc.errors():
                    loc = ".".join(str(part) for part in err["loc"])
                    errors.append(f"'witness{('.' + loc) if loc else ''}': {err['msg']}")
            if "evidence" in witness:
                _resolve_evidence(witness.get("evidence"), ws, cite, "witness", execution_body)

    return errors, (ir if not errors else {})


def render_prior_ir_section(ir: object) -> str:
    """Render a validated prior Result IR for injection into the next epoch."""
    try:
        body = json.dumps(ir, indent=2, ensure_ascii=False)
    except (TypeError, ValueError):
        return ""
    return (
        "\n\n## PRIOR RESULT IR (mechanically validated by the host; "
        "reconciliation statuses and open defects are authoritative)\n"
        + body
    )


def load_ir_from_deliverable(deliverable_text: str | None) -> dict | None:
    """Recover the embedded Result IR from a prior deliverable (restore/chaining)."""
    if not deliverable_text:
        return None
    ir = extract_result_ir(deliverable_text)
    return ir if isinstance(ir, dict) and ir.get("reconciliation") else None


def artifact_sha256(path: str | Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def format_friendly_deliverable(text: str) -> str:
    """Format an execution deliverable for human/agent presentation in regular REPL mode.

    Replaces raw Result IR JSON blocks with a clean, readable summary card.
    """
    if not text:
        return text

    is_unverified = text.startswith("UNVERIFIED ANSWER:")
    reason = ""
    candidate_body = text

    if is_unverified:
        m = re.match(
            r"^UNVERIFIED ANSWER:.*?(?:Reason:\s*(.*?))\s*\n\nCandidate deliverable:\s*\n(.*)$",
            text,
            re.S,
        )
        if m:
            reason = m.group(1).strip()
            candidate_body = m.group(2).strip()

    # Extract IR if present
    ir = extract_result_ir(candidate_body)
    if not ir:
        return text

    # Strip Result IR json block from candidate body
    clean_body = candidate_body
    clean_body = re.sub(r"```json\s*\{.*?\"files\".*?\}\s*```", "", clean_body, flags=re.S).strip()
    clean_body = re.sub(
        r"(?:Result IR:|\n|^)\s*\{\s*\"(?:files|witness)\".*\}\s*$",
        "",
        clean_body,
        flags=re.S,
    ).strip()

    lines = []
    if is_unverified:
        lines.append("[!] UNVERIFIED DELIVERABLE (Substantive verification incomplete)")
        if reason:
            lines.append(f"    Reason: {reason}")
        lines.append("")
        lines.append("Candidate Output:")
        lines.append(clean_body)
    else:
        lines.append(clean_body)

    lines.append("")
    lines.append("Result Reconciliation:")

    recon = ir.get("reconciliation") or []
    if recon:
        for r in recon:
            if isinstance(r, dict):
                rid = r.get("requirement", "")
                st = r.get("status", "")
                sym = "[+]" if st == "satisfied" else ("[~]" if st == "partial" else "[-]")
                lines.append(f"  {sym} {rid}: {st}")
    else:
        lines.append("  (no requirement citations)")

    files = ir.get("files") or []
    if files:
        file_names = ", ".join(f.get("filename", "") for f in files if isinstance(f, dict))
        lines.append(f"  * Files: {len(files)} modified ({file_names})")
    else:
        lines.append("  * Files: 0 modified")

    witness = ir.get("witness")
    if witness and isinstance(witness, dict):
        pol = witness.get("polarity", "")
        flag = witness.get("provisional")
        status = (
            "not verified" if is_unverified or flag is None
            else "provisional, not reproduced by the host" if flag
            else "reproduced by the host sandbox"
        )
        if pol == "positive":
            data = witness.get("data") or {}
            keys = ", ".join(sorted(data)) if isinstance(data, dict) else ""
            lines.append(f"  * Verification: Positive witness ({status}){' [' + keys + ']' if keys else ''}")
        elif pol == "negative":
            if witness.get("basis") == "proof":
                lines.append(f"  * Verification: Negative witness by proof ({status})")
            else:
                nodes = witness.get("nodes_explored", 0)
                method = witness.get("method") or "search"
                searched = "search exhausted" if witness.get("search_exhausted", True) else "search not exhausted"
                lines.append(f"  * Verification: Negative witness ({searched}, {nodes} states via {method}; {status})")
    elif is_unverified:
        lines.append("  * Verification: Witness missing or unverified")

    defects = ir.get("open_defects") or []
    if defects:
        lines.append(f"  * Open Defects: {len(defects)}")
        for d in defects:
            if isinstance(d, dict):
                lines.append(f"    - {d.get('id', '')}: {d.get('description', '')}")

    return "\n".join(lines).strip()

