"""L145: the call trace records every generation id, so each call's served provider, model and cost can be looked up
afterwards (OpenRouter's /generation): one per tool-loop round, and System 1's. Telemetry only; nothing sent changes.
Offline."""
from __future__ import annotations

import io
import json
from pathlib import Path

from pdl_taskmaster.providers.api_worker import ApiWorker

ROOT = Path(__file__).resolve().parents[1]


def test_every_round_of_a_call_keeps_its_generation_id():
    worker = ApiWorker(model="m", repo_root=ROOT)
    trace = worker.begin_call("EXECUTE_UNCONFIRMED")
    for gid in ("gen-1", "gen-2", "gen-3"):
        worker._record_reply({"id": gid, "model": "m", "usage": {}}, schema_constrained=False)
    worker.end_call(trace)
    assert trace.reply["response_ids"] == ["gen-1", "gen-2", "gen-3"]
    assert trace.reply["response_id"] == "gen-3"  # the last round, as before


def test_system1_calls_record_their_generation_id(monkeypatch):
    from pdl_taskmaster.providers.sys1 import client as sys1_client
    from pdl_taskmaster.providers.sys1.schema import Sys1Request

    class Response(io.BytesIO):
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    monkeypatch.setattr(sys1_client.urllib.request, "urlopen",
                        lambda req, timeout=None: Response(json.dumps({"id": "gen-s1", "model": "lfm"}).encode()))
    worker = ApiWorker(model="m", repo_root=ROOT)
    client = sys1_client.Sys1Client(api_key="k", endpoint="https://openrouter.ai/api/alpha/decisions", model="lfm")
    client.tracer = worker
    client.call(Sys1Request(state={}, questions={}))
    assert worker.call_traces[-1].reply == {"response_id": "gen-s1", "model": "lfm"}
