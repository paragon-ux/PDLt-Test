# PDLt Catalogue Run - run-20260930-131112

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T17:11:12.226316+00:00  
**Total Time:** 150.5s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 4 |
| Failed | 3 |
| **Pass Rate** | **57.1%** |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| negative_and_impossible | 7 | 4 | 3 | 57% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 4 |
| FAIL | 2 |
| MANUAL | 1 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **2** |
|  - 13-03 | uses the nonexistent frostbitedb API |
|  - 13-06 | optimizes against a guessed schema ('FROM your_table') |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 1 | 0 | 0% |
| hard | 3 | 2 | 67% |
| adversarial | 3 | 2 | 67% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 13-02 | negative_and_impossible | CLOSED_CANCELLED | 27.0 |
| 13-03 | negative_and_impossible | CLOSED_SUCCESS | 16.1 |
| 13-06 | negative_and_impossible | CLOSED_SUCCESS | 24.5 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 13-03 | REG-003 | CLOSED_SUCCESS |
| 13-06 | REG-013 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| PASS 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 66.2 |
| FAIL 13-02 | negative_and_impossible | hard | CLOSED_CANCELLED | MANUAL | 27.0 |
| FAIL 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | FAIL | 16.1 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 14.9 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0.9 |
| FAIL 13-06 | negative_and_impossible | medium | CLOSED_SUCCESS | FAIL | 24.5 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0.9 |
