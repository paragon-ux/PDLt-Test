# Plan: fix 13-07, then port the viewer (PDLt-Test, branch `claude/hopeful-gauss-nw44rt`)

## Context

The first live runs (pushed by the user in commit `6685598`) gave:
- **06-04:** PASS.
- **Category 13:** 6 of 7 pass, and 13-01 is graded PASS. 13-07 fails with `WAITING_INPUT`. The manifest expects `CLOSED_SUCCESS`.
- The user mentioned a failed run in category 01, but **no category 01 run is in the pushed data**. Only `run-20260930-112405` (06-04) and `run-20260930-112451` (category 13) exist. I'll ask them to push the category 01 run so I can diagnose it, and I won't guess.

## Part 1: diagnose and fix 13-07

**What the transcript shows** (`run-20260930-112451/results/13-07_stale_knowledge_cutoff/stdout.txt`):
1. The model drafted the prompt and plan as "READ the list of winners from the 2027 Nobel Prize ceremonies…".
2. At EXECUTE it emitted `REQUEST_INPUT` ("Please provide the list of winners…"). The stage went to `WAITING_INPUT` and the process exited 3.
3. The later `ControllerError: intent_stage` lines are just the runner's extra piped `/confirm` lines hitting a waiting stage. They're harmless, and 13-06 has the same noise.

**Root cause: Phase 0 (System 1 activation route) is skipped in headless runs.**
- TARGET_ARCHITECTURE §3 Phase 0 and §5: System 1 `ActivationRoute` decides `BLOCKED_BY_HIGHER_PRIORITY` from the environment state, including `PDLT_KNOWLEDGE_CUTOFF`. The cutoff never reaches System 2.
- The host prepends `$confirm-with-pseudocode` to every message. The engine treats that as an explicit invocation and jumps straight to `_draft_initial_prompt`, so **no System 1 boundary routing ever runs**. Post-cutoff requests therefore reach System 2 as ordinary tasks.
- The cutoff state I already wired into `ActivationRouteRecipe.build_request` is correct, but unreachable.

**Fix: restore Phase 0 with System 1 only. No System 2 involvement, no new prompt text, no helpers in `api_worker.py`.**
1. `runtime/session_engine.py`: add `_s1_boundary_refusal(text) -> str | None`, called from the explicit-invocation branch of `_activation` before `_draft_initial_prompt`.
   - It runs `ActivationRouteRecipe` through `self.sys1_client`, using the recipe's own `build_request` (environment state: policy scope, offline sandbox, knowledge cutoff), `parse_response` and the existing confidence gate.
   - Only a gated `BLOCKED_BY_HIGHER_PRIORITY` produces a refusal. It goes through the existing `_refuse(..., phase="activation")`, so the outcome is `closure=REFUSED`, exit 0.
   - System 1 unavailable, low confidence, or any error falls through to the normal protocol, so behaviour never gets stricter without S1 evidence.
   - It reuses `ActivationRouteRecipe.classify_text_deterministic` for the existing environment fast path (medical scope, offline network), which no longer depends on the bootstrap call.
2. Tests (offline, fake `sys1_client`):
   - Gated BLOCKED from S1 gives a refusal, `engine.refused`, and **the S2 `model_call` is never invoked** (the fake raises if called).
   - S1 says `APPLY_PROTOCOL`, low confidence, unconfigured, or an exception: protocol proceeds and S2 is called.
   - The recipe request state contains the cutoff from `PDLT_KNOWLEDGE_CUTOFF` and the S2 request text does not (assert the cutoff string is absent from every `model_call` request).
   - The anti-overfitting scan stays green (no new vocabulary).
3. Verification: this container has no `OPENROUTER_API_KEY`, so I can't rerun. The user reruns `python run_catalogue.py --category 13`, then the full suite if green. If S1 doesn't gate 13-07 as BLOCKED, it stays a recorded diagnostic failure, and I won't tune anything to change that.

## Part 2: port the viewer

**Where it goes: the evaluation plane, not the harness package.**
- The upstream viewer reads `prompts/` for its catalogue tab. GUARD-02 says the harness package (`src/pdl_taskmaster/`) never reads `prompts/`, and the contamination scan enforces that.
- So the viewer lives at repo root as `viewer/` (`viewer/__init__.py`, `viewer/server.py`, `viewer/index.html`), launched with `python -m viewer`.
- It doesn't import any harness code; it only reads files.
- I'll drop the `pdlt viewer` subcommand and the REPL `/viewer` command for that reason, and say so.

**Adaptations to the upstream code** (`tools/viewer_server.py` and `repl_viewer.html` in the harness repo):
1. **Roots:** `REPO_ROOT` becomes the directory containing `viewer/`. The catalogue root defaults to it, and `PDLT_TEST_ROOT` is no longer needed.
2. **Session discovery:** look in `runs/live-sessions/*` (interactive sessions) **and** `catalogue-runs/run-*/results/*/session/` (runner sessions).
   - Runner workspaces are laid out as `session/W-*/turns/turn_*/…` directly under the workspace root.
   - Match them with a recursive search for `controller-state.json` and `50_execution/output/current.md`, taking the newest by mtime. This also fixes the upstream assumption that the turn is always `turn_001`.
3. **Localhost only:** bind `127.0.0.1` instead of `0.0.0.0`. The upstream server exposed session data on all interfaces, which shouldn't be the default for a local viewer.
4. **New `/api/runs` endpoint and Runs panel:** list `catalogue-runs/run-*` with scoreboard summary (pass rate, ground-truth counts, false positives) and per-prompt verdicts read from `SCOREBOARD.json` and `result.json`. Selecting a prompt shows its transcript and deliverable.
   - This is the useful view for headless runs, and it's a small addition to the ported HTML.
5. Keep the existing panels: live stage, prompt, plan, code snippet, witness, log tail, catalogue list.

**Tests:** port `tests/test_viewer_command.py` as `tests/test_viewer.py`, keeping the endpoint test for `/`, `/api/status` and `/api/catalogue`, dropping the CLI dispatch test, and adding tests for `/api/runs` and for session discovery against a temporary tree that mimics the runner layout.

**Manual verification:** start `python -m viewer --no-open` locally, `curl` the three endpoints, and confirm that a pushed catalogue run directory renders (the user's `run-20260930-112451` is a good fixture).

## Order and delivery
1. Part 1 (fix, tests, commit, push), because the user asked for the fix first.
2. Part 2 (viewer, tests, commit, push).
3. README gets two short additions: the `python -m viewer` command, and a note on the cutoff environment variable.
4. Full `pytest -q` before each push. Report what wasn't verified live: the 13-07 rerun, and the category 01 failure.