"""Render every reachable recorded model request offline: no model, no network.

Three corpora, all deterministic:

* fixture: each case in ``tests/fixtures/recorded-cases.json`` is replayed through
  ``SessionEngine`` with its recorded responses, in order, and every request the
  engine sends is captured (operation and prompt);
* bootstrap: the first request (``BOOTSTRAP_ANALYSIS``) is rendered for every prompt
  in ``prompts/CATALOGUE_MANIFEST.jsonl``;
* brief (``--draft-execute`` only): two scripted sessions, confirmed and unconfirmed,
  with ``DRAFT_EXECUTE`` on and System 1 labelling the task VERIFIED_EXECUTION; fixed
  replies, so every request they send renders the same on every run.

This is evaluation-plane tooling (it reads the catalogue); the harness never imports it.

usage:
  python scripts/render_recorded_prompts.py render OUT.json [--draft-execute]
  python scripts/render_recorded_prompts.py compare BASE.json NEW.json
  python scripts/render_recorded_prompts.py rekey OUT_FIXTURE.json

``rekey`` rewrites the fixture's keys for the current code (``prompt_text``,
``prompt_sha256``, and the replay key: the complete ``provider_request`` and its
``request_sha256``) and refuses to change any recorded response.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdl_taskmaster.providers.fixtures import REPLAY_REQUEST_SETTINGS, replay_request_builder  # noqa: E402
from pdl_taskmaster.providers.recorded import request_sha256  # noqa: E402
from pdl_taskmaster.runtime.session_engine import SessionEngine  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "recorded-cases.json"
MANIFEST = ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl"
# The constraint text the recorded fixture was keyed with (providers/fixtures.py).
FIXTURE_CONSTRAINTS = "Obey applicable provider/platform safety, privacy, permission, and tool constraints."


class _Stop(Exception):
    """Raised by the capture stub once it has the request it needs."""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_BODY = None


def _request_record(request) -> dict:
    """The prompt the engine rendered and the complete provider request a live worker
    would send for it (fixed replay settings; no network)."""
    global _BODY
    if _BODY is None:
        _BODY = replay_request_builder(ROOT, json.loads(FIXTURE.read_text(encoding="utf-8")).get("request_settings"))
    body = _BODY(request)
    return {"operation": request.operation, "prompt_sha256": _sha(request.prompt), "prompt_text": request.prompt,
            "request_sha256": request_sha256(body), "provider_request": body}


def _engine(model_call, workspace: str) -> SessionEngine:
    return SessionEngine(
        str(ROOT),
        model_call,
        higher_priority_constraints=FIXTURE_CONSTRAINTS,
        available_execution_tools=None,
        workspace_root=workspace,
    )


def render_fixture() -> tuple[list[dict], list[str]]:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rendered: list[dict] = []
    unreached: list[str] = []
    for case, turns in fixture["case_turns"].items():
        recorded = [e for e in fixture["entries"] if e["source"].split(":")[0] == case]
        position = 0

        def model_call(request, _recorded=recorded):
            nonlocal position
            entry = _recorded[position]
            position += 1
            if entry["operation"] != request.operation:
                raise RuntimeError(f"{case}: expected {entry['operation']}, engine sent {request.operation}")
            rendered.append({"source": entry["source"], **_request_record(request)})
            return entry["response"]

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            engine = _engine(model_call, tmp)
            for turn in turns:
                engine.handle_user_message(turn)
        unreached += [e["source"] for e in recorded[position:]]
    return rendered, unreached


def render_bootstrap() -> list[dict]:
    rendered: list[dict] = []
    for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        item = json.loads(line)
        text = (ROOT / "prompts" / item["file"]).read_text(encoding="utf-8-sig")
        captured: list[dict] = []

        def model_call(request, _captured=captured):
            _captured.append(_request_record(request))
            raise _Stop

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            try:
                _engine(model_call, tmp).handle_user_message(text)
            except _Stop:
                pass
            except Exception:  # the engine may wrap the stop; the capture is what matters
                pass
        rendered.append({"id": item["id"], **(captured[0] if captured else {"operation": None})})
    return rendered


class _VerifiedSys1:
    """System 1 stand-in for the brief corpus: routes through Phase 0 and labels the
    task VERIFIED_EXECUTION, the only class for which DRAFT_EXECUTE runs."""

    is_configured = True
    model = "render-sys1"

    def call(self, request):
        name = next(iter(request.questions))
        choice, other = ("APPLY_PROTOCOL", "BYPASS") if name == "route" else ("VERIFIED_EXECUTION", "STANDARD_EXECUTION")
        return {"answers": {name: {"choice": choice, "confidence": 0.97,
                                   "probabilities": {choice: 0.97, other: 0.03}}}}, 1.0


_BRIEF_PROGRAM = "import json\nprint('WITNESS: ' + json.dumps({'polarity': 'positive', 'data': {'answer': 12}}))"
_BRIEF_REPLIES = {
    "BOOTSTRAP_ANALYSIS": {"kind": "ANALYSIS", "task_summary": "Compute the stated value.", "approach_notes": "",
                           "risk_notes": "", "task_entities": []},
    "DRAFT_PROMPT": {"kind": "PROMPT", "prompt_body": "COMPUTE the stated value\nRETURN the value",
                     "approach_handoff": "NONE"},
    "DRAFT_PLAN": {"neutral_plan_body": "DERIVE the value\nEMIT the value"},
    "DRAFT_EXECUTE": {"kind": "RESULT", "brief_body": "Sum the three values; one pass.", "execution_entities": []},
    "EXECUTE": {"kind": "RESULT", "body": _BRIEF_PROGRAM, "result_ir": {}},
    "EXECUTE_UNCONFIRMED": {"kind": "RESULT", "interpretation": "COMPUTE the stated value",
                            "approach": "SUM the values", "body": _BRIEF_PROGRAM, "result_ir": {}},
}
_BRIEF_SESSIONS = {
    "confirmed": ({}, ("$confirm-with-pseudocode Compute the sum of 3, 4 and 5.", "/confirm", "/confirm")),
    "unconfirmed": ({"no_review": True}, ("Compute the sum of 3, 4 and 5.",)),
}


def render_brief() -> list[dict]:
    rendered: list[dict] = []
    for name, (options, turns) in _BRIEF_SESSIONS.items():
        count = 0

        def model_call(request, _name=name):
            nonlocal count
            count += 1
            rendered.append({"source": f"{_name}:{count:04d}-{request.operation.lower()}", **_request_record(request)})
            return json.dumps(_BRIEF_REPLIES[request.operation])

        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            engine = SessionEngine(str(ROOT), model_call, higher_priority_constraints=FIXTURE_CONSTRAINTS,
                                   available_execution_tools=None, workspace_root=tmp,
                                   sys1_client=_VerifiedSys1(), **options)
            engine.draft_execute = True
            for turn in turns:
                engine.handle_user_message(turn)
    return rendered


def render(out: Path, draft_execute: bool = False) -> None:
    fixture, unreached = render_fixture()
    data = {"fixture": fixture, "fixture_unreached": unreached, "bootstrap": render_bootstrap()}
    if draft_execute:
        data["brief"] = render_brief()
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"fixture requests: {len(fixture)} (unreached recorded entries: {len(unreached)}); "
          f"bootstrap requests: {len(data['bootstrap'])}"
          + (f"; brief requests: {len(data['brief'])}" if draft_execute else "") + f" -> {out}")


def compare(base_path: Path, new_path: Path) -> int:
    base = json.loads(base_path.read_text(encoding="utf-8"))
    new = json.loads(new_path.read_text(encoding="utf-8"))
    changed = 0
    for corpus, key in (("fixture", "source"), ("bootstrap", "id"), ("brief", "source")):
        if corpus not in base or corpus not in new:
            continue
        old_by = {r[key]: r for r in base[corpus]}
        new_by = {r[key]: r for r in new[corpus]}
        for name in sorted(set(old_by) | set(new_by)):
            a, b = old_by.get(name), new_by.get(name)
            if a is None or b is None:
                print(f"{corpus}:{name}: {'added' if a is None else 'removed'}")
                changed += 1
                continue
            for field in ("operation", "prompt_sha256", "request_sha256"):
                if field in a and a.get(field) != b.get(field):
                    print(f"{corpus}:{name}: {field} differs")
                    changed += 1
    print(f"{changed} difference(s)")
    return 1 if changed else 0


def rekey(out: Path) -> None:
    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    rendered, unreached = render_fixture()
    by_source = {r["source"]: r for r in rendered}
    for entry in fixture["entries"]:
        new = by_source.get(entry["source"])
        if new is None:
            continue  # unreached by the scripted turns: left as recorded
        if new["operation"] != entry["operation"]:
            raise SystemExit(f"{entry['source']}: operation changed; refusing to re-key")
        entry["prompt_text"], entry["prompt_sha256"] = new["prompt_text"], new["prompt_sha256"]
        entry["provider_request"], entry["request_sha256"] = new["provider_request"], new["request_sha256"]
    fixture.setdefault("request_settings", dict(REPLAY_REQUEST_SETTINGS))
    original = {e["source"]: e["response"] for e in json.loads(FIXTURE.read_text(encoding="utf-8"))["entries"]}
    if any(original[e["source"]] != e["response"] for e in fixture["entries"]):
        raise SystemExit("a recorded response would change; refusing to write")
    # LF endings on every platform, like the committed fixture.
    out.write_bytes((json.dumps(fixture, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"re-keyed {len(rendered)} entries; unreached left as recorded: {unreached}")


if __name__ == "__main__":
    command, *args = sys.argv[1:] or ["help"]
    if command == "render":
        render(Path(args[0]), draft_execute="--draft-execute" in args[1:])
    elif command == "compare":
        sys.exit(compare(Path(args[0]), Path(args[1])))
    elif command == "rekey":
        rekey(Path(args[0]))
    else:
        print(__doc__)
