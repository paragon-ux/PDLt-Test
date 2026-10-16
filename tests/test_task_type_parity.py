"""L124 D2: every built-in task type, registered through its profile, behaves exactly as before task types existed:
the same worker and System 1 requests, stages, exit statuses, events and provenance (tests/parity_scenarios.py;
the fixture was recorded from the engine before the migration and matches the pre-B2 main tree). Offline."""
from __future__ import annotations

import json

import pytest

import parity_scenarios
from parity_scenarios import FIXTURE, SCENARIOS


@pytest.mark.parametrize("name", sorted(SCENARIOS))
def test_each_built_in_behaves_as_before_task_types(name, tmp_path):
    assert parity_scenarios.run(name, tmp_path / name) == json.loads(FIXTURE.read_text(encoding="utf-8"))[name]
