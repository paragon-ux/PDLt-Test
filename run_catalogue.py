#!/usr/bin/env python3
"""
PDLt Prompt Catalogue - Automated Test Runner
==============================================

Executes every prompt in CATALOGUE_MANIFEST.jsonl through the live pdlt REPL
in non-interactive mode. Each prompt gets exactly ONE attempt. No retries,
no do-overs, no cherry-picking.

Usage:
    python run_catalogue.py [--model MODEL] [--reasoning EFFORT] [--category CAT] [--dry-run]

Outputs:
    catalogue-runs/<timestamp>/
        +-- RUN_META.json           # Run configuration and environment
        +-- SCOREBOARD.json         # Aggregate results
        +-- SCOREBOARD.md           # Human-readable scoreboard
        +-- results/
            +-- 01-01_schur_triples_n15/
            |   +-- transcript.txt  # Full pdlt session output
            |   +-- stderr.txt      # Stderr capture
            |   +-- result.json     # Structured result (exit code, timing, verdict)
            +-- ...
"""

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import graders

try:  # POSIX only; imported here, never inside a forked child (import locks)
    import resource
except ImportError:
    resource = None

_script_dir = Path(__file__).resolve().parent
if (_script_dir / "prompts").is_dir():
    PDLT_TEST_ROOT = _script_dir
    RUNS_DIR = _script_dir / "catalogue-runs"
elif (_script_dir.parent / "prompts").is_dir():
    PDLT_TEST_ROOT = _script_dir.parent
    RUNS_DIR = _script_dir
else:
    PDLT_TEST_ROOT = _script_dir
    RUNS_DIR = _script_dir / "catalogue-runs"

# The runner reads the harness's own sandbox definitions (graders, containment):
# the same source tree the harness runs from, never another installed copy.
sys.path.insert(0, str(PDLT_TEST_ROOT / "src"))

from pdl_taskmaster.host.console import COLOR_NAMES, THEME_NAMES

PROMPTS_DIR = PDLT_TEST_ROOT / "prompts"
MANIFEST_PATH = PROMPTS_DIR / "CATALOGUE_MANIFEST.jsonl"
WORKTREE_DIFF = "WORKTREE.diff"



def code_provenance(root: Path = PDLT_TEST_ROOT) -> dict:
    """The code a run executes (TARGET_ARCHITECTURE I-9): the commit, whether the tree
    differs from it, and the difference itself. Untracked files run too, so each one is
    part of the difference. Returns ``diff`` (text) for the run folder plus the metadata
    recorded in RUN_META."""
    def git(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                              encoding="utf-8", errors="replace")

    head = git("rev-parse", "HEAD")
    if head.returncode != 0:
        return {"commit": None, "dirty": None, "diff": "", "diff_sha256": None, "untracked": []}
    parts = [git("diff", "HEAD", "--binary").stdout]
    untracked = []
    for rel in git("ls-files", "--others", "--exclude-standard", "-z").stdout.split("\0"):
        if not rel:
            continue
        data = (Path(root) / rel).read_bytes()
        untracked.append({"path": rel, "sha256": hashlib.sha256(data).hexdigest()})
        text = data.decode("utf-8", errors="replace")
        parts.append(f"--- /dev/null\n+++ b/{rel}\n" + "".join(f"+{line}\n" for line in text.splitlines()))
    diff = "".join(parts)
    dirty = bool(diff.strip())
    return {
        "commit": head.stdout.strip(),
        "dirty": dirty,
        "diff": diff,
        "diff_sha256": hashlib.sha256(diff.encode("utf-8")).hexdigest() if dirty else None,
        "untracked": untracked,
    }


def record_provenance(run_dir: Path, provenance: dict) -> dict:
    """Store the uncommitted difference beside the run and return RUN_META's ``code`` record."""
    if provenance.get("dirty"):
        (Path(run_dir) / WORKTREE_DIFF).write_bytes(provenance["diff"].encode("utf-8"))
    return {key: provenance.get(key) for key in ("commit", "dirty", "diff_sha256", "untracked")} | {
        "diff_file": WORKTREE_DIFF if provenance.get("dirty") else None}


def refuse_dirty_tree(provenance: dict, allow_dirty: bool) -> None:
    """A live run from uncommitted code is refused unless explicitly allowed (I-9)."""
    if provenance.get("dirty") and not allow_dirty:
        raise SystemExit("The working tree has uncommitted changes, so this run could not be attributed "
                         "to a commit. Commit them, or pass --allow-dirty to record the difference with the run.")
TIMEOUT_PER_PROMPT = 600  # heavy-tier tasks may make 3 execute attempts (2 repairs)
EXIT_SUCCESS = 0
EXIT_CANCELLED = 1
EXIT_UNCONFIRMED = 2
EXIT_WAITING_INPUT = 3
EXIT_HARNESS_ERROR = 4  # a model call failed (provider/transport); not a model outcome


def load_manifest(category_filter=None):
    entries = []
    cats = set()
    if category_filter:
        for c in str(category_filter).split(","):
            c = c.strip()
            if c:
                cats.add(c)
                if c.isdigit():
                    cats.add(f"{int(c):02d}")

    with open(MANIFEST_PATH, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            if cats:
                entry_cat = entry.get("category", "")
                entry_id_prefix = entry["id"][:2]
                entry_num_str = str(int(entry_id_prefix)) if entry_id_prefix.isdigit() else ""
                if not (entry_cat in cats or entry_id_prefix in cats or entry_num_str in cats):
                    continue
            entries.append(entry)
    return entries


HARNESS_MEMORY_MB = 4096  # one harness process tree (harness + its sandboxed programs)


class _Containment:
    """Bounds one harness process tree so no prompt can exhaust the machine (run
    20261001-154533 froze the evaluator's PC at 100% CPU / 80% memory) and measures
    it, so a leak shows up as a number in result.json instead of a frozen console.

    Windows: a Job Object with a job memory cap, below-normal priority, and
    kill-on-close, so every process the harness started dies with it (even if the
    runner itself is killed). The harness starts suspended and is resumed only once
    it is in the job, so nothing it starts escapes. POSIX: an address-space cap, a
    lowered priority and a new session, killed as a group (sandboxed programs run in
    sessions of their own and are bounded by their own CPU-time limit). Peak memory
    comes from the job accounting (Windows) or the child's rusage (POSIX)."""

    def __init__(self, memory_mb: int):
        self.limit_bytes = memory_mb * 1024 * 1024
        self.job = None
        self.peak_bytes: int | None = None

    def popen_kwargs(self) -> dict:
        if os.name == "nt":
            from pdl_taskmaster.verification import sandbox as sb

            flags = subprocess.CREATE_NEW_PROCESS_GROUP | sb.BELOW_NORMAL_PRIORITY_CLASS
            self.job = self._create_job()
            if self.job is not None:
                flags |= sb.CREATE_SUSPENDED  # resumed by attach() once inside the job
            return {"creationflags": flags}
        limit = self.limit_bytes

        def _limit():
            try:
                resource.setrlimit(resource.RLIMIT_AS, (limit, limit))
            except (ValueError, OSError):  # e.g. a lower hard limit already set by the shell
                pass
            os.nice(5)

        return {"start_new_session": True, "preexec_fn": _limit}

    def _create_job(self):
        import ctypes

        from pdl_taskmaster.verification import sandbox as sb

        kernel32 = sb.kernel32()
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None
        info = sb.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = (sb.JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE | sb.JOB_OBJECT_LIMIT_JOB_MEMORY
                                                 | sb.JOB_OBJECT_LIMIT_PRIORITY_CLASS)
        info.BasicLimitInformation.PriorityClass = sb.BELOW_NORMAL_PRIORITY_CLASS
        info.JobMemoryLimit = self.limit_bytes
        if not kernel32.SetInformationJobObject(job, sb.JobObjectExtendedLimitInformation, ctypes.byref(info),
                                                ctypes.sizeof(info)):
            kernel32.CloseHandle(job)
            return None
        return job

    def attach(self, proc: subprocess.Popen) -> None:
        """Windows: put the suspended harness into the job, then resume it. If the
        job refuses it, it runs uncontained (killed with taskkill /T on timeout)."""
        if os.name != "nt" or self.job is None:
            return
        from pdl_taskmaster.verification import sandbox as sb

        if not sb.kernel32().AssignProcessToJobObject(self.job, int(proc._handle)):
            self.close()
        if not sb.resume_process(proc):
            proc.kill()
            self.close()
            raise OSError("could not resume the suspended harness process")

    def wait(self, proc: subprocess.Popen, timeout: float) -> int:
        """Wait for the harness to exit (subprocess.TimeoutExpired past the timeout)."""
        if os.name == "nt":
            return proc.wait(timeout=timeout)
        deadline = time.monotonic() + timeout
        while True:
            pid, status, usage = os.wait4(proc.pid, os.WNOHANG)
            if pid:
                # ru_maxrss is in KiB on Linux and in bytes on macOS.
                self.peak_bytes = usage.ru_maxrss * (1 if sys.platform == "darwin" else 1024)
                proc.returncode = os.waitstatus_to_exitcode(status)
                return proc.returncode
            if time.monotonic() >= deadline:
                raise subprocess.TimeoutExpired(proc.args, timeout)
            time.sleep(0.05)

    def kill(self, proc: subprocess.Popen) -> None:
        """Kill the harness and everything it started (sandbox programs, workers)."""
        if os.name == "nt":
            if self.job is None:
                try:
                    subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True, timeout=30)
                except (OSError, subprocess.TimeoutExpired):
                    pass
        else:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
        self.close()
        try:
            proc.kill()
        except OSError:
            pass

    def close(self) -> None:
        """Read the job's peak memory, then close it: kill-on-close ends any process
        the harness left behind."""
        if self.job is None:
            return
        import ctypes

        from pdl_taskmaster.verification import sandbox as sb

        kernel32 = sb.kernel32()
        info = sb.JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        if kernel32.QueryInformationJobObject(self.job, sb.JobObjectExtendedLimitInformation, ctypes.byref(info),
                                              ctypes.sizeof(info), None):
            self.peak_bytes = int(info.PeakJobMemoryUsed)
        kernel32.CloseHandle(self.job)
        self.job = None

    @property
    def peak_mb(self) -> float | None:
        return None if self.peak_bytes is None else round(self.peak_bytes / (1024 * 1024), 1)

    @property
    def limit_reached(self) -> bool:
        return self.peak_bytes is not None and self.peak_bytes >= 0.95 * self.limit_bytes


def run_with_deadline(cmd, stdin_text, timeout, stdout_path, stderr_path, *, cwd=None, env=None,
                      memory_mb=HARNESS_MEMORY_MB):
    """Run one prompt with a hard deadline, contained (see _Containment). Output
    goes straight to files, so no pipe can keep the runner waiting after a kill
    (subprocess.run with capture_output can block on Windows when a grandchild
    still holds the pipes), and progress is on disk while the run is live. On
    timeout the whole process tree is killed. Returns (exit_code, timed_out,
    containment)."""
    containment = _Containment(memory_mb)
    with open(stdout_path, "w", encoding="utf-8", errors="replace") as out, \
            open(stderr_path, "w", encoding="utf-8", errors="replace") as err:
        try:
            proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True,
                                    encoding="utf-8", errors="replace", cwd=cwd, env=env,
                                    **containment.popen_kwargs())
        except BaseException:
            containment.close()
            raise
        containment.attach(proc)
        try:
            try:
                proc.stdin.write(stdin_text)
                proc.stdin.close()
            except OSError:  # the harness exited before reading its input
                pass
            exit_code = containment.wait(proc, timeout)
            containment.close()
            return exit_code, False, containment
        except subprocess.TimeoutExpired:
            containment.kill(proc)
            try:
                proc.wait(timeout=10)
            except (subprocess.TimeoutExpired, ChildProcessError):
                pass
            return -1, True, containment


HANG_DUMP_HEADER = "Timeout ("  # faulthandler's dump from the harness exit watchdog (host/cli.py)


def harness_hung(stderr: str) -> bool:
    return any(line.startswith(HANG_DUMP_HEADER) and line.rstrip().endswith(")!")
               for line in (stderr or "").splitlines())


def harness_fault(containment: _Containment, stderr: str) -> str | None:
    """A fault of the harness process itself, reported as such and never as a model
    outcome, whatever the exit code says: its tree used the whole memory allowance
    (the job's peak, or a MemoryError raised in the harness: a sandboxed program's
    own MemoryError is captured by the harness and never reaches this stderr), or
    it hung after the session ended (the exit watchdog's stack dump)."""
    if containment.limit_reached or any(line.startswith("MemoryError") for line in (stderr or "").splitlines()):
        return "HARNESS_MEMORY_LIMIT"
    if harness_hung(stderr):
        return "HARNESS_HANG"
    return None


def harness_error_record(stderr: str) -> dict | None:
    """The structured record the harness writes when a model call fails
    ("[harness-error] {json}" on stderr): category, operation, HTTP status, and
    each provider's own error message."""
    for line in reversed((stderr or "").splitlines()):
        if line.startswith("[harness-error] "):
            try:
                return json.loads(line[len("[harness-error] "):])
            except ValueError:
                return {"category": "HARNESS_EXCEPTION", "message": line[:2000]}
    return None


def effective_reasoning(model, reasoning_effort, reasoning_ops=()):
    """The reasoning effort each operation runs at, resolved exactly as the harness
    resolves it (model_classification.resolve_reasoning), for RUN_META."""
    from pdl_taskmaster.runtime.model_classification import resolve_reasoning

    by_operation = {key.strip(): value.strip().lower()
                    for key, _, value in (op.partition("=") for op in reasoning_ops or () if "=" in op)}
    default, mapping = resolve_reasoning(model, reasoning_effort, by_operation)
    return {"default": default, "by_operation": mapping}


def build_harness_command(prompt_file, session_id, transcript_path, session_dir, model, reasoning_effort,
                          reasoning_ops=(), run_settings=None):
    """The exact harness command line for one prompt. With no reasoning effort the
    harness's per-model default applies (ADR-0022), as in a live session."""
    reasoning_args = [arg for op in reasoning_ops for arg in ("--api-reasoning-operation", op)]
    if reasoning_effort is not None:
        reasoning_args = ["--api-reasoning-effort", reasoning_effort, *reasoning_args]
    settings = run_settings or {}
    setting_args = []
    for flag, key in (("--max-output-tokens", "max_output_tokens"), ("--max-repairs", "max_repairs"),
                      ("--api-providers", "providers")):
        if settings.get(key) is not None:
            setting_args += [flag, str(settings[key])]
    if settings.get("draft_execute"):
        setting_args.append("--draft-execute")
    if settings.get("route") != "control" and settings.get("tier_d1") is not None:
        # Always explicit: the harness's own default is on, so leaving the flag out does not mean off.
        setting_args.append("--tier-d1" if settings["tier_d1"] else "--no-tier-d1")
    if settings.get("sandbox"):
        setting_args += ["--sandbox", settings["sandbox"]]
    if settings.get("route") == "unconfirmed":
        setting_args.append("--no-review")
    if settings.get("theme"):
        setting_args += ["--theme", settings["theme"]]
    if settings.get("user_color"):
        setting_args += ["--user-color", settings["user_color"]]
    if settings.get("assistant_color"):
        setting_args += ["--assistant-color", settings["assistant_color"]]
    module = "pdl_taskmaster.host.control_cli" if settings.get("route") == "control" else "pdl_taskmaster.host.cli"
    cmd = [
        sys.executable, "-m", module,
        "--non-interactive",
        "--exit-on-close",
        "--dev",
        "--new-session",
        "--session-id", session_id,
        "--transcript", str(transcript_path),
        "--workspace-root", str(session_dir),
        "--workdir", str(session_dir),
        "--model", model,
        *reasoning_args,
        *setting_args,
        "--api-structured-output",
        "--prompt-file", str(prompt_file),
    ]
    return cmd


def run_single_prompt(entry, run_dir, model, reasoning_effort, timeout, repeat_index=None, reasoning_ops=(),
                      run_settings=None, memory_mb=HARNESS_MEMORY_MB):
    prompt_id = entry["id"]
    prompt_file = PROMPTS_DIR / entry["file"]
    safe_name = f"{prompt_id}_{prompt_file.stem}" + (f"_r{repeat_index}" if repeat_index else "")
    result_dir = run_dir / "results" / safe_name
    result_dir.mkdir(parents=True, exist_ok=True)

    session_id = f"catalogue-{prompt_id}-{int(time.time())}" + (f"-r{repeat_index}" if repeat_index else "")
    transcript_path = result_dir / "transcript.txt"
    session_dir = result_dir / "session"
    session_dir.mkdir(exist_ok=True)

    repl_input = "/confirm\n" * 5
    cmd = build_harness_command(prompt_file, session_id, transcript_path, session_dir, model, reasoning_effort,
                                reasoning_ops, run_settings)

    start_time = time.monotonic()
    start_ts = datetime.now(timezone.utc).isoformat()

    stdout_path, stderr_path = result_dir / "stdout.txt", result_dir / "stderr.txt"
    exit_code, timed_out, containment = run_with_deadline(
        cmd,
        repl_input,
        timeout,
        stdout_path,
        stderr_path,
        cwd=str(PDLT_TEST_ROOT),
        env={**os.environ, "PYTHONPATH": str(PDLT_TEST_ROOT / "src"), "PYTHONIOENCODING": "utf-8"},
        memory_mb=memory_mb,
    )
    stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
    stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
    if timed_out:
        stderr += f"\n[RUNNER] TIMEOUT after {timeout}s (process tree killed)"
        try:
            stderr_path.write_text(stderr, encoding="utf-8")
        except OSError:  # Windows: a killed process can hold the file a moment longer
            pass

    elapsed = time.monotonic() - start_time

    for path, text in ((stdout_path, stdout), (stderr_path, stderr)):
        if not text:
            try:
                path.unlink(missing_ok=True)
            except OSError:  # Windows: still open in a process that is being torn down
                pass

    fault = harness_fault(containment, stderr)
    if fault:
        verdict = fault
    elif timed_out:
        verdict = "TIMEOUT"
    elif exit_code == EXIT_SUCCESS:
        verdict = "CLOSED_SUCCESS"
    elif exit_code == EXIT_CANCELLED:
        verdict = "CLOSED_CANCELLED"
    elif exit_code == EXIT_HARNESS_ERROR:
        verdict = "HARNESS_ERROR"
    elif exit_code == EXIT_WAITING_INPUT:
        verdict = "WAITING_INPUT"
    elif exit_code == EXIT_UNCONFIRMED:
        verdict = "UNCONFIRMED_GATE"
    else:
        verdict = f"EXIT_{exit_code}"

    ground_truth_check = None
    if entry.get("solution_file") and entry["ground_truth_status"] == "verified":
        sol_path = PROMPTS_DIR / entry["solution_file"]
        if sol_path.exists():
            solution = json.loads(sol_path.read_text(encoding="utf-8-sig"))
            ground_truth_check = {
                "solution_file": entry["solution_file"],
                "expected_behavior": solution.get("expected_behavior"),
                "polarity": solution.get("polarity"),
                "note": "Ground truth available - manual or automated comparison required post-run",
            }

    if timed_out:
        verified = entry.get("ground_truth_status") == "verified"
        grade = {"grade": graders.FAIL if verified else graders.NA, "reason": "timeout"}
    else:
        grade = graders.grade(entry, result_dir, PROMPTS_DIR)

    result = {
        "id": prompt_id,
        "category": entry["category"],
        "file": entry["file"],
        "difficulty": entry["difficulty"],
        "expected_routing": entry["expected_routing"],
        "expected_stage": entry["expected_stage"],
        "ground_truth_status": entry["ground_truth_status"],
        "verdict": verdict,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "elapsed_seconds": round(elapsed, 2),
        "harness_peak_memory_mb": containment.peak_mb,
        "start_time": start_ts,
        "session_id": session_id,
        "transcript_file": str(transcript_path.relative_to(run_dir)),
        "ground_truth_check": ground_truth_check,
        "ground_truth_grade": grade,
        "pdl_rules_stressed": entry.get("pdl_rules_stressed", []),
        "tags": entry.get("tags", []),
        "regression_ref": entry.get("regression_ref"),
        # Evaluator-only context from the manifest; never sent to the harness.
        "tester_note": entry.get("tester_note"),
        "multi_turn_script": entry.get("multi_turn_script"),
        "model_calls": call_accounting(result_dir),
        "repeat": repeat_index,
        "harness_error": harness_error_record(stderr),
    }

    (result_dir / "result.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def call_accounting(result_dir: Path) -> dict:
    """Model calls a run made, counted from its own events (wire retries included),
    so harness conditions with more repairs are compared at equal cost."""
    by_operation: dict[str, int] = {}
    attempts = None
    echo = None  # the last plan's PLAN_PROMPT_ECHO (telemetry)
    repairs = 0
    for events in Path(result_dir).rglob("events.jsonl"):
        for line in events.read_text(encoding="utf-8", errors="replace").splitlines():
            if '"VERIFICATION_REPAIR"' in line:
                repairs += 1
            if '"PLAN_PROMPT_ECHO"' in line:
                try:
                    echo = json.loads(line).get("payload")
                except ValueError:
                    pass
            if '"MODEL_OUTPUT_RECORDED"' in line or '"EXECUTION_ATTEMPTS"' in line:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get("kind") == "MODEL_OUTPUT_RECORDED":
                    op = event.get("payload", {}).get("operation", "UNKNOWN")
                    by_operation[op] = by_operation.get(op, 0) + 1
                elif event.get("kind") == "EXECUTION_ATTEMPTS":
                    attempts = event.get("payload")
    return {"total": sum(by_operation.values()), "by_operation": by_operation, "repairs": repairs,
            "execution_attempts": attempts, "plan_echo": echo,
            **token_usage(result_dir)}


def _first(value, key):
    if isinstance(value, dict):
        if key in value:
            return value[key]
        value = list(value.values())
    if isinstance(value, list):
        for item in value:
            found = _first(item, key)
            if found is not None:
                return found
    return None


def is_execute_operation(operation: str) -> bool:
    """The model call that produces the deliverable: EXECUTE (confirmed routes), EXECUTE_UNCONFIRMED, or the control's one call."""
    return operation in ("EXECUTE", "EXECUTE_UNCONFIRMED", "CONTROL_EXECUTE")


def token_usage(result_dir: Path) -> dict:
    """Output and reported reasoning tokens, summed per operation. Some providers
    report no reasoning split for some operations (EXECUTE on gpt-oss: 0 reported
    while ~30K hidden tokens are billed as output, run 215232), so output tokens
    are the effort a run actually got, whatever the requested label.

    An observation record is one REPL turn and lists every call of that turn, so
    every call counts. (Reading only the first call of a record, as this once did,
    dropped all of an unconfirmed run's EXECUTE tokens.) The control writes its one
    call's tokens into its event log instead of an observation record."""
    reasoning: dict[str, int] = {}
    output: dict[str, int] = {}
    inputs: dict[str, int] = {}
    cached: dict[str, int] = {}

    def add(operation, usage) -> None:
        if not isinstance(operation, str) or not isinstance(usage, dict):
            return
        for totals, key in ((reasoning, "reasoning_tokens"), (output, "output_tokens"), (inputs, "input_tokens"),
                            (cached, "cached_tokens")):
            if isinstance(usage.get(key), (int, float)):
                totals[operation] = totals.get(operation, 0) + int(usage[key])

    for path in Path(result_dir).rglob("observations/*.jsonl"):
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            if '"reasoning_tokens"' not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            calls = record.get("calls") if isinstance(record, dict) else None
            if isinstance(calls, list):
                for call in calls:
                    if isinstance(call, dict):
                        add(call.get("operation"), call.get("usage"))
            else:  # an older record shape: one operation and its usage somewhere inside
                add(_first(record, "operation"), _first(record, "usage"))
    if not output:
        for path in Path(result_dir).rglob("events.jsonl"):
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if '"CONTROL_EXECUTE"' not in line:
                    continue
                try:
                    payload = json.loads(line).get("payload") or {}
                except ValueError:
                    continue
                add(payload.get("operation"), payload)
    return {"reasoning_tokens": reasoning, "output_tokens": output, "input_tokens": inputs, "cached_tokens": cached}


def stage_pass(r):
    """The run reached the manifest's expected stage."""
    exp = r.get("expected_stage", "CLOSED_SUCCESS")
    if exp == "WAITING_INPUT":
        return r.get("verdict") in {"WAITING_INPUT", "CLOSED_SUCCESS"}
    return r.get("verdict") == exp


def gt_grade(r):
    return (r.get("ground_truth_grade") or {}).get("grade", graders.NA)


HOLD_VERDICT = "UNCONFIRMED_GATE"  # exit 2: a gate left for a human (ADR-0019; D3 holds)
ADVERSARIAL_CATEGORY = "adversarial_and_injection"


def outcome_class(r):
    """One outcome per result (TARGET_ARCHITECTURE I-11; LEDGER L49d, D3).

    PASS: the expected stage and a grader PASS. PENDING: the expected stage and a
    MANUAL grade awaiting a human (FA2). UNGRADED: the expected stage with no grader
    (N/A); nothing judged the deliverable, so it is never a pass. HELD: a gate left for
    a human (exit 2) where the manifest does not expect one; never a pass. FAIL: the rest.
    """
    if r.get("verdict") == HOLD_VERDICT and r.get("expected_stage") != HOLD_VERDICT:
        return "HELD"
    if not stage_pass(r):
        return "FAIL"
    grade = gt_grade(r)
    if grade == graders.PASS:
        return "PASS"
    if grade == graders.MANUAL:
        return "PENDING"
    if grade == graders.NA:
        return "UNGRADED"
    return "FAIL"


def is_prompt_pass(r):
    """The expected stage and a grader PASS. An ungraded (N/A) or held result is not a
    pass, and neither is MANUAL: it awaits the GOAL.md Step 5 human check (pending)."""
    return outcome_class(r) == "PASS"


def is_prompt_pass_legacy(r):
    """The counting before L49d (2026-10-05): an ungraded stage match counted as a pass.
    Reported beside the current counting, never instead of it."""
    return stage_pass(r) and gt_grade(r) in {graders.PASS, graders.NA}


def is_prompt_pending(r):
    """Expected stage with a MANUAL ground truth: neither passed nor failed until a
    human checks it."""
    return outcome_class(r) == "PENDING"


def is_prompt_ungraded(r):
    return outcome_class(r) == "UNGRADED"


def is_prompt_held(r):
    return outcome_class(r) == "HELD"


def is_prompt_fail(r):
    """A missed stage, a FAIL or a grader ERROR. Fail-fast, known regressions and the
    failure list read this."""
    return outcome_class(r) == "FAIL"


def stops_fail_fast(r):
    """--fail-fast stops on a failure, and on a hold outside the adversarial category
    (a false hold); an adversarial prompt's hold is a containment outcome (D3)."""
    return is_prompt_fail(r) or (is_prompt_held(r) and r.get("category") != ADVERSARIAL_CATEGORY)


def outcome_label(r):
    return outcome_class(r)


def outcome_counts(results):
    """Counts per outcome, with the old counting beside them (TARGET_ARCHITECTURE I-11)."""
    counts = {name.lower(): 0 for name in ("PASS", "FAIL", "PENDING", "UNGRADED", "HELD")}
    for r in results:
        counts[outcome_class(r).lower()] += 1
    counts["total"] = len(results)
    counts["legacy_pass"] = sum(1 for r in results if is_prompt_pass_legacy(r))
    return counts


def format_counts(counts) -> str:
    """One line for a report: the current pass count beside the old counting."""
    n = counts["total"]
    return (f"pass {counts['pass']}/{n} (old counting {counts['legacy_pass']}/{n}); "
            f"fail {counts['fail']}, pending {counts['pending']}, ungraded {counts['ungraded']}, held {counts['held']}")


def generate_scoreboard(results, run_dir, run_meta):
    total = len(results)
    by_verdict = {}
    by_category = {}
    by_difficulty = {}
    regressions_hit = []

    for r in results:
        v = r["verdict"]
        by_verdict[v] = by_verdict.get(v, 0) + 1

        cat = r["category"]
        if cat not in by_category:
            by_category[cat] = {"total": 0, "pass": 0, "fail": 0, "pending": 0, "ungraded": 0, "held": 0}
        by_category[cat]["total"] += 1
        is_pass = is_prompt_pass(r)
        by_category[cat][outcome_label(r).lower()] += 1

        d = r["difficulty"]
        if d not in by_difficulty:
            by_difficulty[d] = {"total": 0, "pass": 0}
        by_difficulty[d]["total"] += 1
        if is_pass:
            by_difficulty[d]["pass"] += 1

        if r.get("regression_ref") and is_prompt_fail(r):
            regressions_hit.append({
                "id": r["id"], "regression_ref": r["regression_ref"], "verdict": v,
            })

    passed = sum(1 for r in results if is_prompt_pass(r))
    pending = sum(1 for r in results if is_prompt_pending(r))
    failed = sum(1 for r in results if is_prompt_fail(r))
    ungraded = sum(1 for r in results if is_prompt_ungraded(r))
    held = sum(1 for r in results if is_prompt_held(r))
    legacy_passed = sum(1 for r in results if is_prompt_pass_legacy(r))
    pass_rate = (passed / total * 100) if total > 0 else 0
    decided = passed + failed
    grades = [(r, (r.get("ground_truth_grade") or {}).get("grade", graders.NA)) for r in results]
    ground_truth = {
        g: sum(1 for _, x in grades if x == g)
        for g in (graders.PASS, graders.FAIL, graders.MANUAL, "ERROR")
    }
    false_positives = [
        {"id": r["id"], "reason": r["ground_truth_grade"].get("reason")}
        for r, g in grades if g == graders.FAIL and stage_pass(r)
    ]
    manual = [r["id"] for r, g in grades if g == graders.MANUAL]
    total_time = sum(r["elapsed_seconds"] for r in results)
    calls = [(r.get("model_calls") or {}) for r in results]
    model_calls = {
        "total": sum(c.get("total", 0) for c in calls),
        "execute": sum(n for c in calls for op, n in (c.get("by_operation") or {}).items() if is_execute_operation(op)),
        "repairs": sum(c.get("repairs", 0) for c in calls),
    }
    model_calls["execute_reasoning_tokens"] = sum(
        n for c in calls for op, n in (c.get("reasoning_tokens") or {}).items() if is_execute_operation(op))
    model_calls["execute_output_tokens"] = sum(
        n for c in calls for op, n in (c.get("output_tokens") or {}).items() if is_execute_operation(op))
    repeat_pass_rates: dict = {}
    if any(r.get("repeat") for r in results):
        for r in results:
            rate = repeat_pass_rates.setdefault(r["id"], {"runs": 0, "passed": 0})
            rate["runs"] += 1
            rate["passed"] += int(is_prompt_pass(r))
    echoes = [c.get("plan_echo") for c in calls if c.get("plan_echo")]
    plan_echo = {
        "plans": len(echoes),
        "identical": sorted(r["id"] for r, c in zip(results, calls) if (c.get("plan_echo") or {}).get("identical")),
        "copied_80pct": sum(1 for e in echoes if e.get("copied_line_ratio", 0) >= 0.8),
    }

    scoreboard = {
        "run_id": run_meta["run_id"],
        "timestamp": run_meta["start_time"],
        "route": run_meta.get("route", "confirmed"),
        "model": run_meta["model"],
        "reasoning_effort": run_meta["reasoning_effort"],
        "total_prompts": total,
        "passed": passed,
        "failed": failed,
        "pending_human_check": pending,
        "ungraded": ungraded,
        "held": held,
        "legacy_passed": legacy_passed,
        "legacy_pass_rate_pct": round(legacy_passed / total * 100, 1) if total else 0.0,
        "stage_passed": sum(1 for r in results if stage_pass(r)),
        "manual_spot_check": manual,
        "pass_rate_pct": round(pass_rate, 1),
        "decided_pass_rate_pct": round(passed / decided * 100, 1) if decided else 0.0,
        "total_elapsed_seconds": round(total_time, 1),
        "model_calls": model_calls,
        "plan_echo": plan_echo,
        "repeat_pass_rates": repeat_pass_rates,
        "ground_truth": ground_truth,
        "false_positives": false_positives,
        "by_verdict": by_verdict,
        "by_category": by_category,
        "by_difficulty": by_difficulty,
        "regressions_hit": regressions_hit,
        "failures": [
            {"id": r["id"], "category": r["category"], "verdict": r["verdict"],
             "elapsed": r["elapsed_seconds"]}
            for r in results if is_prompt_fail(r)
        ],
    }

    (run_dir / "SCOREBOARD.json").write_text(
        json.dumps(scoreboard, indent=2), encoding="utf-8"
    )

    # Markdown scoreboard
    lines = [
        f"# PDLt Catalogue Run - {scoreboard['run_id']}",
        "",
        f"**Model:** `{scoreboard['model']}`  ",
        f"**Reasoning Effort:** `{scoreboard['reasoning_effort']}`  ",
        f"**Timestamp:** {scoreboard['timestamp']}  ",
        f"**Route:** `{scoreboard.get('route', 'confirmed')}`  ",
        f"**Total Time:** {scoreboard['total_elapsed_seconds']:.1f}s  ",
        "",
        "---",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total Prompts | {scoreboard['total_prompts']} |",
        f"| Passed | {scoreboard['passed']} |",
        f"| Failed | {scoreboard['failed']} |",
        f"| Awaiting human check (MANUAL; not a pass) | {scoreboard['pending_human_check']} |",
        f"| Ungraded (expected stage, no grader; not a pass) | {scoreboard['ungraded']} |",
        f"| Held for a human (exit 2; not a pass) | {scoreboard['held']} |",
        f"| **Pass Rate** | **{scoreboard['pass_rate_pct']}%** |",
        f"| Pass rate, old counting (ungraded counted as a pass) | {scoreboard['legacy_pass_rate_pct']}% "
        f"({scoreboard['legacy_passed']}) |",
        f"| Pass rate over decided prompts (excluding MANUAL) | {scoreboard['decided_pass_rate_pct']}% |",
        f"| Model calls (total / EXECUTE / repairs) | {scoreboard['model_calls']['total']} / "
        f"{scoreboard['model_calls']['execute']} / {scoreboard['model_calls']['repairs']} |",
        f"| EXECUTE output tokens / provider-reported reasoning (all prompts) | "
        f"{scoreboard['model_calls']['execute_output_tokens']} / {scoreboard['model_calls']['execute_reasoning_tokens']} |",
        f"| Plans identical to prompt / >=80% copied (of plans) | {len(scoreboard['plan_echo']['identical'])} / "
        f"{scoreboard['plan_echo']['copied_80pct']} (of {scoreboard['plan_echo']['plans']}) |",
        "",
    ]
    if scoreboard["repeat_pass_rates"]:
        lines += ["## Pass Rate per Prompt (repeats)", "", "| Prompt | Passed | Runs |", "|--------|--------|------|"]
        lines += [f"| {pid} | {rate['passed']} | {rate['runs']} |"
                  for pid, rate in scoreboard["repeat_pass_rates"].items()]
        lines.append("")
    lines += [
        "---",
        "",
        "## By Category",
        "",
        "| Category | Total | Pass | Fail | Pending | Ungraded | Held | Rate | Rate, old counting |",
        "|----------|-------|------|------|---------|----------|------|------|--------------------|",
    ]
    for cat in sorted(scoreboard["by_category"].keys()):
        c = scoreboard["by_category"][cat]
        rate = (c["pass"] / c["total"] * 100) if c["total"] > 0 else 0
        old_rate = ((c["pass"] + c.get("ungraded", 0)) / c["total"] * 100) if c["total"] > 0 else 0
        lines.append(f"| {cat} | {c['total']} | {c['pass']} | {c['fail']} | {c.get('pending', 0)} | "
                     f"{c.get('ungraded', 0)} | {c.get('held', 0)} | {rate:.0f}% | {old_rate:.0f}% |")

    lines += ["", "---", "", "## Ground Truth (evaluation-plane graders)", "",
              "| Grade | Count |", "|-------|-------|"]
    for g, n in scoreboard["ground_truth"].items():
        lines.append(f"| {g} | {n} |")
    lines.append(f"| **False positives** (stage pass, wrong answer) | **{len(scoreboard['false_positives'])}** |")
    for fp in scoreboard["false_positives"]:
        lines.append(f"|  - {fp['id']} | {fp['reason']} |")

    lines += ["", "---", "", "## By Difficulty", "",
              "| Difficulty | Total | Pass | Rate |",
              "|-----------|-------|------|------|"]
    for d in ["easy", "medium", "hard", "adversarial"]:
        if d in scoreboard["by_difficulty"]:
            dd = scoreboard["by_difficulty"][d]
            rate = (dd["pass"] / dd["total"] * 100) if dd["total"] > 0 else 0
            lines.append(f"| {d} | {dd['total']} | {dd['pass']} | {rate:.0f}% |")

    if scoreboard["failures"]:
        lines += ["", "---", "", "## Failures", "",
                  "| ID | Category | Verdict | Time (s) |",
                  "|----|----------|---------|----------|"]
        for f in scoreboard["failures"]:
            lines.append(f"| {f['id']} | {f['category']} | {f['verdict']} | {f['elapsed']:.1f} |")

    if scoreboard["regressions_hit"]:
        lines += ["", "---", "", "## KNOWN REGRESSIONS HIT", "",
                  "| ID | Regression Ref | Verdict |",
                  "|----|---------------|---------|"]
        for r in scoreboard["regressions_hit"]:
            lines.append(f"| {r['id']} | {r['regression_ref']} | {r['verdict']} |")

    lines += ["", "---", "", "## Per-Prompt Results", "",
              "| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |",
              "|----|----------|-----------|---------|--------------|-------------|----------|"]
    for r in results:
        icon = outcome_label(r)
        lines.append(
            f"| {icon} {r['id']} | {r['category']} | {r['difficulty']} "
            f"| {r['verdict']} | {gt_grade(r)} | {(r.get('model_calls') or {}).get('total', '')} | {r['elapsed_seconds']:.1f} |"
        )

    (run_dir / "SCOREBOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return scoreboard


def regrade_run(run_dir: Path) -> int:
    """Apply the current graders to a finished run (no model calls)."""
    manifest = {e["id"]: e for e in load_manifest()}
    results = []
    for result_file in sorted((run_dir / "results").glob("*/result.json")):
        result = json.loads(result_file.read_text(encoding="utf-8"))
        entry = manifest[result["id"]]
        if not result.get("timed_out"):
            result["ground_truth_grade"] = graders.grade(entry, result_file.parent, PROMPTS_DIR)
        result["tester_note"] = entry.get("tester_note")
        result["multi_turn_script"] = entry.get("multi_turn_script")
        result["model_calls"] = call_accounting(result_file.parent)
        result_file.write_text(json.dumps(result, indent=2), encoding="utf-8")
        results.append(result)
    run_meta = json.loads((run_dir / "RUN_META.json").read_text(encoding="utf-8"))
    scoreboard = generate_scoreboard(results, run_dir, run_meta)
    for r in results:
        icon = outcome_label(r)
        grade = r["ground_truth_grade"]
        print(f"{icon} {r['id']:6s} {r['verdict']:16s} gt={gt_grade(r):7s} {grade.get('reason', '')}")
    print(f"Pass Rate: {scoreboard['pass_rate_pct']}% ({scoreboard['passed']}/{scoreboard['total_prompts']}; "
          f"{scoreboard['pending_human_check']} awaiting a human check); "
          f"stage only {scoreboard['stage_passed']}/{scoreboard['total_prompts']}; "
          f"false_positives={len(scoreboard['false_positives'])}")
    return 1 if scoreboard["false_positives"] else 0


def _utf8_console() -> None:
    """Provider messages and grader reasons can hold any character; a Windows console
    or redirected output would otherwise use the ANSI code page and raise
    UnicodeEncodeError mid-run."""
    if sys.platform == "win32":
        for stream in (sys.stdout, sys.stderr):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, ValueError):
                pass


def main():
    _utf8_console()
    parser = argparse.ArgumentParser(
        description="PDLt Prompt Catalogue Test Runner - no retries, no shortcuts"
    )
    parser.add_argument("--model", default="nvidia/nemotron-3-super-120b-a12b:free",
                        help="Model to test (default: nvidia/nemotron-3-super-120b-a12b:free)")
    parser.add_argument("--reasoning", default=None,
                        choices=["none", "low", "medium", "high"],
                        help="reasoning effort for every operation (default: the harness's per-model default, "
                             "for gpt-oss high with EXECUTE=low, the same as a live session)")
    parser.add_argument("--category", default=None,
                        help="Run only a specific category (e.g. 'combinatorial_search' or '01,13,14')")
    parser.add_argument("--categories", dest="category",
                        help="Alias for --category with comma-separated list")
    parser.add_argument("--fail-fast", "--stop-on-failure", action="store_true",
                        help="Stop execution immediately upon any prompt failure")
    parser.add_argument("--prompt-id", "--id", dest="prompt_id", default=None,
                        help="Run only a specific prompt by ID (e.g. '01-02')")
    parser.add_argument("--dry-run", action="store_true",
                        help="List prompts that would be run without executing")
    parser.add_argument("--timeout", type=int, default=None,
                        help=f"Per-prompt timeout in seconds (default: {TIMEOUT_PER_PROMPT} at every effort level)")
    parser.add_argument("--reasoning-op", action="append", default=[], metavar="OP=EFFORT",
                        help="per-operation effort overriding --reasoning (repeatable), e.g. EXECUTE=high")
    parser.add_argument("--max-output-tokens", type=int, default=None, metavar="N",
                        help="output-token cap per model call, reasoning included (harness default: 16384)")
    parser.add_argument("--max-repairs", type=int, default=None, metavar="N",
                        help="EXECUTE repairs after a failed verification; 0 stops at the first failure (no retries)")
    parser.add_argument("--providers", default=None, metavar="A,B,C",
                        help="provider order for the model calls, only these are used (e.g. Cerebras,Groq,SambaNova)")
    parser.add_argument("--draft-execute", action="store_true",
                        help="run exactly one DRAFT_EXECUTE feasibility-scratchpad call before EXECUTE (A/B option)")
    parser.add_argument("--tier-d1", action=argparse.BooleanOptionalAction,
                        default=os.environ.get("PDLT_TIER_D1", "1") == "1",
                        help="Tier D1 in standard execution: feed sandbox failures back as repairs "
                             "(default: on, as the harness ships; --no-tier-d1 turns it off, PDLT_TIER_D1=0 flips the "
                             "default). Not applicable to --route control")
    parser.add_argument("--sandbox", choices=["auto", "native", "container", "audit-only"], default=None,
                        help="confinement for model-authored programs, in the harness and the graders (default: "
                             "$PDLT_SANDBOX, else auto = native); audit-only opts out of OS-native confinement")
    parser.add_argument("--harness-memory-mb", type=int, default=HARNESS_MEMORY_MB, metavar="MB",
                        help=f"memory cap for one prompt's harness process tree (default: {HARNESS_MEMORY_MB})")
    parser.add_argument("--repeat", type=int, default=1, metavar="N",
                        help="run each selected prompt N times in one run (pass rate per prompt on the scoreboard)")
    parser.add_argument("--route", choices=["confirmed", "unconfirmed", "control"], default="confirmed",
                        help="execution route: 'confirmed' (default, multi-stage with review), 'unconfirmed' (--no-review / ultrafast), or 'control' (unharnessed direct model baseline)")
    parser.add_argument("--theme", choices=THEME_NAMES, default=None,
                        help="Color theme for runner output and child process (default: $PDLT_THEME)")
    parser.add_argument("--user-color", choices=COLOR_NAMES, default=None,
                        help="Override user prompt color")
    parser.add_argument("--assistant-color", choices=COLOR_NAMES, default=None,
                        help="Override assistant response color")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="run from a working tree with uncommitted changes; the difference is stored with "
                             "the run as WORKTREE.diff (without it, such a run is refused)")
    parser.add_argument("--regrade", metavar="RUN_DIR", default=None,
                        help="re-grade a finished run with the current graders and rewrite its scoreboard")
    args = parser.parse_args()
    if args.timeout is None:
        # One deadline for every effort level: slow configurations are penalised,
        # not given more time. Per-call cost is bounded by --max-output-tokens.
        args.timeout = TIMEOUT_PER_PROMPT
    if args.regrade:
        sys.exit(regrade_run(Path(args.regrade)))

    entries = load_manifest(category_filter=args.category)
    if args.prompt_id:
        target_pids = {p.strip() for p in args.prompt_id.split(",") if p.strip()}
        entries = [e for e in entries if e["id"] in target_pids]
    if args.repeat < 1:
        parser.error("--repeat must be at least 1")
    runs = [(e, k if args.repeat > 1 else None) for e in entries for k in range(1, args.repeat + 1)]
    run_settings = {"max_output_tokens": args.max_output_tokens, "max_repairs": args.max_repairs,
                    "providers": args.providers, "draft_execute": args.draft_execute,
                    "tier_d1": args.tier_d1 and args.route != "control",  # what the child will run with
                    "sandbox": args.sandbox, "route": args.route,
                    "theme": args.theme, "user_color": args.user_color, "assistant_color": args.assistant_color}
    if args.sandbox:
        # The graders run deliverable code in this process: the same confinement.
        os.environ["PDLT_SANDBOX"] = args.sandbox

    if not entries:
        print("No prompts match the filter. Exiting.")
        sys.exit(1)

    print(f"PDLt Prompt Catalogue Test Runner")
    print(f"{'=' * 50}")
    print(f"Model:      {args.model}")
    reasoning_effective = effective_reasoning(args.model, args.reasoning, args.reasoning_op)
    print(f"Reasoning:  {args.reasoning or 'harness default'}"
          + (f" (per operation: {', '.join(args.reasoning_op)})" if args.reasoning_op else ""))
    print(f"            effective: default={reasoning_effective['default']}, "
          f"per operation={json.dumps(reasoning_effective['by_operation'])}")
    print(f"Prompts:    {len(entries)}" + (f" x {args.repeat} repeats = {len(runs)} runs" if args.repeat > 1 else ""))
    print(f"Timeout:    {args.timeout}s per prompt")
    shown = {k: v for k, v in run_settings.items() if v is not None and v is not False}
    if shown:
        print(f"Settings:   {', '.join(f'{k}={v}' for k, v in shown.items())}")
    print()

    if args.dry_run:
        print("DRY RUN - prompts that would be executed:")
        for e in entries:
            gt = "VERIFIED" if e["ground_truth_status"] == "verified" else "       "
            print(f"  {gt} {e['id']:6s} [{e['difficulty']:11s}] {e['file']}")
        n_verified = sum(1 for e in entries if e["ground_truth_status"] == "verified")
        print(f"\nVERIFIED = verified ground truth ({n_verified} prompts)")
        sys.exit(0)

    provenance = code_provenance()
    refuse_dirty_tree(provenance, args.allow_dirty)

    route_tag = args.route
    if args.draft_execute:
        route_tag += "-draft-execute"
    if run_settings["tier_d1"]:
        route_tag += "-tier-d1"
    run_id = f"run-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{route_tag}"
    run_dir = RUNS_DIR / run_id
    (run_dir / "results").mkdir(parents=True)

    run_meta = {
        "run_id": run_id,
        "start_time": datetime.now(timezone.utc).isoformat(),
        "model": args.model,
        "route": args.route,
        "reasoning_effort": args.reasoning or "harness-default",
        "reasoning_by_operation": args.reasoning_op,
        "reasoning_effective": reasoning_effective,
        "run_settings": run_settings,
        "category_filter": args.category,
        "prompt_id_filter": args.prompt_id,
        "total_prompts": len(runs),
        "repeat": args.repeat,
        "timeout_per_prompt": args.timeout,
        "harness_memory_mb": args.harness_memory_mb,
        "sandbox": args.sandbox or os.environ.get("PDLT_SANDBOX") or "auto",
        "pdlt_test_root": str(PDLT_TEST_ROOT),
        "code": record_provenance(run_dir, provenance),
        "rules": {
            "retries_allowed": 0,
            "do_overs_allowed": False,
            "non_interactive": True,
            "exit_on_close": True,
            "dev_mode": True,
            "structured_output": True,
            "gate_policy": "evaluator_confirms_via_stdin",
        },
    }
    (run_dir / "RUN_META.json").write_text(
        json.dumps(run_meta, indent=2), encoding="utf-8"
    )

    results = []
    for i, (entry, repeat_index) in enumerate(runs, 1):
        prompt_id = entry["id"]
        label = prompt_id + (f" r{repeat_index}" if repeat_index else "")
        print(f"[{i:3d}/{len(runs)}] {label:9s} {entry['category']:30s} ", end="", flush=True)
        result = run_single_prompt(entry, run_dir, args.model, args.reasoning, args.timeout, repeat_index,
                                   args.reasoning_op, run_settings, memory_mb=args.harness_memory_mb)
        results.append(result)
        icon = outcome_label(result)
        peak = result.get("harness_peak_memory_mb")
        memory = f", {peak:.0f} MB" if peak is not None else ""
        print(f"{icon} {result['verdict']:20s} gt={gt_grade(result):7s} ({result['elapsed_seconds']:.1f}s{memory})")

        if args.fail_fast and stops_fail_fast(result):
            print(f"\n[FAIL-FAST] Stopping execution immediately after failure on {prompt_id} ({result['verdict']}).")
            break

    print()
    print(f"{'=' * 50}")
    scoreboard = generate_scoreboard(results, run_dir, run_meta)
    print(f"Pass Rate: {scoreboard['pass_rate_pct']}% "
          f"({scoreboard['passed']}/{scoreboard['total_prompts']}; "
          f"{scoreboard['pending_human_check']} awaiting a human check, not counted as passes)")
    print(f"Total Time: {scoreboard['total_elapsed_seconds']:.1f}s")
    print(f"Results: {run_dir}")
    print(f"Scoreboard: {run_dir / 'SCOREBOARD.md'}")

    gt = scoreboard["ground_truth"]
    print(f"Stage only: {scoreboard['stage_passed']}/{scoreboard['total_prompts']} reached the expected stage")
    for fault, meaning in (("HARNESS_MEMORY_LIMIT", f"the harness used its whole {args.harness_memory_mb} MB allowance"),
                           ("HARNESS_HANG", "the harness did not exit after the session ended; stacks in stderr.txt")):
        ids = [r["id"] for r in results if r.get("verdict") == fault]
        if ids:
            print(f"{fault}: {len(ids)} ({meaning}; not a model outcome) - {', '.join(ids)}")
    peaks = [r["harness_peak_memory_mb"] for r in results if r.get("harness_peak_memory_mb") is not None]
    if peaks:
        print(f"Harness peak memory: max {max(peaks):.0f} MB, median {sorted(peaks)[len(peaks) // 2]:.0f} MB")
    harness_errors = [r for r in results if r.get("verdict") == "HARNESS_ERROR"]
    if harness_errors:
        print(f"HARNESS ERRORS: {len(harness_errors)} (a model call failed; not a model outcome)")
        groups: dict = {}
        for r in harness_errors:
            record = r.get("harness_error") or {}
            attempts = " | ".join(f"{a.get('provider')}: {a.get('message', '')[:160]}"
                                  for a in record.get("attempts") or []) or record.get("message", "")[:240]
            key = (record.get("category", "UNKNOWN"), record.get("operation"), record.get("status"), attempts)
            groups.setdefault(key, []).append(r["id"])
        for (category, operation, status, attempts), ids in groups.items():
            print(f"    {category} at {operation} (HTTP {status}) - {', '.join(ids)}")
            print(f"        {attempts}")
    mc = scoreboard["model_calls"]
    print(f"Model calls: {mc['total']} total, {mc['execute']} EXECUTE, {mc['repairs']} verification repairs")
    print(f"EXECUTE tokens: {mc['execute_output_tokens']} output, {mc['execute_reasoning_tokens']} reported as reasoning "
          "(hidden reasoning is billed as output when the provider reports no split)")
    pe = scoreboard["plan_echo"]
    print(f"Plan echo: {len(pe['identical'])} identical to prompt, {pe['copied_80pct']} >=80% copied (of {pe['plans']} plans)")
    print(f"Ground truth: PASS={gt['PASS']} FAIL={gt['FAIL']} MANUAL={gt['MANUAL']} "
          f"false_positives={len(scoreboard['false_positives'])}")
    for fp in scoreboard["false_positives"]:
        print(f"    FALSE POSITIVE {fp['id']}: {fp['reason']}")
    if scoreboard["repeat_pass_rates"]:
        print("Pass rate per prompt (repeats):")
        for pid, rate in scoreboard["repeat_pass_rates"].items():
            print(f"    {pid}: {rate['passed']}/{rate['runs']}")
    if scoreboard["manual_spot_check"]:
        print(f"Needs human spot check (not verified): {', '.join(scoreboard['manual_spot_check'])}")
    if scoreboard["regressions_hit"]:
        print(f"\nKNOWN REGRESSIONS HIT: {len(scoreboard['regressions_hit'])} (failed prompts the manifest tags with a past regression)")
        for r in scoreboard["regressions_hit"]:
            print(f"    {r['id']} ({r['regression_ref']}): {r['verdict']}")

    exit_code = 1 if (
        scoreboard["regressions_hit"]
        or scoreboard["false_positives"]
        or (args.fail_fast and scoreboard.get("failed", 0) > 0)
    ) else 0
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

