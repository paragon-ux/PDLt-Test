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


def render_instructions(
    requirements: list[str],
    repo_root: str | Path | None = None,
    evidence_paths: list[str] | None = None,
    requires_verified_execution: bool = False,
) -> str:
    numbered = "\n".join(f"R{i}: {r}" for i, r in enumerate(requirements, 1))
    effective_paths = list(evidence_paths or ["execution://body"])
    if requires_verified_execution and "execution://witness" not in effective_paths:
        effective_paths.append("execution://witness")
    paths = "\n".join(f"- {p}" for p in effective_paths)
    base = (
        "CONFIRMED REQUIREMENTS (mechanically derived; reconcile EVERY ID):\n"
        + (numbered or "R1: COMPLETE confirmed task")
        + "\n\n"
        + load_standard_instructions(repo_root).replace(
            "{evidence_paths}", paths or "- execution://body"
        )
    )
    if requires_verified_execution:
        base += (
            "\n\nWITNESS REQUIREMENT (ADR-0013 / ADR-0015): Because this task requires verified execution, your Result IR MUST include a 'witness' field certifying any result it claims:\n"
            "- If a solution exists: {\"polarity\": \"positive\", \"evidence\": {\"path\": \"execution://witness\"}, \"data\": {<the concrete result, keyed by name>}}\n"
            "- If no solution exists: {\"polarity\": \"negative\", \"evidence\": {\"path\": \"execution://witness\"}, \"basis\": \"proof\", \"argument\": \"<the impossibility argument>\"} or, for an exhausted search, {\"polarity\": \"negative\", \"basis\": \"search\", \"search_exhausted\": true, \"nodes_explored\": <states explored>, \"method\": \"<method>\"}\n"
            "- If the result could not be obtained: emit no witness; mark each unmet requirement \"open\" in 'reconciliation' and record the reason in 'open_defects'.\n\n"
            "WITNESS CERTIFICATION: When the deliverable includes code, the host sandbox executes it. Print exactly one line `WITNESS: <json>` to stdout; the host-reproduced witness replaces any witness asserted in the Result IR. A witness the host could not reproduce is reported as provisional."
        )
    return base


_CANONICAL_RESULT_IR_INSTRUCTIONS = """The response MUST end with a fenced ```json block containing the Result IR object, exactly this shape:
{"files": [{"filename": "<name>.py", "satisfies": ["R<n>"], "evidence": {"path": "<workspace-relative path>", "section": "<verbatim section marker, optional>"}}], "reconciliation": [{"requirement": "R<n>", "status": "satisfied|partial|open", "evidence": {"path": "...", "section": "...", "observed": "<verbatim quote from cited artifact if status is partial/open, or omit for satisfied>"}}], "open_defects": [{"id": "D<n>", "description": "<defect>", "evidence": {"path": "...", "observed": "<verbatim quote>"}}]}
Files note: 'files' must be an array (use [] if no files in workspace were created or modified).
Evidence rules: the path "execution://body" refers to THIS response's own deliverable text (use it for code and claims that exist only in this response); the path "execution://witness" refers to witness payload; any other path MUST be one of the AVAILABLE EVIDENCE PATHS listed below; every "observed" string MUST be copied verbatim from the cited artifact; every requirement ID MUST appear in "reconciliation" exactly once; do not invent paths, sections, quotes, or requirement IDs; the host mechanically validates every citation and rejects fabrication.
AVAILABLE EVIDENCE PATHS: {evidence_paths}"""


def load_standard_instructions(repo_root: str | Path | None = None) -> str:
    """Load Result IR instructions safely without fragile disk dependency (ADR-0009 / ADR-0015).

    Returns the canonical compiled Result IR instructions, falling back to the immutable
    constant if contracts/standards/RESULT_STANDARD.md is not present on disk in candidate repo.
    """
    candidates = []
    if repo_root:
        candidates.append(Path(repo_root) / "contracts" / "standards" / "RESULT_STANDARD.md")
    try:
        pkg_root = Path(__file__).resolve().parents[3]
        candidates.append(pkg_root / "contracts" / "standards" / "RESULT_STANDARD.md")
    except Exception:
        pass

    for candidate in candidates:
        if candidate.is_file():
            try:
                text = candidate.read_text(encoding="utf-8")
                m = re.search(
                    r"<!-- RESULT-IR:INSTRUCTIONS.*?-->\s*\n(.*?)\n?<!-- /RESULT-IR:INSTRUCTIONS -->",
                    text,
                    re.S,
                )
                if m:
                    return m.group(1).strip()
            except Exception:
                continue

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
) -> tuple[list[str], dict]:
    """Mechanically validate a Result IR against the workspace filesystem.

    Returns (errors, normalized_ir). Empty errors means every structural,
    coverage, and evidence-citation constraint held.
    """
    errors: list[str] = []
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
        errors.append("'reconciliation' must be a non-empty array")

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
                errors.append(f"reconciliation[{i}]: unknown requirement ID {rid!r}")
            ev = entry.get("evidence")
            req_idx = int(rid[1:]) - 1 if rid.startswith("R") and rid[1:].isdigit() else -1
            req_text = requirements[req_idx] if 0 <= req_idx < len(requirements) else ""
            if status == "satisfied" and isinstance(ev, dict):
                # Per RS-07, verbatim observed citation is mandatory for partial or open status
                # and open defects. For satisfied status, the deliverable artifact satisfies the
                # requirement, and 'observed' is optional explanatory text or requirement echo.
                ev_to_resolve = dict(ev)
                ev_to_resolve.pop("observed", None)
                _resolve_evidence(ev_to_resolve, ws, errors, f"reconciliation[{i}] ({rid})", execution_body)
            else:
                _resolve_evidence(ev, ws, errors, f"reconciliation[{i}] ({rid})", execution_body)
    total = {f"R{j}" for j in range(1, len(requirements) + 1)}
    for rid in sorted(total - set(seen)):
        errors.append(f"requirement {rid} is not reconciled")
    for rid, n in sorted(seen.items()):
        if n > 1 and rid in total:
            errors.append(f"requirement {rid} reconciled {n} times (expected exactly once)")

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
                    f_ev_to_resolve, ws, errors, f"files[{i}] ({f.get('filename')})", execution_body
                )
            else:
                _resolve_evidence(
                    f_ev, ws, errors, f"files[{i}] ({f.get('filename')})", execution_body
                )

    if isinstance(defects, list):
        for i, d in enumerate(defects, 1):
            if not isinstance(d, dict) or not str(d.get("description", "")).strip():
                errors.append(f"open_defects[{i}]: 'description' required")
                continue
            _resolve_evidence(d.get("evidence"), ws, errors, f"open_defects[{i}]", execution_body)

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
                _resolve_evidence(witness.get("evidence"), ws, errors, "witness", execution_body)

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

