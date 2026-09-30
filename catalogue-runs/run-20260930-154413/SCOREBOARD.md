# PDLt Catalogue Run - run-20260930-154413

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T19:44:13.324795+00:00  
**Total Time:** 59.5s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 6 |
| Failed | 1 |
| **Pass Rate** | **85.7%** |

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
|  - 13-01 | does not report unsatisfiability |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 1 | 1 | 100% |
| hard | 3 | 2 | 67% |
| adversarial | 3 | 3 | 100% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 13-01 | negative_and_impossible | CLOSED_SUCCESS | 27.7 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 13-01 | REG-003 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| FAIL 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | FAIL | 27.7 |
| PASS 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 2.1 |
| PASS 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 2.2 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 14.8 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.2 |
| PASS 13-06 | negative_and_impossible | medium | WAITING_INPUT | PASS | 10.4 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.0 |
