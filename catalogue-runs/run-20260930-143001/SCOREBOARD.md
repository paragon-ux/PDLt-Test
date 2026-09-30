# PDLt Catalogue Run - run-20260930-143001

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T18:30:01.012622+00:00  
**Total Time:** 129.0s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 5 |
| Failed | 2 |
| **Pass Rate** | **71.4%** |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| negative_and_impossible | 7 | 5 | 2 | 71% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 5 |
| FAIL | 2 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **2** |
|  - 13-02 | claims an optimum with neither an acknowledgement nor code that computes it |
|  - 13-03 | uses the nonexistent frostbitedb API |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 1 | 1 | 100% |
| hard | 3 | 2 | 67% |
| adversarial | 3 | 2 | 67% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 13-02 | negative_and_impossible | CLOSED_SUCCESS | 15.0 |
| 13-03 | negative_and_impossible | CLOSED_SUCCESS | 24.1 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 13-03 | REG-003 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| PASS 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 20.2 |
| FAIL 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | FAIL | 15.0 |
| FAIL 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | FAIL | 24.1 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 55.8 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.1 |
| PASS 13-06 | negative_and_impossible | medium | WAITING_INPUT | PASS | 11.7 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.1 |
