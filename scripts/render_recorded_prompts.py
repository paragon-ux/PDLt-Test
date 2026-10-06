"""Render every reachable recorded model request offline: no model, no network.

Two corpora, both deterministic:

* fixture: each case in ``tests/fixtures/recorded-cases.json`` is replayed through
  ``SessionEngine`` with its recorded responses, in order, and every request the
  engine sends is captured (operation and prompt);
* bootstrap: the first request (``BOOTSTRAP_ANALYSIS``) is rendered for every prompt
  in ``prompts/CATALOGUE_MANIFEST.jsonl``.

This is evaluation-plane tooling (it reads the catalogue); the harness never imports it.

usage:
  python scripts/render_recorded_prompts.py render OUT.json
  python scripts/render_recorded_prompts.py compare BASE.json NEW.json
  python scripts/render_recorded_prompts.py rekey OUT_FIXTURE.json

``rekey`` rewrites the fixture's keys (``prompt_text``, ``prompt_sha256``) for the
current code and refuses to change any recorded response.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from pdl_taskmaster.runtime.session_engine import SessionEngine  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "recorded-cases.json"
MANIFEST = ROOT / "prompts" / "CATALOGUE_MANIFEST.jsonl"
# The constraint text the recorded fixture was keyed with (providers/fixtures.py).
FIXTURE_CONSTRAINTS = "Obey applicable provider/platform safety, privacy, permission, and tool constraints."


class _Stop(Exception):
    """Raised by the capture stub once it has the request it needs."""


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _request_record(request) -> dict:
    record = {"operation": request.operation, "prompt_sha256": _sha(request.prompt), "prompt_text": request.prompt}
    body = getattr(request, "provider_request", None)
    if body is not None:
        text = json.dumps(body, sort_keys=True, ensure_ascii=False)
        record["provider_request_sha256"] = _sha(text)
        record["provider_request"] = body
    return record


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


def render(out: Path) -> None:
    fixture, unreached = render_fixture()
    data = {"fixture": fixture, "fixture_unreached": unreached, "bootstrap": render_bootstrap()}
    out.write_text(json.dumps(data, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"fixture requests: {len(fixture)} (unreached recorded entries: {len(unreached)}); "
          f"bootstrap requests: {len(data['bootstrap'])} -> {out}")


def compare(base_path: Path, new_path: Path) -> int:
    base = json.loads(base_path.read_text(encoding="utf-8"))
    new = json.loads(new_path.read_text(encoding="utf-8"))
    changed = 0
    for corpus, key in (("fixture", "source"), ("bootstrap", "id")):
        old_by = {r[key]: r for r in base[corpus]}
        new_by = {r[key]: r for r in new[corpus]}
        for name in sorted(set(old_by) | set(new_by)):
            a, b = old_by.get(name), new_by.get(name)
            if a is None or b is None:
                print(f"{corpus}:{name}: {'added' if a is None else 'removed'}")
                changed += 1
                continue
            for field in ("operation", "prompt_sha256", "provider_request_sha256"):
                if a.get(field) != b.get(field) and not (field == "provider_request_sha256" and field not in a):
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
    original = {e["source"]: e["response"] for e in json.loads(FIXTURE.read_text(encoding="utf-8"))["entries"]}
    if any(original[e["source"]] != e["response"] for e in fixture["entries"]):
        raise SystemExit("a recorded response would change; refusing to write")
    # LF endings on every platform, like the committed fixture.
    out.write_bytes((json.dumps(fixture, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
    print(f"re-keyed {len(rendered)} entries; unreached left as recorded: {unreached}")


if __name__ == "__main__":
    command, *args = sys.argv[1:] or ["help"]
    if command == "render":
        render(Path(args[0]))
    elif command == "compare":
        sys.exit(compare(Path(args[0]), Path(args[1])))
    elif command == "rekey":
        rekey(Path(args[0]))
    else:
        print(__doc__)
