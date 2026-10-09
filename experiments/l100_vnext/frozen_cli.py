"""Child entry for the fixed-entity experiment (ENTITY_VNEXT_PLAN.md section 5.2). It runs the harness
CLI exactly as run_catalogue.py runs it, with one difference: BOOTSTRAP_ANALYSIS returns a frozen,
recorded reply and makes no model call. Everything else (System 1, EXECUTE, its retries and the
host's verification) runs as usual. Evaluation plane only; the harness never imports this.

Environment:
    PDLT_FROZEN_REPLIES  JSON file written by fixed_entity.py freeze: {prompt path: {"reply", "sys1"}}
    PDLT_FROZEN_ARM      A (no entities: run with --no-task-entities), B (the reply as recorded),
                         C (the reply with every entity's relation removed)
    PDLT_FROZEN_DRYRUN   optional file: offline. System 1 answers from the recorded decisions,
                         each provider body is appended to this file and the call stops, and any
                         other network call raises.
"""
from __future__ import annotations

import json
import os
import runpy
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "src"), str(HERE)]

from pdl_taskmaster.providers.api_worker import ApiWorker  # noqa: E402
from pdl_taskmaster.providers.base import WorkerResult  # noqa: E402


def frozen_reply(entry: dict, arm: str) -> str:
    if arm != "C":
        return entry["reply"]
    doc = json.loads(entry["reply"])
    for entity in doc.get("task_entities") or []:
        entity.pop("relation", None)
    return json.dumps(doc, ensure_ascii=False)


def main() -> None:
    prompt = Path(sys.argv[sys.argv.index("--prompt-file") + 1]).resolve()
    entry = json.loads(Path(os.environ["PDLT_FROZEN_REPLIES"]).read_text(encoding="utf-8"))[
        prompt.relative_to(ROOT / "prompts").as_posix()]
    arm = os.environ["PDLT_FROZEN_ARM"]
    reply = frozen_reply(entry, arm)
    original_call = ApiWorker._call

    def _call(self, request):
        if getattr(request, "operation", None) == "BOOTSTRAP_ANALYSIS":
            return WorkerResult(reply, {"worker": "frozen", "model": self.model, "observed_model": self.model,
                                        "operation": "BOOTSTRAP_ANALYSIS", "frozen_arm": arm})
        return original_call(self, request)

    ApiWorker._call = _call

    dryrun = os.environ.get("PDLT_FROZEN_DRYRUN")
    if dryrun:
        from static_checks import ReplaySys1

        def no_network(*_args, **_kwargs):
            raise RuntimeError("fixed-entity dry run: network call blocked")

        urllib.request.urlopen = no_network
        original_init = ApiWorker.__init__

        def _init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            self.sys1_client = ReplaySys1(entry["sys1"])

        def _send(self, req, deadline=None):
            with open(dryrun, "a", encoding="utf-8") as handle:
                handle.write(json.dumps(json.loads(req.data.decode("utf-8")), ensure_ascii=False) + "\n")
            raise RuntimeError("fixed-entity dry run: body captured")

        ApiWorker.__init__ = _init
        ApiWorker._send_json_with_retries = _send

    sys.argv = [sys.argv[0], *sys.argv[1:]]
    runpy.run_module("pdl_taskmaster.host.cli", run_name="__main__", alter_sys=True)


if __name__ == "__main__":
    main()
