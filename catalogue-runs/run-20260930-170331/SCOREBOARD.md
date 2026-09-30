# PDLt Catalogue Run - run-20260930-170331

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T21:03:31.346570+00:00  
**Total Time:** 67.8s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 6 |
| Failed | 1 |
| **Pass Rate** | **85.7%** |
| Model calls (total / EXECUTE / repairs) | 15 / 4 / 1 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| negative_and_impossible | 7 | 6 | 1 | 86% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 6 |
| FAIL | 1 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **1** |
|  - 13-06 | optimizes against a guessed schema ('FROM orders') |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 1 | 0 | 0% |
| hard | 3 | 3 | 100% |
| adversarial | 3 | 3 | 100% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 13-06 | negative_and_impossible | CLOSED_SUCCESS | 13.2 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 13-06 | REG-013 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| PASS 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 7 | 35.1 |
| PASS 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 0 | 2.2 |
| PASS 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.8 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 4 | 12.7 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.3 |
| FAIL 13-06 | negative_and_impossible | medium | CLOSED_SUCCESS | FAIL | 4 | 13.2 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.5 |
