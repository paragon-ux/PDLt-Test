# L107 scratchpad: repair review (2026-10-10)

Source: the 26 scratchpad-arm turns of the L107 A/B that needed a repair (`catalogue-runs/l107-scratchpad`, 60 runs, live, recorded). Everything below is from the recorded artifacts or offline reruns; no new API call. Scripts are in the session scratchpad: `l107_chains.py`, `l107_compare.py`, `l107_expected_0101.py`, `l107_expected_0402.py`.

How each column was established:
- **Original**: the first attempt's failure, from the recorded correction.
- **Note (expected repair)**: the scratchpad note the repair wrote.
- **Would the note's fix work?**: checked offline.
  - 01-01: the strategy the note names, written plainly, run in the host sandbox at the 10M-step budget (`l107_expected_0101.py`).
  - 04-02: the note's fix applied to the program the host ran, then graded by the hidden tests (`l107_expected_0402.py`).
  - 04-03: read against the code.
- **Actual repair**: what the repair program did, from the recorded run, and from offline reruns at a 200M-step budget where marked.

## 1. Accumulation, and notes that only repeat the error

- **Accumulation happened once.** 25 of 26 repaired turns had exactly one repair; the STANDARD tier allows one (`sandbox.py:401`). The one turn with a second repair ([18]) got the first note back as `SCRATCHPAD`. That note said "No previous attempt details needed", so nothing useful accumulated. Notes reached the model in 1 of 57 repair requests (ledger L107).
- **No note copies the error text.** Of each note's content words, 8–27% appear in the correction.
- **9 of 21 notes say nothing beyond the error**: they restate it or say "straightforward backtracking" and claim a fix without naming a cause or a concrete change ([0] [9] [18]×2 [26] [36] [37] [42] [44]).
- **12 name a cause or a concrete change.** Of those 12:
  - 6 are right and would fix the failure if implemented ([1] [24] [48] [57] [12] [11]);
  - 1 is right but would not be enough ([34]: a second bug sits behind the syntax error);
  - 2 are wrong ([33]: the plan *is* the bug; [59]: the typo it names is not in the program);
  - 3 are guesses that can't be checked ([20] [38] [50]).
- **About 10 notes claim results the model cannot know**: "tests now pass", "should finish well within 10M steps".
- **6 repairs wrote no note**: 5 on 04-02, 1 on 04-03. The field is optional on the wire (`anyOf string/null`) and the response format is `json_object`, so nothing enforced it.

## 2. Original vs repair expected (note) vs repair actual

| Turn | Original failure | Note (expected repair) | Would the note's fix work? | Actual repair | Grade |
|---|---|---|---|---|---|
| 01-01 [0] | over budget (26.3M steps at a 200M budget: 2.6× over, would have found the answer) | "simple backtracking with early pruning … staying within 10M" | no change named | new program, >200M steps (further over) | FAIL |
| 01-01 [9] | >200M | "straightforward backtracking; expect to find solution quickly; if exceeded, output negative witness" | no change named; the plan contradicts the correction | >200M | FAIL |
| 01-01 [12] | over budget | "precompute candidate triples, DFS with pruning" | yes (the model's own version passed) | implemented, 4.8M steps | PASS |
| 01-01 [18] | a1 ran no program; a2 >200M | a2: "No previous attempt details needed"; a3: "explores at most the number of triples" | nothing to apply; a false claim | a2 and a3 >200M | FAIL |
| 01-01 [24] | >200M | "smallest-element heuristic; step counter to abort" | **yes: 2.87M steps** written plainly | pivot implemented, but every remaining number scanned at each node; >150 s at a 200M budget. The step counter counts loop turns, not steps, so it never fires | FAIL |
| 01-01 [33] | over budget | "pick c having fewest remaining pairs" | **no: the plan is the bug** (each number tried only as a sum; a number that is never a sum has 0 pairs, so the search dead-ends) | implemented as written; 21k steps, false negative witness, WITNESS_INVALID | FAIL |
| 01-01 [36] | a1 ran no program | "backtracking with heuristic" | generic | 3.9M steps | PASS |
| 01-01 [42] | >200M | "straightforward; the set is small, should finish well under budget" | no change named; false claim | over budget | FAIL |
| 01-01 [48] | over budget | "exact-cover backtracking" | **yes: 8.7M steps** written plainly (first-unused pivot) | pivot implemented, but all 146 triples scanned at each node; over budget | FAIL |
| 01-01 [57] | over budget | "most constrained unused number" | **yes: 1.2M steps** | implemented, 3.0M steps | PASS |
| 04-02 [1] | SyntaxError: `raise ValueError('Invalid \u escape')` | "unescaped \u in a string literal; avoid raw \u" | **yes: with the fix applied, the original passes every hidden test** | `\u` line re-emitted in the rewritten program; same SyntaxError | FAIL |
| 04-02 [10] | JSONParseError: invalid number | (none) | – | rewritten; passed | PASS |
| 04-02 [13] | `\u` SyntaxError | (none; reply malformed) | fix applied: hidden tests fail (bytes vs str) | OUTPUT_MALFORMED | FAIL |
| 04-02 [19] | `\u` SyntaxError | (none) | fix applied: hidden tests fail | `\u` again | FAIL |
| 04-02 [25] | `\u` SyntaxError | (none) | fix applied to the *repair*: passes every hidden test | `\u` again | FAIL |
| 04-02 [34] | `\u` SyntaxError | "incorrect escaping of \u; fixed by using proper double backslashes" | diagnosis right; fix applied: hidden tests still fail (second bug) | **the line is byte-identical**: `\\u` in the JSON both times, which decodes to `\u` | FAIL |
| 04-02 [37] | ValueError: Expected , or ] | "fixed _after_value and comma handling" | restates the error | new program with the `\u` SyntaxError | FAIL |
| 04-02 [49] | `\u` SyntaxError | (none) | – | different approach; passed | PASS |
| 04-03 [11] | IndexError: pop from empty list | "operator stack misuse; rewrote with recursive descent" | plausible | rewritten; passed | PASS |
| 04-03 [20] | AssertionError, no message (the failing line `assert engine2.match('123')` was dropped by the host) | "likely pattern parsing error or missing epsilon handling" | a guess | passed | PASS |
| 04-03 [26] | ValueError: Invalid regex | "fixed token classification … All tests now pass" | vague; false claim | exit 0; hidden tests fail (IndexError) | FAIL |
| 04-03 [35] | TypeError in parse_factor | (none) | – | new TypeError | FAIL |
| 04-03 [38] | AssertionError: '[0-9]+' on 'abc' expected False | "character class: expand ranges" | specific; unverified | another assertion fails | FAIL |
| 04-03 [44] | SyntaxError: unmatched '}' | "stray curly brace; reviewed brackets" | restates the error | exit 0; hidden tests fail (constructor signature) | FAIL |
| 04-03 [50] | ValueError: Invalid regex (the calling line `assert matches('a(b\|c)*d','ad')` was dropped by the host) | "handling '.' and character classes; explicit concatenation" | a guess | same ValueError, same function | FAIL |
| 04-03 [59] | SyntaxError: `def build_\|(self, ast):` | "variable name typo nFA1 -> nfa1" | **wrong: no such name in the program** | syntax error gone (rewritten), new TypeError | FAIL |

**Totals:**
- The repair reproduced the original's first error code in 11 of 26 scratchpad turns, and in 6 of 20 baseline turns.
- Where a note named a working fix, the actual repair missed it 4 times ([1] [24] [34] [48]): the note was right and the program was not.
- The note itself was wrong twice ([33] [59]).

## 3. What stops the scratchpad from repairing

1. **The note is written after the program.** In all 21 replies with a note, the fields come in schema order and `scratchpad` is last. The note summarises a repair already written, so it can't steer it, and it claims results the model hasn't seen.
2. **The repair can't see the program it is repairing.** No repair request carries the first attempt's program or approach. The one apparent match is the input list copied from the task. The model rewrites from scratch: the error's line numbers point at code it doesn't have, and habits come back. On 04-02 the `\u` line was regenerated in 7 of 8 repairs, including one that introduced it ([37]).
3. **The host drops the traceback.** `_stderr_summary` (`session_engine.py:293-303`) keeps only the innermost location and the exception. Python printed the failing source line and the calling frames (which test, which pattern), and the host threw them away. Notes then guess ("likely …") or invent a cause ([59]).
4. **The JSON layer eats a backslash.** The program travels as a JSON string. The model's "double the backslash" fix was made in the JSON, so the line the host ran was unchanged: in both notes that named this fix, the repaired line is byte-identical.
5. **Budget failures carry no measurement.** The correction says only "stopped after 10,000,000 steps". The model can't tell how far over it was or where the steps went, and every measured 01-01 repair was further over than its original. The plans in the notes were often good enough (2.9M and 8.7M steps written plainly); the implementations cost 3–25× more.
6. **One repair.** With one repair per turn, a note can't come back, so memory was never exercised.
7. **The note isn't enforced.** It is optional on the wire and the response format is `json_object`, so 6 repairs wrote none.

## 4. Fixes under test (each on its own branch)

- **L108, traceback** (branch `l108-traceback`, off `ec089e2d`): the correction for a failed program carries the program's own traceback: every frame in the program with the source line Python printed for it, and the exception. The host's own frames are left out; the cap is 2,000 characters, keeping the end. Facts only, no method advice (GUARD-01). It addresses 3 and partly 4, since the host-run line now shows the single backslash. Offline: 5 new tests; one existing test updated for the format.
- **L107 v2, note first** (branch `scratchpad-test`): `scratchpad` is the first property of both repair variants, and its description asks for it before the other fields (the failure, its cause, what this attempt changes). It addresses 1. First attempts are unchanged, because the field exists only in repair mode.
- **Not addressed in this round**: 2 (send the failed program back), 5 (a step measurement for budget stops), 6 (repairs per tier) and 7 (enforcement). These are the candidates if the round shows no uplift.

**Test design: frozen repair** (`experiments/l107_scratchpad/frozen_repair.py`, branch `scratchpad-test`):
- **Samples:** the 39 recorded L107 turns whose first attempt ran a program that failed, by a rule fixed before any result.
- **What is frozen:** the first attempt, its sandbox run and System 1's decisions are the recorded ones. Only the repair is sent live, under each arm's tree.
- **Fidelity:** offline, the replayed repair request under the baseline tree is byte-identical to the recorded one.
- **Arms:** baseline (`ec089e2d`), traceback (`l108-traceback`), and scratchpad v2 (`scratchpad-test`, which includes the traceback fix).
- **Measures:** PASS per arm, paired comparisons (exact test on discordant pairs), and how often the first error code repeats.
