"""The original entity model's measured defects on L99's recorded runs (evaluation plane: reads artifacts only)."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(r"C:\Users\USER\Desktop\Frameworks\PDLt-Test")
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from pdl_taskmaster.runtime.quarantine import compile_bootstrap_output  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from quotes import RequestText  # noqa: E402  (a copy of the L100 locator; vNext's runtime has none)

RUN = ROOT / "catalogue-runs" / "run-20261009-042907-unconfirmed-tier-d1"
REPLY_FORM = {"answer", "expression", "result", "output", "response", "solution", "explanation", "the answer"}


def first_json(text):
    try:
        return json.JSONDecoder().raw_decode(text[text.index("{"):])[0]
    except ValueError:
        return None


dup_runs, reply_form, summary_only, payload, deduped = [], [], [], 0, 0
relations_09 = []
for d in sorted((RUN / "results").iterdir()):
    turns = sorted(d.glob("session/W-*/turns/turn_001"))
    if not turns:
        continue
    turn = turns[0]
    raw_md = turn / "stages/10_prompt/input/0001-bootstrap_analysis/raw_untrusted_content.md"
    raw = raw_md.read_text(encoding="utf-8").replace("<untrusted_user_input>", "").replace("</untrusted_user_input>", "").strip()
    sources = RequestText(compile_bootstrap_output(raw, raw)[0])
    out = sorted((turn / "stages/10_prompt/output").glob("*-bootstrap_analysis/model-response.txt"))
    reply = first_json(out[-1].read_text(encoding="utf-8")) if out else None
    if not reply or reply.get("kind") != "ANALYSIS":
        continue
    ents = [e for e in reply.get("task_entities") or [] if isinstance(e, dict)]
    surfaces = Counter((e.get("surface") or "").strip().lower() for e in ents)
    dups = [s for s, n in surfaces.items() if n > 1]
    if dups:
        statuses = {s: sorted(str(e.get("status")) for e in ents if (e.get("surface") or "").strip().lower() == s) for s in dups}
        dup_runs.append((d.name, statuses))
    for e in ents:
        s = (e.get("surface") or "").strip().strip("\"'").lower()
        if str(e.get("status")).lower() == "target" and s in REPLY_FORM:
            reply_form.append((d.name, e.get("surface")))
        if sources.locate(e.get("surface")) is None:
            summary_only.append((d.name, e.get("status"), e.get("surface")))
    sent = sorted(turn.glob("stages/50_execution/input/*-execute_unconfirmed/task_entities.json"))
    if sent:
        fwd = json.loads(sent[0].read_text(encoding="utf-8"))
        payload += len(json.dumps(fwd, ensure_ascii=False))
        deduped += len(json.dumps([{k: e[k] for k in ("surface", "kind", "status", "group", "relation") if k in e}
                                   for e in fwd], ensure_ascii=False))
        if d.name.startswith("09"):
            relations_09 += [(d.name, e.get("surface"), e.get("relation")) for e in fwd if e.get("relation")]

print(f"runs with a repeated surface: {len(dup_runs)}")
for name, st in dup_runs:
    print("  ", name, st)
print(f"reply-form targets: {len(reply_form)} {reply_form}")
print(f"surfaces not in the request (kept by the summary match): {len(summary_only)}")
for row in summary_only:
    print("  ", row)
print(f"forwarded payload chars: {payload} ; without the duplicated keys: {deduped} ({deduped / payload:.0%})")
print(f"category 09 forwarded relations: {len(relations_09)}")
for row in relations_09:
    print("  ", row[0][:12], "|", row[1], "|", (row[2] or "")[:150])
