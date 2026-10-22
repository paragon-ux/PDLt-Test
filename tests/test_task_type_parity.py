"""L124 D2: every built-in task type, registered through its profile, behaves exactly as before task types existed:
the same worker and System 1 requests, stages, exit statuses, events and provenance (tests/parity_scenarios.py;
the fixture was recorded from the engine before the migration and matches the pre-B2 main tree). Offline."""
from __future__ import annotations

import json
import sys

import pytest

import parity_scenarios
from parity_scenarios import FIXTURE, SCENARIOS


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_each_built_in_behaves_as_before_task_types(name, tmp_path):
    from pdl_taskmaster import __version__

    record = parity_scenarios.run(name, tmp_path / name)
    expected = json.loads(FIXTURE.read_text(encoding="utf-8"))[name]
    if record["provenance"]:
        assert record["provenance"]["pdlt_version"] == __version__  # the running release, not the recorded one
    assert parity_scenarios.comparable(record) == parity_scenarios.comparable(expected)


def test_the_declared_interpreter_is_the_one_that_runs():
    """L134: the parity hashes key the interpreter declaration to the fixture's version; the declaration itself
    names this host's interpreter, and that interpreter is the one the sandbox runs."""
    from pdl_taskmaster.verification.sandbox import PYTHON_VERSION, ExecutionSandbox, python_declaration

    running = ".".join(map(str, sys.version_info[:2]))
    assert PYTHON_VERSION == running and f"Python {running} " in python_declaration()
    with ExecutionSandbox(label="parity") as sandbox:
        result = sandbox.run_code("import sys\nprint('.'.join(map(str, sys.version_info[:2])))")
    assert result.success, result.stderr
    assert result.stdout.strip() == running
