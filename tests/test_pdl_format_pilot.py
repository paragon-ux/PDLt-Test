"""The PDL-versus-natural-language pilot driver (ledger L97): what the model is sent, and the
frozen-artifact flow (a trunk stops at the plan review; every execution restores it and makes
exactly one EXECUTE call from the same confirmed artifacts)."""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT, ROOT / "src", ROOT / "tests"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import test_reasoning_wire as wire  # noqa: E402
from experiments import runner  # noqa: E402
from experiments.pdl_format import run_pilot as pilot  # noqa: E402


def test_the_prompts_carry_the_request_and_nothing_addressed_to_the_experimenter() -> None:
    for task in pilot.TASKS:
        prompt = pilot.task_prompt(task)
        assert "Task ID" not in prompt and "**Evaluation:**" not in prompt and "both arms" not in prompt
        assert prompt.startswith("# Task ")
    t1 = pilot.task_prompt("T1")
    fixtures = ROOT / "experiments" / "pdl_format" / "tasks" / "fixtures" / "task-01"
    for name in ("accounts.csv", "pricing.json", "events.jsonl"):
        assert (fixtures / name).read_text(encoding="utf-8").rstrip("\n") in t1
    assert "{this is not valid json}" in t1  # the malformed line is attached unchanged


def test_the_order_runs_every_task_repeat_and_arm_once_and_alternates_arms() -> None:
    sessions = [(task, repeat, arm) for task, repeat, order in pilot.ORDER for arm in order]
    assert len(sessions) == len(set(sessions)) == 18
    assert [order for _, _, order in pilot.ORDER] == ["PN", "NP"] * 4 + ["PN"]


def test_a_replay_executes_the_frozen_artifacts_in_its_arm(tmp_path, monkeypatch) -> None:
    seen: list = []
    bodies: list = []
    server = wire._stub_server(seen, bodies)
    monkeypatch.setenv("OPENROUTER_API_KEY", "stub")
    for key in [k for k in os.environ if k.startswith("SYS1")]:
        monkeypatch.delenv(key)
    stub = ("--api-base-url", f"http://127.0.0.1:{server.server_address[1]}")
    prompt = tmp_path / "p.txt"
    prompt.write_text("What is 2 + 3?", encoding="utf-8")
    try:
        trunk = tmp_path / "trunk"
        run = runner.run_cli(pilot.spec("N"), pilot.MODEL, trunk, prompt_file=prompt, restore=None,
                             stdin=runner.TRUNK_STDIN, extra_args=(*pilot.SETTINGS, *stub), timeout=120)
        assert run["exit_code"] == 2 and runner.controller_stage(trunk / "session") == "PLAN_REVIEW"
        assert [op for op, _ in seen] == ["BOOTSTRAP_ANALYSIS", "DRAFT_PROMPT", "DRAFT_PLAN"]
        for number in (1, 2):
            seen.clear()
            bodies.clear()
            execution = tmp_path / f"exec{number}"
            shutil.copytree(trunk, execution)
            workspace = next((execution / "session").glob("W-*"))
            run = runner.run_cli(pilot.spec("N"), pilot.MODEL, execution, prompt_file=None, restore=workspace,
                                 stdin=runner.FORCE_CONFIRM, extra_args=(*pilot.SETTINGS, *stub), timeout=120)
            # a contract-checked result closes CLOSED_UNVERIFIED, exit 5 (L164)
            assert run["exit_code"] == 5 and runner.controller_stage(execution / "session") == "CLOSED_UNVERIFIED"
            assert [op for op, _ in seen] == ["EXECUTE"]
            assert "Prompt Interpretation" in bodies[0]["input"]  # the replay runs in its arm
            command = json.loads((execution / "command.json").read_text(encoding="utf-8"))["cmd"]
            assert "--review" in command and command[command.index("--representation") + 1] == "nl"
    finally:
        server.shutdown()
