"""Static analysis of the original entity model on L99's 126 recorded unconfirmed runs.

For each run: what BOOTSTRAP wrote (entities, roles, kinds, free-text relations), what EXECUTE
received (TASK_ENTITIES), where each surface comes from (request vs summary only), and the
catalogue's outcome class. Writes entity-corpus.json into the run folder and prints aggregates.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(r"C:\Users\USER\Desktop\Frameworks\PDLt-Test")
sys.path.insert(0, str(ROOT))  # catalogue_runs.py lives at the repository root
from catalogue_runs import RUNS_DIR  # noqa: E402  (runs live outside the repository)
sys.path[:0] = [str(ROOT), str(ROOT / "src")]
from run_catalogue import outcome_class  # noqa: E402
from pdl_taskmaster.runtime.quarantine import compile_bootstrap_output  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
from quotes import RequestText  # noqa: E402  (a copy of the L100 locator; vNext's runtime has none)

RUN = RUNS_DIR / sys.argv[1] if len(sys.argv) > 1 else RUNS_DIR / "run-20261009-042907-unconfirmed-tier-d1"
OUT = RUN / "entity-corpus.json"
WORD = re.compile(r"[A-Za-z0-9_]+")


def first_json(text: str):
    try:
        return json.JSONDecoder().raw_decode(text[text.index("{"):])[0]
    except ValueError:
        return None


def novel_words(text: str, source: str) -> float:
    """Share of a relation's words that do not occur in the request: how much is the model's own wording."""
    words = [w.lower() for w in WORD.findall(text or "")]
    if not words:
        return 0.0
    vocab = {w.lower() for w in WORD.findall(source)}
    return sum(w not in vocab for w in words) / len(words)


rows = []
for d in sorted((RUN / "results").iterdir()):
    result = json.loads((d / "result.json").read_text(encoding="utf-8"))
    row = {"run": d.name, "prompt": d.name[:5], "category": d.name[:2], "class": outcome_class(result),
           "verdict": result.get("verdict")}
    turns = sorted(d.glob("session/W-*/turns/turn_001"))
    if not turns:
        rows.append(row)
        continue
    turn = turns[0]
    raw_md = turn / "stages/10_prompt/input/0001-bootstrap_analysis/raw_untrusted_content.md"
    raw = raw_md.read_text(encoding="utf-8").replace("<untrusted_user_input>", "").replace("</untrusted_user_input>", "").strip() if raw_md.is_file() else ""
    sanitized = compile_bootstrap_output(raw, raw)[0]
    sources = RequestText(sanitized)
    replies = [first_json(p.read_text(encoding="utf-8"))
               for p in sorted((turn / "stages/10_prompt/output").glob("*-bootstrap_analysis/model-response.txt"))]
    reply = next((r for r in reversed(replies) if r and r.get("kind") == "ANALYSIS"), None)
    row["bootstrap_kind"] = replies[-1].get("kind") if replies and replies[-1] else None
    if reply:
        ents = [e if isinstance(e, dict) else {"surface": e} for e in reply.get("task_entities") or []]
        row["written"] = len(ents)
        row["targets_written"] = sum(str(e.get("status", "")).lower() == "target" for e in ents)
        row["kinds"] = dict(Counter(e.get("kind") for e in ents))
        rel = [e.get("relation") for e in ents if isinstance(e.get("relation"), str) and e["relation"].strip()]
        row["with_relation"] = len(rel)
        row["relation_chars"] = sum(map(len, rel))
        row["relation_novelty"] = round(sum(novel_words(r, raw) for r in rel) / len(rel), 3) if rel else None
        row["surface_in_request"] = sum(sources.locate(e.get("surface")) is not None for e in ents)
        tgt = [e for e in ents if str(e.get("status", "")).lower() == "target"]
        row["targets_in_request"] = sum(sources.locate(e.get("surface")) is not None for e in tgt)
        row["target_surfaces"] = [e.get("surface") for e in tgt]
        row["target_kinds"] = dict(Counter(e.get("kind") for e in tgt))
        row["groups"] = len({e.get("group") for e in ents if e.get("group")})
        # The target's relation: does it name what to produce or determine (the model's reading)?
        row["target_relations"] = [(e.get("surface"), e.get("relation")) for e in tgt][:8]
    sent = sorted(turn.glob("stages/50_execution/input/*-execute_unconfirmed/task_entities.json"))
    if sent:
        fwd = json.loads(sent[0].read_text(encoding="utf-8"))
        row["forwarded"] = len(fwd)
        row["forwarded_targets"] = sum(e.get("status") == "target" for e in fwd)
        row["forwarded_chars"] = len(json.dumps(fwd, ensure_ascii=False))
    rows.append(row)

OUT.write_text(json.dumps(rows, indent=1, ensure_ascii=False), encoding="utf-8")

# --- aggregates ---------------------------------------------------------------------------------
classes = Counter(r["class"] for r in rows)
print("runs", len(rows), dict(classes))
has = [r for r in rows if "written" in r]
tot = lambda k: sum(r.get(k) or 0 for r in has)  # noqa: E731
print(f"analysis replies {len(has)}; entities written {tot('written')}; targets {tot('targets_written')}; "
      f"with relation {tot('with_relation')} (chars {tot('relation_chars')})")
print(f"surfaces found in the request (request-only rule) {tot('surface_in_request')}/{tot('written')}; "
      f"targets found {tot('targets_in_request')}/{tot('targets_written')}")
nov = [r["relation_novelty"] for r in has if r.get("relation_novelty") is not None]
print(f"relation novelty (share of words not in the request): mean {sum(nov)/len(nov):.2f}")
print("runs with no target written:", sum(1 for r in has if not r["targets_written"]),
      " forwarded with no target:", sum(1 for r in has if r.get("forwarded") is not None and not r.get("forwarded_targets")))
print("target kinds:", dict(sum((Counter(r.get("target_kinds") or {}) for r in has), Counter())))

# Within-prompt contrasts: prompts with both PASS and FAIL repeats (difficulty held fixed).
by_prompt = defaultdict(list)
for r in has:
    by_prompt[r["prompt"]].append(r)
print("\nmixed prompts (PASS and FAIL repeats): feature means, PASS vs FAIL")
feats = ["written", "targets_written", "with_relation", "relation_chars", "targets_in_request", "forwarded_targets"]
agg = {f: [0.0, 0, 0.0, 0] for f in feats}
for p, rs in sorted(by_prompt.items()):
    cls = {r["class"] for r in rs}
    if not {"PASS", "FAIL"} <= cls:
        continue
    line = [p]
    for f in feats:
        ps = [r.get(f) or 0 for r in rs if r["class"] == "PASS"]
        fs = [r.get(f) or 0 for r in rs if r["class"] == "FAIL"]
        agg[f][0] += sum(ps) / len(ps); agg[f][1] += 1
        agg[f][2] += sum(fs) / len(fs); agg[f][3] += 1
        line.append(f"{f}={sum(ps)/len(ps):.1f}/{sum(fs)/len(fs):.1f}")
    print("  ", " ".join(line))
print("  mean over mixed prompts (PASS / FAIL):",
      {f: (round(a / b, 2), round(c / d, 2)) for f, (a, b, c, d) in agg.items() if b})
