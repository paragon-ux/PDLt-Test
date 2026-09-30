# PDLt System 2 Prompt Catalogue — Test Execution Goal

## MISSION

Execute the complete 105-prompt PDLt System 2 Prompt Catalogue through the live pdlt REPL
to produce a definitive scoreboard measuring protocol fidelity on `gpt-oss-120b` at low
reasoning effort. Results are written to `catalogue-runs/<run-timestamp>/`.

---

## NON-NEGOTIABLE RULES

### 1. No Retries, No Do-Overs
Each prompt gets **exactly one execution attempt**. If it fails, log the failure and move on.
No re-running a prompt "to see if it works this time." No modifying prompts mid-run. The
manifest is frozen at run start.

### 2. No Cherry-Picking
All 105 prompts must be executed in manifest order. You may not skip prompts, reorder them
to run easy ones first, or filter to only run categories you expect to pass.

### 3. No Prompt Modification
Prompt files are read-only inputs. You may not edit, simplify, clarify, or annotate a prompt
before feeding it to pdlt. The whole point is testing the model's ability to interpret raw
user input under protocol governance.

### 4. No Manual Intervention in the Protocol
The runner uses `--non-interactive` and `--exit-on-close` and confirms every review gate by
piping `/confirm` (recorded in RUN_META as `gate_policy: evaluator_confirms_via_stdin`). No human
may confirm, revise, edit, or override any gate. The model must produce Prompt Pseudocode and
Response Plan Pseudocode autonomously; the harness's grammar lint is the only gate on them.

### 5. Full Transcript Capture
Every session must produce a transcript file. Sessions without transcripts are invalid.

### 6. Single Model, Single Configuration
The entire run uses one model (`openai/gpt-oss-120b`) at one reasoning effort (`low`).
No switching models mid-run. No escalating reasoning effort for hard prompts.

---

## EXECUTION

### Step 1: Dry Run (Verify Setup)
```powershell
python run_catalogue.py --dry-run
```
Verify: 105 prompts listed, 21 marked VERIFIED (ground truth), manifest parses cleanly.

### Step 2: Single-Prompt Smoke Test
```powershell
python run_catalogue.py --prompt-id 06-04 --timeout 120
```
Run the easiest prompt first (race condition counter, difficulty: easy) to confirm the
harness pipeline works end-to-end. Check the generated result.json and transcript.

### Step 3: Full Run
```powershell
python run_catalogue.py --model openai/gpt-oss-120b --reasoning low --timeout 180
```
This will take approximately 30-60 minutes depending on API latency.

### Step 4: Review Scoreboard
Open `catalogue-runs/<run-timestamp>/SCOREBOARD.md` and report:
1. Overall pass rate
2. Pass rate by category
3. Pass rate by difficulty tier
4. Any known regressions hit (REG-001 through REG-004)
5. Which categories had 0% pass rate (ceiling not reached)
6. Which categories had 100% pass rate (ceiling not tested)

### Step 5: Spot-Check Verified Prompts
For every prompt with `ground_truth_status: "verified"` that reported CLOSED_SUCCESS,
open the transcript and compare the model's output against the solution oracle file in
`prompts/solutions/`. Flag any case where the verdict is CLOSED_SUCCESS but the answer
is substantively wrong (false positive).

---

## OUTPUT STRUCTURE

```
PDLt-Test/catalogue-runs/
    run-YYYYMMDD-HHMMSS/
        RUN_META.json               # Frozen run configuration
        SCOREBOARD.json             # Machine-readable aggregate results
        SCOREBOARD.md               # Human-readable scoreboard with tables
        results/
            01-01_schur_triples_n15/
                result.json         # Verdict, exit code, timing, ground truth
                transcript.txt      # Full pdlt session transcript
                stdout.txt          # Raw stdout from pdlt
                stderr.txt          # Raw stderr (errors, warnings)
                session/            # pdlt session workspace directory
            01-02_exact_cover_dlx/
                ...
            ...                     # 105 result directories total
```

---

## VERDICTS

| Verdict | Meaning |
|---------|---------|
| `CLOSED_SUCCESS` | Full protocol traversal: PROMPT_REVIEW -> PLAN_REVIEW -> EXECUTION -> closed green |
| `UNCONFIRMED_GATE` | Session exited while sitting at an unconfirmed review gate (exit code 2) |
| `TIMEOUT` | Wall-clock timeout exceeded (prompt took too long) |
| `EXIT_N` | pdlt exited with unexpected exit code N |

---

## WHAT SUCCESS LOOKS LIKE

A successful run produces a scoreboard with:
- **Every prompt attempted** (105 results, 0 skipped)
- **RUN_META.json confirms**: `retries_allowed: 0, do_overs_allowed: false`
- **Known regressions (REG-001 to REG-004) not regressed**: these prompts should pass
- **Verified prompts spot-checked**: CLOSED_SUCCESS verdicts match ground truth
- **0 false positives** in SCOREBOARD `false_positives` (graded prompts: 01-01..01-07, 13-01; the other 13 verified prompts are MANUAL)

The pass rate itself is the empirical measurement. We expect it won't be 100% — the whole
point is finding where the ceiling is. But every failure must be a real failure, not an
infrastructure bug or a skipped prompt.

---

## WHAT FAILURE LOOKS LIKE

Invalid run conditions (must abort and restart from scratch):
- Runner crashes before completing all 105 prompts
- Network/API outage causes mass timeouts (>50% TIMEOUT verdicts)
- PYTHONPATH misconfigured (pdlt import errors in stderr)
- Manifest file modified during run

These are NOT invalid — they are legitimate test results:
- Model produces wrong answers (that's what we're measuring)
- Model fails review gates (protocol enforcement working as designed)
- Model times out on hard problems (ceiling found)
- Adversarial prompts cause unexpected behavior (that's why they're in the catalogue)
