# PDLt Catalogue Run - run-20260930-132457

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T17:24:57.981326+00:00  
**Total Time:** 136.3s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 3 |
| Failed | 4 |
| **Pass Rate** | **42.9%** |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| negative_and_impossible | 7 | 3 | 4 | 43% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 3 |
| FAIL | 4 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **4** |
|  - 13-01 | does not report unsatisfiability |
|  - 13-02 | claims an optimum with neither an acknowledgement nor code that computes it |
|  - 13-03 | uses the nonexistent frostbitedb API |
|  - 13-06 | optimizes against a guessed schema ('FROM table') |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 1 | 0 | 0% |
| hard | 3 | 1 | 33% |
| adversarial | 3 | 2 | 67% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 13-01 | negative_and_impossible | CLOSED_SUCCESS | 24.9 |
| 13-02 | negative_and_impossible | CLOSED_SUCCESS | 15.7 |
| 13-03 | negative_and_impossible | CLOSED_SUCCESS | 21.1 |
| 13-06 | negative_and_impossible | CLOSED_SUCCESS | 12.8 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 13-01 | REG-003 | CLOSED_SUCCESS |
| 13-03 | REG-003 | CLOSED_SUCCESS |
| 13-06 | REG-013 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| FAIL 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | FAIL | 24.9 |
| FAIL 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | FAIL | 15.7 |
| FAIL 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | FAIL | 21.1 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 59.8 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.0 |
| FAIL 13-06 | negative_and_impossible | medium | CLOSED_SUCCESS | FAIL | 12.8 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.0 |
