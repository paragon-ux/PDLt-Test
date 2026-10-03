# IMPL-0011: Headless Exit Handling and Catalogue Verdicts

## Status
**Accepted.** Implements [ADR-0019](../0019-headless-waiting-input-exit-and-wire-tolerance.md) and its amendments, plus §6 of [ADR-0012](../0012-system-1-decision-models-via-rlcd.md). Recorded 2026-10-03 from the 2.6.0rc1 code.

## Decision (as implemented)
- **Where.** `host/repl.py` maps the final controller stage to an exit code when the session is non-interactive (`--non-interactive`, `--exit-on-close`, or piped input). `EXIT_HARNESS_ERROR = 4` is defined there.
- **Messages.**
  - A run ending at `WAITING_INPUT` prints `[headless halt] Session paused at stage 'WAITING_INPUT' (input requested). Exiting (code 3).`
  - A harness or provider error prints a structured `[harness-error]` record to stderr, then exits 4.
- **`REQUEST_INPUT` tolerance.** In `ExecutionRequestInputData` (`runtime/wire_payloads.py`), `description` is optional. When it is empty, it is filled from the first line of `body` (up to 120 characters).
- **Catalogue mapping** (`run_catalogue.py`):

  | Exit | Verdict |
  |---|---|
  | 0 | `CLOSED_SUCCESS` |
  | 1 | `CLOSED_CANCELLED` |
  | 2 | `UNCONFIRMED_GATE` |
  | 3 | `WAITING_INPUT` |
  | 4 | `HARNESS_ERROR` |

  - A timeout or harness fault gets its own verdict.
  - `CATALOGUE_MANIFEST.jsonl` sets `expected_stage`, for example `WAITING_INPUT` for 13-06.
  - A pass also needs a ground-truth grade that is not FAIL (`is_prompt_pass`).

## Evidence
REG-013, catalogue `13-06` (`catalogue-13-06-1790682691`): a correct clarification request was scored as an unconfirmed gate (exit 2), and the required `description` caused wire retries.

## Verification
`tests/test_codex_decoupling.py`, the REPL integration and exit-code tests, and `run_catalogue.py --dry-run`.
