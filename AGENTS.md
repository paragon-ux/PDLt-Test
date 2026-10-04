# Agent Rules & Guidelines

## Continuity (read first, every session and after every context compaction)
- **`docs/plans/LEDGER.md` is the canonical record** of cross-cutting decisions and open items: each with its source (main chat, side chat, the user), status and link.
- **Read it before starting work.** Then read the current PR's work list it points to (for example `docs/plans/pr2-worklist.md`).
- **Update it in the same change** that settles, changes or completes an item.
- **A side-chat decision is not settled until it has a ledger row.** When two recorded decisions disagree, mark the row `conflict` and ask the user; never pick one silently.
- **Within one turn, a built-in task list is fine for progress.** The ledger and the work list are what survive compaction. An external tracker may mirror them, never replace them.

## Diagnosis and Verification Rule (CRITICAL / MANDATORY)
- **Static first.** Diagnose from the code: trace the path and cite `file:line`. Read the artifacts existing runs already recorded (`call-trace.jsonl`, `events.jsonl`, `compiled-projection.json`, `model-response.txt`). If the code determines the answer, do not reproduce it live.
- **Offline before live.** Verify host logic with the offline suite and recorded replays (`--worker recorded`). Controller transitions, exit codes, routing plumbing, grading, telemetry, docs and refactors need no API call.
- **Live only when the answer depends on what code cannot determine:**
  - what a model returns for a request, when no recorded output answers it;
  - provider behaviour: schema acceptance, routing, stalls, token reporting, latency;
  - a System 1 decision on an input it has not seen;
  - a change to what the model or provider receives, checked once before merge (trigger below).
- **The trigger for "receives".** Either of these:
  - a recorded replay misses, because the rendered prompt's hash changed (`RecordedWorker` keys on the operation plus the prompt's SHA-256 and raises `ReplayMissError`);
  - the provider-layer request changed (`providers/api_worker.py`: guidance text, effort, response format, caps, provider pinning).

  Replay alone does not cover the second: those parts are added after the prompt is hashed.
- **A static conclusion about runtime behaviour is a hypothesis.** Code can be read confidently and still not be what runs: environment variables, provider defaults, a stale install. A static claim about model or provider behaviour stays a hypothesis until a recorded artifact confirms it. Only when none exists does it justify a live run.
- **A live run answers a stated question.** Before running, write what you expect and what would falsify it. Use the smallest run that answers it, in dev mode (`--dev`), from the repository root. No generic smoke runs.
- **Label the evidence.** Every claim says how it was established: static (`file:line`), offline test, recorded artifact, or live run. Never report a static or offline result as "verified live". If a required live check can't run because `OPENROUTER_API_KEY` is unavailable, say so.

## PDL Standard Adherence
- Prompt Pseudocode MUST strictly conform to `PDL-01` through `PDL-08`.
- NO invented field schemas (`TASK:`, `OUTPUT:`, `INCLUDE:`).
- One operation per line (`PDL-02`), capitalized action verbs (`PDL-04`).
- No drafting meta-rules or deferrals in the prompt or plan bodies (`PROMPT-01`, `PDL-08`).

## Architecture & Verification Governance (ADR-0018, ADR-0019, ADR-0020)
- **Pydantic SSOT (ADR-0018)**: NEVER use heuristic regex for domain detection, witness extraction, or wire verification. All parsing and validation MUST go through strict, schema-first Pydantic models with alias coercion (`OutputVerifier`, `wire_payloads.WitnessPayload`). No problem-specific checker ships in the harness plane.
- **Autonomous Host Execution & First-Class Reasoning (GUARD-03)**:
  - When Python code or solver scripts are present, the host sandbox automatically executes them to capture stdout witnesses. NEVER emit `REQUEST_INPUT` asking the user to run code.
  - Analytical derivations, symbolic mathematics, word problems, and logical deductions are first-class deliverables (`GUARD-03`). The harness MUST NOT coerce symbolic or reasoning tasks into executable Python scripts or force models to fabricate concrete values for symbolic variables.
- **System 1 Boundary Refusal (ADR-0020, GUARD-02)**: Out-of-bounds, network-dependent, or mathematically impossible tasks MUST be intercepted and refused fail-closed by System 1 in <2s conditioned on runtime environment variables (`PDLT_SANDBOX_NETWORK`, `PDLT_POLICY_SCOPE`); the knowledge cutoff (`PDLT_KNOWLEDGE_CUTOFF`) is injected into System 1's state, never matched by a year regex. NEVER hardcode prompt-specific benchmark tokens or entity names into production regex traps.
- **Headless Automation & Exit Codes (ADR-0019)**:
  - `0`: `CLOSED_SUCCESS` (deliverable verified).
  - `0` also covers a published boundary refusal (`closure=REFUSED`, ADR-0019 amendment).
  - `1`: `CLOSED_CANCELLED` / fail-closed error.
  - `2`: `UNCONFIRMED_GATE` (execution stalled at review gate).
  - `3`: `WAITING_INPUT` (legitimate pause awaiting external input).
  - `4`: harness or provider error (`EXIT_HARNESS_ERROR`); never a protocol result.
  - `130`: interrupted by the user.
- **Catalogue Verification**: Before merging a PR that changes behaviour (what the model receives, routing, stage logic, verification or grading), run `python run_catalogue.py --fail-fast` from the repository root to check for regressions across all 16 categories. It is not a per-pass check. Never loosen `is_prompt_pass` or `graders.py` to obtain a green result.

## Post-Implementation Anti-Overfitting & Integrity Gate (MANDATORY / SSOT)
- **The Referee Invariant (GUARD-01, GUARD-04)**: The harness is strictly an objective protocol referee and governor—NEVER an AI task solver. The harness MUST NEVER:
  - Inject prescriptive algorithmic advice, search methods (e.g. MRV, backtracking, DLX), or solution hints into prompts, plans, or `CARRIED_APPROACH_SOURCES`.
  - Mechanically require specific algorithmic keywords in Plan Soundness gates.
  - Scrape deliverable text with regex to synthesize witnesses.
- **Feedback channel**: retry and lint feedback travels only through operator correction; `CARRIED_APPROACH_SOURCES` stays user-originated.
- **Mandatory Anti-Overfitting Suite**: After ANY implementation round touching prompts, gates, checkers, or session engine, you MUST execute:
  ```bash
  pytest tests/test_harness_anti_overfitting.py
  ```
  Every test must pass with zero warnings, failures, or skips.
- **Guardrail Cross-Check**: Any changes MUST strictly conform to `docs/guardrails/ANTI_OVERFITTING_AND_BENCHMARK_INTEGRITY.md` (`GUARD-01` through `GUARD-05`).
- **Integrity Over Checkmarks**: **A failed benchmark is acceptable and diagnostic of genuine model capability boundaries (e.g. `REG-011`, `REG-012`), but a gamed benchmark is a critical integrity breach.** Never introduce harness crutches to force a green test.


