from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import sys
import tempfile

from pdl_taskmaster.providers.recorded import RecordedFixtureBuilder, RecordedWorker, request_sha256

# The provider settings replay keys are built with (TARGET_ARCHITECTURE I-10). They are
# fixed here and stored in the fixture, never read from the environment, so a key is a
# function of the code alone: the operation guidance, the effort mapping, the output
# format and the input the engine renders.
REPLAY_REQUEST_SETTINGS: dict[str, Any] = {
    "model": "openai/gpt-oss-120b",
    "provider_pinning": {"order": ["Baseten", "Crusoe"], "allow_fallbacks": True},
    "max_output_tokens": 16384,
}


def replay_request_builder(repo_root: str | Path, settings: dict[str, Any] | None = None):
    """The request body the live API worker would send for a request, built offline
    (no network, no credentials) with the fixture's settings."""
    from pdl_taskmaster.providers.api_worker import ApiWorker

    resolved = {**REPLAY_REQUEST_SETTINGS, **(settings or {})}
    worker = ApiWorker(
        model=resolved["model"],
        repo_root=repo_root,
        provider_pinning=resolved["provider_pinning"],
        max_output_tokens=resolved["max_output_tokens"],
    )
    return lambda request: worker.build_request_body(request)[0]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_candidate(candidate_repo: str | Path) -> str:
    repo = str(Path(candidate_repo).resolve())
    if repo not in sys.path:
        sys.path.insert(0, repo)
    return repo


def _ordered_recorded_calls(workspaces: list[Path]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for workspace in workspaces:
        workspace_calls: list[dict[str, Any]] = []
        response_paths = list(workspace.glob("stages/*/output/*/model-response.txt")) + list(
            workspace.glob("turns/*/stages/*/output/*/model-response.txt")
        )
        for response_path in response_paths:
            projection_path = response_path.parent / "compiled-projection.json"
            if not projection_path.is_file():
                continue
            projection = json.loads(projection_path.read_text(encoding="utf-8"))
            workspace_calls.append(
                {
                    "operation": projection.get("operation", "UNKNOWN"),
                    "response": response_path.read_text(encoding="utf-8"),
                    "invocation_id": response_path.parent.name,
                }
            )
        workspace_calls.sort(key=lambda item: item["invocation_id"])
        calls.extend(workspace_calls)
    return calls


def _resolve_workspaces(eval_root: Path, row: dict[str, Any]) -> list[Path]:
    base = eval_root / "evidence" / "round4" / "workspaces" / row["run_id"] / row["case_id"]
    candidates = sorted(base.glob("W-*")) if base.is_dir() else []
    if not candidates:
        raise SystemExit(f"cannot resolve workspaces for case {row.get('case_id')} run {row.get('run_id')}")

    def _created_at(workspace: Path) -> str:
        meta_path = workspace / "workspace.json"
        if meta_path.is_file():
            value = json.loads(meta_path.read_text(encoding="utf-8")).get("created_at_utc")
            if isinstance(value, str):
                return value
        return workspace.name

    return sorted(candidates, key=_created_at)


def build_recorded_fixture(
    candidate_repo: str | Path,
    eval_root: str | Path,
    evidence_jsonl: str | Path,
    *,
    case_ids: list[str] | None = None,
    run_id: str | None = None,
) -> RecordedWorker:
    repo = _load_candidate(candidate_repo)
    eval_root = Path(eval_root).resolve()
    rows = _load_jsonl(Path(evidence_jsonl).resolve())
    if run_id is not None:
        rows = [row for row in rows if row.get("run_id") == run_id]
    if case_ids:
        wanted = set(case_ids)
        rows = [row for row in rows if row.get("case_id") in wanted]
    if not rows:
        raise SystemExit("no evidence rows selected for fixture")

    from pdl_taskmaster.runtime.session_engine import SessionEngine

    request_body = replay_request_builder(repo)
    builder = RecordedFixtureBuilder(request_body)
    for row in rows:
        workspaces = _resolve_workspaces(eval_root, row)
        recorded_calls = _ordered_recorded_calls(workspaces)
        call_index = 0

        def model_call(request: Any, _recorded=recorded_calls) -> str:
            nonlocal call_index
            if call_index >= len(_recorded):
                raise SystemExit(
                    f"fixture replay exhausted for case {row.get('case_id')} "
                    f"at operation {request.operation}"
                )
            recorded = _recorded[call_index]
            call_index += 1
            if recorded["operation"] != request.operation:
                raise SystemExit(
                    f"fixture replay order mismatch: expected {recorded['operation']} "
                    f"got {request.operation} for case {row.get('case_id')}"
                )
            builder.add(
                request.operation,
                request_sha256(request_body(request)),
                recorded["response"],
                metadata={"source": f"{row['case_id']}:{recorded['invocation_id']}"},
                prompt_text=request.prompt,
            )
            return recorded["response"]

        with tempfile.TemporaryDirectory(prefix="pdl-r2s-fixture-", ignore_cleanup_errors=True) as tmp:
            engine = SessionEngine(
                repo,
                model_call,
                higher_priority_constraints="Obey applicable provider/platform safety, privacy, permission, and tool constraints.",
                available_execution_tools=None,
                workspace_root=tmp,
            )
            for turn in row.get("turns", []):
                engine.handle_user_message(turn.get("user", ""))
    return builder.build()

def build_recorded_fixture_from_vendored(
    candidate_repo: str | Path,
    fixture_file: str | Path,
    *,
    case_ids: list[str] | None = None,
) -> RecordedWorker:
    """Build a recorded worker from the vendored standalone fixture.

    Extraction adaptation: the qualified REPL recorded path previously read
    recorded workspaces from an external evaluation repository. The standalone
    harness vendors the exact recorded calls (operation, prompt hash, response)
    so the published harness does not depend on that repository.

    Each entry is keyed by the complete provider request recorded with it
    (``provider_request``, built with the fixture's ``request_settings``), so a change
    to anything a model receives is a replay miss (TARGET_ARCHITECTURE I-10). An entry
    without a recorded request (one the scripted turns never reach) cannot be matched
    and is left out.

    The sandbox declares the host's own interpreter version in EXECUTE prompts, so a
    fixture recorded under another version (``recorded_python``) is replayed against
    the request this host sends: the sandbox's interpreter declaration in the recorded
    request is swapped for this host's, and the entry is keyed by that request.
    Every other byte of the request must still match.
    """
    from pdl_taskmaster.verification.sandbox import PYTHON_VERSION, python_declaration

    _load_candidate(candidate_repo)
    value = json.loads(Path(fixture_file).read_text(encoding="utf-8"))
    entries = value.get("entries") or []
    if case_ids:
        wanted = set(case_ids)
        entries = [e for e in entries if (e.get("source") or "").split(":")[0] in wanted]
    if not entries:
        raise SystemExit("no vendored fixture entries selected")
    recorded_python = value.get("recorded_python")
    builder = RecordedFixtureBuilder(replay_request_builder(candidate_repo, value.get("request_settings")))
    for entry in entries:
        body = entry.get("provider_request")
        if body is None or request_sha256(body) != entry.get("request_sha256"):
            continue  # not reached by the recorded turns, or not keyed by its request
        metadata = {"source": entry.get("source", "vendored")}
        if recorded_python and recorded_python != PYTHON_VERSION:
            recorded, host = python_declaration(recorded_python), python_declaration()
            if any(isinstance(body.get(k), str) and recorded in body[k] for k in ("input", "instructions")):
                body = {k: (v.replace(recorded, host) if k in ("input", "instructions") and isinstance(v, str) else v)
                        for k, v in body.items()}
                metadata["recorded_python"] = recorded_python
        builder.add(
            entry["operation"],
            request_sha256(body),
            entry["response"],
            metadata=metadata,
            prompt_text=entry.get("prompt_text"),
        )
    return builder.build()
