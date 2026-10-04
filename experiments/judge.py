"""Blinded model judges for the judged group (design §12; PR 2 work list T5).

Prompts without a machine grader are judged against a **frozen rubric**,
`experiments/rubrics/<id>.json`. A rubric is a list of criteria written from the
prompt text and a reference answer only, never from model outputs. Each criterion
is required or not.

The verdict is computed, not trusted. A judge reports met / not met for each
criterion, and the verdict is PASS exactly when every required criterion is met. A
judge's own overall verdict, if it gives one, is recorded but never used.

**Two judges** from different labs (configured in the gate config, "judges")
grade every deliverable blind:
- the deliverable passes through `grading.strip_for_adjudication`;
- the judge prompt names no arm, protocol or model.

Agreement settles a row. Disagreement goes to the user (`disagreements`), as in
`adjudicate.py`.

**Calibration comes first** (`calibrate`). Every rubric ships stress answers with
known labels: `rubrics/answers/<id>/pass_*.md` and `fail_*.md`. Both judges grade
them, and Cohen's kappa is computed between the judges and against the labels.
- A rubric whose judges reach kappa >= 0.7 (KAPPA_FLOOR) is used as a grader.
- Below that, its judged results are reported separately and never enter a
  decision rule.

**Manual mode.** `export_requests` writes the judge prompts, and `import_verdicts`
reads verdicts back. A judge can then be run in a chat UI instead of the API.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

RUBRICS = Path(__file__).resolve().parent / "rubrics"
KAPPA_FLOOR = 0.7
# Catalogue prompts whose machine grader can return only one of PASS and FAIL
# (design F11): they keep that grader for the catalogue, and the gate judges them.
QUALITATIVE = frozenset({"14-02", "14-04", "14-06", "16-01", "16-02", "16-04"})
MET, NOT_MET = "met", "not_met"


@dataclass(frozen=True)
class Criterion:
    id: str
    text: str
    required: bool = True


@dataclass(frozen=True)
class Rubric:
    id: str
    task: str                      # what the deliverable is judged as
    criteria: tuple[Criterion, ...]
    reference: str = ""            # the reference answer or facts, shown to the judge
    notes: str = ""                # how to treat equivalent forms, partial answers, refusals

    def verdict(self, marks: dict[str, str]) -> str:
        """PASS exactly when every required criterion is marked met."""
        required = [c.id for c in self.criteria if c.required]
        return "PASS" if all(marks.get(cid) == MET for cid in required) else "FAIL"


def rubric_ids() -> list[str]:
    """Catalogue ids with a rubric (CALIBRATION.json and other reports are not rubrics)."""
    return sorted(p.stem for p in RUBRICS.glob("[0-9][0-9]-[0-9][0-9].json"))


def load_rubric(rubric_id: str) -> Rubric:
    data = json.loads((RUBRICS / f"{rubric_id}.json").read_text(encoding="utf-8"))
    criteria = tuple(Criterion(c["id"], c["text"], bool(c.get("required", True))) for c in data["criteria"])
    ids = [c.id for c in criteria]
    if len(set(ids)) != len(ids) or not criteria:
        raise ValueError(f"rubric {rubric_id}: criteria ids must be unique and non-empty")
    return Rubric(data["id"], data["task"], criteria, data.get("reference", ""), data.get("notes", ""))


def stress_answers(rubric_id: str) -> list[tuple[str, str, str]]:
    """(name, known label, text) for every stress answer of a rubric."""
    out = []
    for path in sorted((RUBRICS / "answers" / rubric_id).glob("*.md")):
        label = "PASS" if path.name.startswith("pass") else "FAIL" if path.name.startswith("fail") else None
        if label:
            out.append((path.name, label, path.read_text(encoding="utf-8")))
    return out


# --------------------------------------------------------------------------- the judge prompt

_INSTRUCTIONS = """You are grading one response to a task against a fixed rubric.

Judge only what the rubric's criteria ask. Do not reward length, style or confidence. A criterion is "met" only if the response itself satisfies it; an answer that is correct but stated in different words or a different order meets it. If a criterion cannot be checked from the response, mark it "not_met".

Reply with one JSON object and nothing else:
{"criteria": {"<criterion id>": "met" | "not_met", ...}, "note": "<one or two sentences on any criterion marked not_met>"}"""


def judge_prompt(rubric: Rubric, prompt_text: str, deliverable: str) -> str:
    criteria = "\n".join(f"- {c.id}{'' if c.required else ' (optional)'}: {c.text}" for c in rubric.criteria)
    parts = [
        _INSTRUCTIONS,
        f"## The task the response answers\n\n{prompt_text.strip()}",
        f"## What is being judged\n\n{rubric.task.strip()}",
        f"## Criteria\n\n{criteria}",
    ]
    if rubric.reference.strip():
        parts.append(f"## Reference (for the judge; the response need not match its wording)\n\n{rubric.reference.strip()}")
    if rubric.notes.strip():
        parts.append(f"## Notes\n\n{rubric.notes.strip()}")
    parts.append(f"## The response\n\n<<<RESPONSE\n{deliverable.strip()}\nRESPONSE>>>")
    return "\n\n".join(parts)


def parse_marks(text: str, rubric: Rubric) -> dict[str, str]:
    """The judge's per-criterion marks. A missing or unreadable mark is not_met."""
    candidates = re.findall(r"\{.*\}", text or "", re.S)
    data: Any = None
    for blob in sorted(candidates, key=len, reverse=True):
        try:
            data = json.loads(blob)
            break
        except ValueError:
            continue
    raw = data.get("criteria", {}) if isinstance(data, dict) else {}
    marks = {}
    for c in rubric.criteria:
        value = str(raw.get(c.id, "")).strip().lower().replace(" ", "_").replace("-", "_")
        marks[c.id] = MET if value in ("met", "true", "yes", "pass") else NOT_MET
    return marks


# --------------------------------------------------------------------------- judging

@dataclass
class JudgeSpec:
    name: str
    model: str
    providers: list[str] = field(default_factory=list)
    effort: str | None = None


Sender = Callable[[JudgeSpec, str], str]  # (judge, prompt) -> reply text


def openrouter_sender(repo_root: Path, *, max_output_tokens: int = 8000) -> Sender:
    """Sends through the API worker's own transport, as the control arms do."""
    from pdl_taskmaster.providers.api_worker import ApiWorker

    workers: dict[str, ApiWorker] = {}

    def send(spec: JudgeSpec, prompt: str) -> str:
        import time

        worker = workers.get(spec.name)
        if worker is None:
            pinning = {"order": list(spec.providers), "allow_fallbacks": False} if spec.providers else None
            worker = workers[spec.name] = ApiWorker(repo_root=repo_root, model=spec.model,
                                                    max_output_tokens=max_output_tokens, provider_pinning=pinning)
        body: dict[str, Any] = {"model": spec.model, "input": prompt, "max_output_tokens": max_output_tokens}
        if worker.provider_pinning:
            body["provider"] = worker.provider_pinning
        if spec.effort:
            body["reasoning"] = {"effort": spec.effort}
        request = worker._responses_request(body, worker._resolve_api_key())
        data = worker._send_json_with_retries(request, time.monotonic() + worker.max_call_seconds)
        return ApiWorker._extract_output_text(data)

    return send


def judge(rubric: Rubric, prompt_text: str, deliverable: str, judges: list[JudgeSpec],
          send: Sender) -> dict[str, dict[str, Any]]:
    """Each judge's marks and computed verdict for one deliverable."""
    from experiments.grading import strip_for_adjudication

    prompt = judge_prompt(rubric, prompt_text, strip_for_adjudication(deliverable))
    out: dict[str, dict[str, Any]] = {}
    for spec in judges:
        try:
            reply = send(spec, prompt)
        except Exception as exc:  # a failed judge call is recorded, never a verdict
            out[spec.name] = {"verdict": None, "error": f"{type(exc).__name__}: {exc}"[:500]}
            continue
        marks = parse_marks(reply, rubric)
        out[spec.name] = {"verdict": rubric.verdict(marks), "marks": marks, "reply": reply[:4000]}
    return out


def settled(verdicts: dict[str, dict[str, Any]]) -> str | None:
    """The agreed verdict, or None when the judges disagree or a call failed."""
    values = {v.get("verdict") for v in verdicts.values()}
    return values.pop() if len(values) == 1 and None not in values else None


# --------------------------------------------------------------------------- agreement

def cohen_kappa(a: list[str], b: list[str]) -> float:
    """Cohen's kappa for two raters over the same items (PASS/FAIL labels)."""
    if len(a) != len(b) or not a:
        raise ValueError("kappa needs two equal, non-empty label lists")
    n = len(a)
    observed = sum(x == y for x, y in zip(a, b)) / n
    labels = set(a) | set(b)
    expected = sum((a.count(k) / n) * (b.count(k) / n) for k in labels)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def calibrate(rubric_ids_: list[str], prompts: dict[str, str], judges: list[JudgeSpec], send: Sender) -> dict[str, Any]:
    """Judge every stress answer; kappa between the judges and against the known labels.

    ``prompts`` maps a rubric id to its prompt text."""
    rows = []
    for rid in rubric_ids_:
        rubric = load_rubric(rid)
        for name, label, text in stress_answers(rid):
            verdicts = judge(rubric, prompts[rid], text, judges, send)
            rows.append({"rubric": rid, "answer": name, "label": label,
                         **{j.name: verdicts[j.name].get("verdict") for j in judges}})
    return calibration_report(rows, [j.name for j in judges])


def calibration_report(rows: list[dict[str, Any]], names: list[str]) -> dict[str, Any]:
    """Accuracy per rubric and judge, and kappa between the judges and against the labels.

    Each row: {"rubric", "answer", "label", <judge name>: "PASS" | "FAIL" | None}. It is
    shared by live calibration and by verdicts collected by hand or by an in-session agent."""
    report: dict[str, Any] = {"rows": rows, "kappa_floor": KAPPA_FLOOR, "rubrics": {}}
    for rid in sorted({r["rubric"] for r in rows}):
        mine = [r for r in rows if r["rubric"] == rid and all(r.get(n) for n in names)]
        entry: dict[str, Any] = {"answers": len(mine)}
        for n in names:
            entry[f"{n}_accuracy"] = (sum(r[n] == r["label"] for r in mine) / len(mine)) if mine else None
        if len(names) == 2:
            entry["judges_agree"] = sum(r[names[0]] == r[names[1]] for r in mine)
        report["rubrics"][rid] = entry
    complete = [r for r in rows if all(r.get(n) for n in names)]
    report["complete_rows"] = len(complete)
    if len(names) == 2 and complete:
        report["kappa_between_judges"] = cohen_kappa([r[names[0]] for r in complete], [r[names[1]] for r in complete])
    for n in names:
        if complete:
            report[f"kappa_{n}_vs_label"] = cohen_kappa([r[n] for r in complete], [r["label"] for r in complete])
    kappas = [v for k, v in report.items() if k.startswith("kappa_") and k != "kappa_floor"]
    report["usable"] = bool(kappas) and len(complete) == len(rows) and all(v >= KAPPA_FLOOR for v in kappas)
    return report


# --------------------------------------------------------------------------- manual mode

def export_requests(items: list[dict[str, str]], out_dir: Path) -> Path:
    """Write one judge prompt per item ({"key", "rubric", "prompt_text", "deliverable"})
    for a judge run by hand. Keys must already be blinded (no arm names)."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    from experiments.grading import strip_for_adjudication

    index = []
    for item in items:
        rubric = load_rubric(item["rubric"])
        text = judge_prompt(rubric, item["prompt_text"], strip_for_adjudication(item["deliverable"]))
        (out_dir / f"{item['key']}.txt").write_text(text, encoding="utf-8")
        index.append({"key": item["key"], "rubric": item["rubric"]})
    path = out_dir / "index.json"
    path.write_text(json.dumps(index, indent=2), encoding="utf-8")
    return path


def import_verdicts(index_path: Path, replies_dir: Path) -> dict[str, dict[str, Any]]:
    """Verdicts from replies saved as <key>.reply.txt next to the exported prompts."""
    out = {}
    for entry in json.loads(Path(index_path).read_text(encoding="utf-8")):
        reply_path = Path(replies_dir) / f"{entry['key']}.reply.txt"
        if not reply_path.is_file():
            continue
        rubric = load_rubric(entry["rubric"])
        marks = parse_marks(reply_path.read_text(encoding="utf-8"), rubric)
        out[entry["key"]] = {"verdict": rubric.verdict(marks), "marks": marks}
    return out


# --------------------------------------------------------------------------- CLI

def _catalogue_prompts() -> dict[str, str]:
    root = Path(__file__).resolve().parents[1] / "prompts"
    out = {}
    for line in (root / "CATALOGUE_MANIFEST.jsonl").read_text(encoding="utf-8-sig").splitlines():
        if line.strip():
            entry = json.loads(line)
            out[entry["id"]] = (root / entry["file"]).read_text(encoding="utf-8-sig")
    return out


def main(argv: list[str] | None = None) -> int:
    """python -m experiments.judge calibrate --config <gate config> [--rubrics id ...]
    python -m experiments.judge export-calibration --out <dir>  (manual mode: paste into a chat UI)"""
    import argparse

    parser = argparse.ArgumentParser(prog="python -m experiments.judge")
    sub = parser.add_subparsers(dest="command", required=True)
    cal = sub.add_parser("calibrate", help="judge every stress answer live and write CALIBRATION.json")
    cal.add_argument("--config", required=True)
    cal.add_argument("--rubrics", nargs="*")
    exp = sub.add_parser("export-calibration", help="write the calibration judge prompts for manual judging")
    exp.add_argument("--out", required=True)
    rep = sub.add_parser("report-calibration", help="kappa from collected replies (manual or in-session judges)")
    rep.add_argument("--export", required=True, help="the export-calibration directory (holds index.json)")
    rep.add_argument("--judge", action="append", required=True, metavar="NAME=REPLIES_DIR")
    args = parser.parse_args(argv)

    prompts = _catalogue_prompts()
    ids = getattr(args, "rubrics", None) or rubric_ids()
    if args.command == "export-calibration":
        import random

        # Keys are opaque and shuffled: a file name must not reveal the known label.
        answers_ = [(rid, name, label, text) for rid in ids for name, label, text in stress_answers(rid)]
        random.Random(20261004).shuffle(answers_)
        items, key = [], {}
        for n, (rid, name, label, text) in enumerate(answers_, 1):
            items.append({"key": f"cal{n:03d}", "rubric": rid, "prompt_text": prompts[rid], "deliverable": text})
            key[f"cal{n:03d}"] = {"rubric": rid, "answer": name, "label": label}
        out_dir = Path(args.out)
        print(export_requests(items, out_dir))
        # Keep the key away from whoever judges by hand.
        (out_dir.parent / f"{out_dir.name}.KEY.json").write_text(json.dumps(key, indent=2), encoding="utf-8")
        return 0
    if args.command == "report-calibration":
        export_dir = Path(args.export)
        key = json.loads((export_dir.parent / f"{export_dir.name}.KEY.json").read_text(encoding="utf-8"))
        names, verdicts = [], {}
        for spec in args.judge:
            name, _, replies = spec.partition("=")
            names.append(name)
            verdicts[name] = import_verdicts(export_dir / "index.json", Path(replies))
        rows = [{"rubric": k["rubric"], "answer": k["answer"], "label": k["label"], "key": cal,
                 **{n: (verdicts[n].get(cal) or {}).get("verdict") for n in names}} for cal, k in sorted(key.items())]
        report = calibration_report(rows, names)
        report["judges"] = names
        out = RUBRICS / "CALIBRATION.json"
        out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({k: v for k, v in report.items() if k.startswith("kappa") or k in ("usable", "complete_rows")},
                         indent=2))
        return 0 if report["usable"] else 1
    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    judges = [JudgeSpec(j["name"], j["model"], list(j.get("providers", [])), j.get("effort"))
              for j in config.get("judges", [])]
    if len(judges) != 2:
        parser.error("the config needs exactly two judges (\"judges\": [{name, model, providers?, effort?}, ...])")
    repo_root = Path(__file__).resolve().parents[1]
    report = calibrate(ids, prompts, judges, openrouter_sender(repo_root))
    report["judges"] = [vars(j) for j in judges]
    out = RUBRICS / "CALIBRATION.json"
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if k.startswith("kappa") or k == "usable"}, indent=2))
    return 0 if report["usable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
