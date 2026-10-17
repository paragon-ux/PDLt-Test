"""L124 D6: interface conformance. Interfaces are clients of Session, not extension points: each runs the same
scenarios and must agree on session handling, review commands, exit statuses (ADR-0019) and the provenance the MCP
server serves. Interfaces: the library Session, the interactive REPL, headless runs (--non-interactive), and the MCP
server's closed-session resources. Offline: a registered scripted worker provider and a scripted System 1."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from pdl_taskmaster import api
from pdl_taskmaster.extensions import providers
from pdl_taskmaster.extensions.conformance import ScriptedSys1, ScriptedWorker
from pdl_taskmaster.host import mcp_server, repl
from pdl_taskmaster.providers.base import WorkerResult

from extension_samples import IR, POSITIVE_SAMPLE

ROOT = Path(__file__).resolve().parents[1]
REQUEST = "Carry out the stated task."
TEXT = {"body": "The stated task is carried out."}
NEGATIVE = ("import json\nnodes = 0\nfor x in range(27):\n    nodes += 1\n"
            "print('WITNESS: ' + json.dumps({'polarity': 'negative', 'basis': 'search', "
            "'search_exhausted': True, 'nodes_explored': nodes, 'method': 'enumeration'}))")
CONFIRMED = [REQUEST, "/confirm", "/confirm"]

# name: (System 1's problem class, or "BYPASS"; review route; EXECUTE reply; lines; final stage; provenance level)
SCENARIOS = {
    "confirmed-success": ("STANDARD_EXECUTION", True, TEXT, CONFIRMED, "CLOSED_SUCCESS", "contract_checked"),
    "at-review": ("STANDARD_EXECUTION", True, TEXT, [REQUEST], "PROMPT_REVIEW", None),
    "cancelled": ("STANDARD_EXECUTION", True, TEXT, [REQUEST, "/cancel"], "CLOSED_CANCELLED", None),
    "host-verified": ("VERIFIED_EXECUTION", True, POSITIVE_SAMPLE, CONFIRMED, "CLOSED_SUCCESS", "host_verified"),
    "unverified": ("VERIFIED_EXECUTION", True, {"body": f"```python\n{NEGATIVE}\n```", "result_ir": IR}, CONFIRMED,
                   "CLOSED_UNVERIFIED", "unverified"),
    "unconfirmed": ("STANDARD_EXECUTION", False, TEXT, [REQUEST], "CLOSED_SUCCESS", "contract_checked"),
    "stray-confirm": ("STANDARD_EXECUTION", True, TEXT, ["/confirm"], None, None),
    "direct-reply": ("BYPASS", False, TEXT, ["What is PDLt?"], None, None),
}
DIRECT_REPLY = "PDLt runs tasks under a protocol."


class Bypassing(ScriptedSys1):
    def call(self, request):
        if next(iter(request.questions)) != "route":
            return super().call(request)
        self.requests.append(request.to_dict())
        return {"answers": {"route": {"choice": "BYPASS", "confidence": 0.97,
                                      "probabilities": {"BYPASS": 0.97, "APPLY_PROTOCOL": 0.03}}}}, 1.0


class Worker(ScriptedWorker):
    def call(self, request):
        if request.operation == "BYPASS_ORDINARY":
            self.requests.append((request.operation, request.prompt))
            return WorkerResult(json.dumps({"message": DIRECT_REPLY}))
        return super().call(request)


MADE: list[Worker] = []


def _worker(scenario: str) -> Worker:
    problem_class, _, execute, *_ = SCENARIOS[scenario]
    sys1 = Bypassing() if problem_class == "BYPASS" else ScriptedSys1({"problem_class": (problem_class, 0.97)})
    MADE.append(Worker(execute, sys1))
    return MADE[-1]


@pytest.fixture(autouse=True)
def provider():
    with providers.REGISTRY.scoped():
        providers.register_provider("conformance", lambda *, scenario: _worker(scenario), settings=["scenario"])
        MADE.clear()
        yield


# ---- the interfaces ---------------------------------------------------------------------------------------------

class Typed(io.StringIO):
    def isatty(self):
        return True


def run_session(name: str, sessions: Path, sid: str, lines: list[str]) -> dict:
    review = SCENARIOS[name][1]
    worker = api.create_worker("conformance", scenario=name)
    with api.Session.open(worker, sessions / sid, repo_root=ROOT, no_review=not review) as session:
        for line in lines:
            result = session.send(line)
    return {"exit_status": result.exit_status, "text": result.text}


def run_repl(name: str, sessions: Path, sid: str, lines: list[str], monkeypatch, *, headless: bool) -> dict:
    review = SCENARIOS[name][1]
    argv = ["pdlt", "--worker", "conformance", "--provider-setting", f"scenario={name}", "--session-id", sid,
            "--review" if review else "--no-review", "--candidate-repo", str(ROOT)]
    monkeypatch.setattr(repl, "_default_session_base", lambda: sessions)
    monkeypatch.setattr(sys, "argv", argv + (["--non-interactive"] if headless else []))
    stdin = "\n".join(lines) + "\n"
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin) if headless else Typed(stdin))
    code = repl.main()
    return {"exit_status": code if headless else None, "text": None}


def outcome(sessions: Path, sid: str) -> dict:
    """What the session folder holds, read back through the library: the stage, and the provenance of its turn
    closed with a result."""
    with api.Session.open(ScriptedWorker({}), sessions / sid, repo_root=ROOT) as session:
        state = session.status().get("controller_state")
    turns = [t for t in api.closed_turns(sessions) if t.session == sid]
    record = turns[-1].provenance() if turns else None
    return {"stage": state.get("stage") if state else None, "provenance": record}


INTERFACES = ["session", "interactive", "headless"]


def drive(interface: str, name: str, sessions: Path, sid: str, monkeypatch, lines=None) -> dict:
    lines = SCENARIOS[name][3] if lines is None else lines
    if interface == "session":
        ran = run_session(name, sessions, sid, lines)
    else:
        ran = run_repl(name, sessions, sid, lines, monkeypatch, headless=interface == "headless")
    return {**ran, **outcome(sessions, sid)}


# ---- the checks -------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("interface", INTERFACES)
@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_every_interface_ends_each_scenario_in_the_same_state(interface, name, tmp_path, monkeypatch, capsys):
    _, _, _, _, stage, level = SCENARIOS[name]
    got = drive(interface, name, tmp_path / "sessions", "s-1", monkeypatch)
    assert got["stage"] == stage
    assert ((got["provenance"] or {}).get("verification") or {}).get("level") == level
    if got["exit_status"] is not None:  # the session and headless runs report one; the interactive REPL does not
        assert got["exit_status"] == api.exit_status(stage)
    if name == "direct-reply":
        shown = got["text"] if interface == "session" else capsys.readouterr().out
        assert DIRECT_REPLY in shown
    if name == "stray-confirm":
        assert MADE[-1].requests == []  # a review command with no open review reaches no model


@pytest.mark.parametrize("name", ["host-verified", "unverified", "confirmed-success"])
def test_every_interface_records_the_same_provenance_and_the_mcp_server_serves_it(name, tmp_path, monkeypatch):
    sessions = tmp_path / "sessions"
    for interface in INTERFACES:
        drive(interface, name, sessions, interface, monkeypatch)
    turns = {t.session: t for t in api.closed_turns(sessions)}
    assert sorted(turns) == sorted(INTERFACES)
    stable = [{k: v for k, v in turns[i].provenance().items() if k != "closed_at_utc"} for i in INTERFACES]
    assert stable[0] == stable[1] == stable[2]
    served = mcp_server.ClosedSessions(sessions)
    for turn in turns.values():
        prefix = f"pdlt://sessions/{turn.session}/{turn.workspace}/{turn.turn}/"
        contents = served.read(prefix + "response")["contents"]
        assert [c["uri"] for c in contents] == [prefix + "response", prefix + "provenance"]
        assert json.loads(contents[1]["text"]) == turn.provenance()


def test_a_session_moves_between_interfaces(tmp_path, monkeypatch):
    """Started headless, stopped at its review (exit 2); confirmed in the interactive REPL; read by the library and
    served by the MCP server."""
    sessions = tmp_path / "sessions"
    started = drive("headless", "confirmed-success", sessions, "s-1", monkeypatch, lines=[REQUEST])
    assert (started["stage"], started["exit_status"]) == ("PROMPT_REVIEW", api.EXIT_UNCONFIRMED)
    finished = drive("interactive", "confirmed-success", sessions, "s-1", monkeypatch, lines=["/confirm", "/confirm"])
    assert finished["stage"] == "CLOSED_SUCCESS"
    assert finished["provenance"]["verification"]["level"] == "contract_checked"
    served = mcp_server.ClosedSessions(sessions).list(None)["resources"]
    assert [r["uri"].rsplit("/", 1)[1] for r in served] == ["provenance", "response"]  # no program ran
