# Decision and work ledger (canonical)

This file is the **single source of truth** for cross-cutting decisions and open items.

**When to read it:** every session reads it first, and again after any context compaction (`AGENTS.md`, "Continuity").

**Where the detail lives:** the plans hold the reasoning. This file holds the status, and points to them.

**Updating it:**
- Every PR that settles or changes an item updates its row in the same PR.
- A decision made in a side chat is not settled until it has a row here with its source.
- An external tracker or dashboard, if any, mirrors this file. It never replaces it.

**Status values:**
- `open`: not decided;
- `decided`: decided, not yet built;
- `in PR n`: being built in that PR;
- `done`: merged;
- `conflict`: two recorded decisions disagree, and only the user settles it.

**Sources:**
- `main`: this repository's main working chat;
- `side`: the user's side chat, pasted into main;
- `user`: the user's own words in main.

## Where the item registries live

| IDs | Registry |
|---|---|
| FA1–FA8, FB1–FB6, Q1–Q9, Tier D (D1–D3 mechanisms) | [protocol-fixes-plan.md](protocol-fixes-plan.md) |
| F1–F19 (facts), D1–D16 (gate decisions), G1–G5, A1, M1 (rules) | [protocol-vs-control-experiment-design.md](protocol-vs-control-experiment-design.md) §1, §8.4, §14 |
| U1–U6 (ultrafast decisions), R1–R7 (review log) | [ultrafast-route-design.md](ultrafast-route-design.md) §8, §12 |
| PR 2 tasks T1–T11 | [pr2-worklist.md](pr2-worklist.md) |

## Ledger

| ID | Item | Source | Status | Decision | Link |
|---|---|---|---|---|---|
| L1 | Fix from principle first; spend runs only on what principle can't settle; measure once, as a gate, never a dial | user + side, 2026-10-04 | decided | The fixes are Tiers A/B; Tier C is the only thing runs are spent on; one gate run. | fix plan, "Why this order" |
| L2 | PR #1 (resume fix FA5) merged before any experiment PR | user, 2026-10-04 | done | Merged as `4ebf7c59`; the catalogue gate was waived (REG-003). | fix plan, Sequencing 1 |
| L3 | FB5: the user's words govern; the pseudocode is the reviewed interpretation | user, 2026-10-04 | decided (PR 4b) | Adopted. | fix plan FB5; gate D8 |
| L4 | The grader budget is the tier the published code ran under | user, 2026-10-04 | done (on the branch) | `graders._run_budget` reads the last `SANDBOX_RUN` tier. | gate D9; `graders.py` |
| L5 | Ultrafast decisions U1, U3, U4, U6 | user (confirming side), 2026-10-04 | decided (PR 5) | As recommended. | ultrafast §8 |
| L6 | **U2, the flag name** | user (main) and side, 2026-10-04 | **conflict** | **Main:** "Ultrafast = --ultrafast". **Side (as pasted):** `--no-review` as the canonical flag, `--ultrafast` as an alias, plus a startup banner. **The user must pick one;** the docs say `--ultrafast` until then. | ultrafast §8 U2 |
| L7 | U5, live checks for ultrafast | side, 2026-10-04 | decided | Superseded by L8. | ultrafast §8 U5 |
| L8 | **Static-first verification:** static analysis, then offline tests, then live only on the trigger | side → user, 2026-10-04 | in PR 2 | AGENTS.md "Diagnosis and Verification Rule"; the ADR-0015 amendment; REVIEWER.md §5; the plan-doc edits (fix plan, 0028 plan, ultrafast U5). | `AGENTS.md`; ADR-0015; `REVIEWER.md` |
| L9 | **Nemotron is out of the experiments** (about 14 tokens/s); gpt-oss only, single-model | user + side, 2026-10-04 | decided | The conclusions are labelled single-model. | gate §7, D14 |
| L10 | The criteria and procedure for a replacement or second model | side, 2026-10-04 | decided (criteria); open (choice) | Criteria fixed before any result; never relaxed to let a candidate pass. | gate §7, D15 |
| L11 | **The Class D / Class C trap:** an unlisted model gets reasoning off at EXECUTE; an id matching thinking/r1/o3/o4 gets Class C | side, 2026-10-04 | decided | Set the model's profile explicitly before any run, with FB1's floor. | gate §7, "Two traps" |
| L12 | **The shipped default model** (Nemotron `:free`) goes untested by the gate | side, 2026-10-04 | **open** | Yours: switch the default to a tested model, or accept an untested default. | gate D16 |
| L13 | D14 is superseded by the model change: the three-stream and Nvidia-check plans are moot | side, 2026-10-04 | decided | Resolved by L9. | gate D14 |
| L14 | **Raise the key's own $5 limit** (topping up doesn't change it) and top up at least $10 | side, 2026-10-04 | open (before Day 1) | A user action on OpenRouter. | gate D6, §7 |
| L15 | **The catalogue is fixed before any run** (no baseline, no experiment) | user + side, 2026-10-04 | in PR 2 | Hidden tests, the judged group, per-template scoring, a regrade. | worklist T1–T9 |
| L16 | Hidden-test graders for the coding categories | side, 2026-10-04 | in PR 2 | 29 prompts: 02 ×7, 03 ×4, 04 ×6, 05 ×7, 06 ×5. Each has ref, alt and bug answers that must pass, pass and fail. Sandbox-denied prompts are judged instead: 03-01, 03-04, 03-07, 04-04, 06-04, 06-05. | `hidden_tests.py`; worklist T1–T2, T4 |
| L17 | Category 15 checked prompt by prompt (machine-graded or judged) | side, 2026-10-04 | decided (rubrics in T5) | All 7 are judged: they are analyses and designs with no API to test. 15-01's rubric carries exact reference counts: LRU 9/30 hits; LFU 12/30 under every tie-break and history variant; ARC 12/30 (Megiddo–Modha; confirm against a second implementation before freezing). So LFU and ARC tie, and both beat LRU. 15-04 and 15-07 carry reference derivations. | worklist T5 |
| L18 | A judged group with frozen rubrics, two blinded judges (Claude, Gemini), and an agreement threshold (κ ≥ 0.7, else reported separately); disagreements go to the user | side, 2026-10-04 | in PR 2 (to do) | | worklist T5 |
| L19 | Generated items analysed per template (clusters); add templates rather than items | side, 2026-10-04 | in PR 2 (to do) | | worklist T7 |
| L20 | Regrade the old catalogue runs with FA2 and the new graders, giving the baseline | side, 2026-10-04 | in PR 2 (to do) | | worklist T9 |
| L21 | **Tier D1:** standard mode feeds the model's own failing tests back as repair findings (from the structured sandbox result; never stderr, never the hidden tests) | side, 2026-10-04 | decided (PR 6) | Its own PR after the gate, with a second gate on a fresh set. | fix plan, Tier D |
| L22 | **Tier D2:** best-of-k EXECUTE with host witness selection (verified mode) | side, 2026-10-04 | decided (PR 6) | Accuracy against cost as k grows. | fix plan, Tier D |
| L23 | **Tier D3:** a post-answer self-check, measured in both directions (wrong→right and right→wrong) | side, 2026-10-04 | decided (PR 6) | | fix plan, Tier D |
| L24 | **Gate addition:** an ambiguity group with a scripted reviewer | side, 2026-10-04 | in PR 2 (designed; build is T11) | Arms P_rev, C0, C0+F, P_unc+F; rule A1, reported. | gate §6.6, §8.4 |
| L25 | **Gate addition:** the FB1-only branch from P_old's plan | side, 2026-10-04 | in PR 2 (designed; build is T11) | +FB1: one extra call per block; a secondary estimate. | gate §3.2, §4, §8.5 |
| L26 | **Gate addition:** cost and latency per correct answer, and a default-choosing rule | side, 2026-10-04 | in PR 2 (designed; analysis is T7) | G5: among eligible routes, the cheapest per correct answer. | gate §8.1, §8.4 |
| L27 | **Gate addition:** category 10 (multi-turn) | side, 2026-10-04 | in PR 2 (designed; build is T11) | Group M, rule M1, reported. | gate §6.6 |
| L28 | Keep the tracker in the repo (this file), with AGENTS.md and memory pointing to it; no MCP task manager as the source of truth | side → user, 2026-10-04 | done (on the branch) | An external dashboard may mirror this file, never replace it. | `AGENTS.md`, "Continuity" |
