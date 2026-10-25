"""Run the pre-merge catalogue with fail-fast continuation and exact final coverage.

    python experiments/premerge_catalogue.py REPO OUT_JSON [--baseline RUN_DIR]

Child logs/state and raw results stay outside the checkout. A completed evaluation can contain
model failures; missing output, harness errors and foreign/stale evidence never count as coverage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import catalogue_runs
import run_catalogue
from experiments import matched_study
from pdl_taskmaster.fileio import replace_text

MIN_REMAINING = 0.08
MODEL = "openai/gpt-oss-120b"
SCHEMA = "pdlt.premerge/2"


def results_of(run_dir: Path) -> dict[str, dict]:
    results = {}
    for folder in sorted((run_dir / "results").iterdir()):
        if not folder.is_dir():
            continue
        result = json.loads((folder / "result.json").read_text(encoding="utf-8"))
        if not isinstance(result, dict) or not isinstance(result.get("id"), str) or not result.get("verdict"):
            raise ValueError(f"invalid result in {folder}")
        pid = result["id"]
        if pid in results:
            raise ValueError(f"duplicate result ID {pid} in {run_dir}")
        results[pid] = result
    return results


def code_identity(code: dict) -> dict:
    return {key: code.get(key) for key in ("commit", "dirty", "diff_sha256")}


class CatalogueCheck:
    def __init__(self, repo: Path, out: Path, baseline: Path | None = None):
        self.repo, self.out = repo.resolve(), out.resolve()
        self.archive = catalogue_runs.runs_dir(self.repo)
        if not self.archive.is_absolute():
            self.archive = self.repo / self.archive
        self.archive = self.archive.resolve()
        if self.archive.is_relative_to(self.repo) or self.out.is_relative_to(self.repo):
            raise ValueError("catalogue outputs and state must be outside the checkout")
        manifest_bytes = (self.repo / "prompts" / "CATALOGUE_MANIFEST.jsonl").read_bytes()
        self.manifest = [json.loads(line) for line in manifest_bytes.decode("utf-8").splitlines() if line.strip()]
        self.expected = {item["id"] for item in self.manifest}
        if not self.expected or len(self.expected) != len(self.manifest):
            raise ValueError("the catalogue must contain unique prompt IDs")
        code = run_catalogue.code_provenance(self.repo)
        run_catalogue.refuse_dirty_tree(code, False)
        if not code.get("commit"):
            raise ValueError("the checked candidate must have a Git source identity")
        self.identity = {"code": code_identity(code), "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                         "model": MODEL, "route": "unconfirmed"}
        self.baseline = {pid: run_catalogue.outcome_class(r) for pid, r in results_of(
            baseline or self.archive / "run-20261017-171943-unconfirmed-tier-d1").items()}
        self.identity["baseline_sha256"] = hashlib.sha256(
            json.dumps(self.baseline, sort_keys=True).encode()).hexdigest()
        self.state = {"schema": SCHEMA, "identity": self.identity, "settings": None,
                      "outcomes": {}, "runs": [], "stops": []}
        if self.out.is_file():
            self.state = json.loads(self.out.read_text(encoding="utf-8"))
            if self.state.get("schema") != SCHEMA or self.state.get("identity") != self.identity:
                raise ValueError("state has a legacy or different candidate identity; keep it and use a new output file")
            self._validate_saved()

    def save(self) -> None:
        self.out.parent.mkdir(parents=True, exist_ok=True)
        replace_text(self.out, json.dumps(self.state, indent=1) + "\n")

    def metadata(self, folder: Path, arguments: list[str] | None = None) -> dict:
        meta = json.loads((folder / "RUN_META.json").read_text(encoding="utf-8"))
        if not isinstance(meta, dict):
            raise ValueError(f"invalid run metadata in {folder}")
        if (code_identity(meta.get("code", {})) != self.identity["code"] or meta.get("model") != MODEL
                or meta.get("route") != "unconfirmed" or meta.get("repeat") != 1 or meta.get("manifest") is not None):
            raise ValueError(f"foreign run identity in {folder}")
        if meta.get("run_id") != folder.name:
            raise ValueError(f"run ID does not match its output folder {folder}")
        if arguments is not None:
            filters = dict(zip(arguments[::2], arguments[1::2]))
            if (meta.get("category_filter") != filters.get("--category")
                    or meta.get("prompt_id_filter") != filters.get("--prompt-id")):
                raise ValueError(f"child filters do not match the requested invocation in {folder}")
        keys = ("model", "route", "reasoning_effort", "reasoning_by_operation", "reasoning_effective", "run_settings",
                "sandbox", "timeout_per_prompt", "harness_memory_mb")
        settings = {key: meta.get(key) for key in keys}
        if self.state["settings"] is not None and settings != self.state["settings"]:
            raise ValueError(f"run settings changed in {folder}")
        return settings

    def _validate_saved(self) -> None:
        for record in self.state["runs"]:
            if record.get("exit") is None or record.get("error") or not record.get("validated", True):
                raise ValueError("unresolved child in saved state; preserve its logs/results and reconcile its "
                                 "exit, liveness and evidence before continuing; no new child was launched")
        outcomes = self.state["outcomes"]
        if not isinstance(outcomes, dict) or set(outcomes) - self.expected:
            raise ValueError("state contains invalid or unexpected prompt coverage")
        if outcomes and not isinstance(self.state.get("settings"), dict):
            raise ValueError("saved coverage has no frozen execution settings")
        cache = {}
        for pid, recorded in outcomes.items():
            folder = (self.archive / recorded["run"]).resolve()
            if not folder.is_relative_to(self.archive) or folder == self.archive:
                raise ValueError("state run must stay inside the archive")
            if folder not in cache:
                self.metadata(folder)
                cache[folder] = results_of(folder)
            actual = cache[folder].get(pid)
            if actual is None or (actual["verdict"], run_catalogue.outcome_class(actual)) != (
                    recorded["verdict"], recorded["outcome"]):
                raise ValueError(f"saved coverage for {pid} has missing or changed evidence")
            if recorded.get("baseline") != self.baseline.get(pid):
                raise ValueError(f"saved baseline comparison changed for {pid}")

    def invoke(self, arguments: list[str], requested: list[str]) -> dict[str, dict]:
        child_root = (self.archive / "premerge" / hashlib.sha256(str(self.out).encode()).hexdigest()[:16]
                      / f"child-{len(self.state['runs']) + 1:03d}")
        logs = self.out.with_suffix(".logs")
        log = logs / f"child-{len(self.state['runs']) + 1:03d}.log"
        record = {"args": arguments, "exit": None, "run": None, "validated": False,
                  "log": str(log), "child_root": str(child_root), "requested": requested}
        self.state["runs"].append(record)
        self.save()  # reserve before spawn; a crash must not cause silent resampling
        try:
            child_root.mkdir(parents=True, exist_ok=False)
            logs.mkdir(parents=True, exist_ok=True)
            with log.open("w", encoding="utf-8") as handle:
                child = subprocess.run([sys.executable, "run_catalogue.py", "--model", MODEL, "--fail-fast", *arguments],
                                       cwd=self.repo, env={**os.environ, "PDLT_CATALOGUE_RUNS": str(child_root)},
                                       stdout=handle, stderr=subprocess.STDOUT)
        except BaseException as exc:
            record["error"] = f"{type(exc).__name__}: child completion/liveness not established"
            self.save()
            raise
        new = sorted(p for p in child_root.glob("run-*") if p.is_dir())
        record.update(exit=child.returncode,
                      run=new[0].relative_to(self.archive).as_posix() if len(new) == 1 else None)
        self.save()  # retain the actual return code even if validation is interrupted
        try:
            if child.returncode not in (0, 1):
                raise ValueError(f"child exited {child.returncode}")
            if len(new) != 1:
                raise ValueError(f"expected one new run folder, found {len(new)}")
            folder = new[0]
            settings = self.metadata(folder, arguments)
            found = results_of(folder)
            scoreboard = json.loads((folder / "SCOREBOARD.json").read_text(encoding="utf-8"))
            if scoreboard.get("total_prompts") != len(found):
                raise ValueError("child scoreboard and result count disagree")
            if not found or set(found) - set(requested):
                raise ValueError("missing results or unexpected prompt IDs")
            if any(str(r["verdict"]).startswith("HARNESS_") or r.get("harness_error") for r in found.values()):
                raise ValueError("child has a harness/provider error; inspect its recorded artifacts")
            if child.returncode and not any(run_catalogue.stops_fail_fast(r) for r in found.values()):
                raise ValueError("nonzero child exit without a recorded fail-fast outcome")
            if set(found) != set(requested):
                prefix = requested[:len(found)]
                if set(found) != set(prefix) or not run_catalogue.stops_fail_fast(found[prefix[-1]]):
                    raise ValueError("incomplete results without a legitimate fail-fast stop")
            if set(found) & set(self.state["outcomes"]):
                raise ValueError("child repeats already observed prompt IDs")
            self.state["settings"] = settings
            for pid, result in found.items():
                self.state["outcomes"][pid] = {"outcome": run_catalogue.outcome_class(result),
                    "baseline": self.baseline.get(pid), "verdict": result["verdict"], "run": record["run"]}
            record["validated"] = True
        except (ValueError, OSError, KeyError, TypeError) as exc:
            record["error"] = str(exc)
            self.save()
            raise ValueError(f"invalid child output ({log}): {exc}") from exc
        self.save()
        return found

    def budget_ok(self) -> bool:
        remaining = matched_study.key_state().get("limit_remaining")
        if remaining is not None and remaining < MIN_REMAINING:
            self.state["stopped_for_budget"] = remaining
            self.save()
            return False
        return True

    def run(self) -> dict:
        self._validate_saved()
        for category in dict.fromkeys(item["category"] for item in self.manifest):
            ids = [item["id"] for item in self.manifest if item["category"] == category]
            pending = [pid for pid in ids if pid not in self.state["outcomes"]]
            if pending == ids:
                if not self.budget_ok():
                    raise ValueError("stopped for budget before complete coverage")
                self.invoke(["--category", category], ids)
            for pid in (pid for pid in ids if pid not in self.state["outcomes"]):
                if not self.budget_ok():
                    raise ValueError("stopped for budget before complete coverage")
                self.state["stops"].append({"category": category, "continued_at": pid})
                self.invoke(["--prompt-id", pid], [pid])
        if set(self.state["outcomes"]) != self.expected:
            raise ValueError("incomplete final catalogue coverage")
        outcomes = self.state["outcomes"]
        self.state["summary"] = {"counts": dict(Counter(o["outcome"] for o in outcomes.values())),
            "baseline_counts": dict(Counter(self.baseline.values())), "prompts": len(outcomes),
            "categories": len({item["category"] for item in self.manifest}),
            "regressions": sorted(pid for pid, o in outcomes.items() if o["outcome"] in ("FAIL", "HELD")
                                  and o["baseline"] not in ("FAIL", "HELD")),
            "improved": sorted(pid for pid, o in outcomes.items() if o["outcome"] == "PASS"
                               and o["baseline"] in ("FAIL", "HELD"))}
        self.save()
        return self.state["summary"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo", type=Path)
    parser.add_argument("out", type=Path)
    parser.add_argument("--baseline", type=Path)
    args = parser.parse_args(argv)
    try:
        summary = CatalogueCheck(args.repo, args.out, args.baseline).run()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f"PREMERGE: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
