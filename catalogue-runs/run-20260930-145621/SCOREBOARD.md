# PDLt Catalogue Run - run-20260930-145621

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T18:56:21.775258+00:00  
**Total Time:** 63.1s  

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
| PASS | 7 |
| FAIL | 0 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

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
| 13-01 | negative_and_impossible | CLOSED_CANCELLED | 27.0 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 13-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| FAIL 13-01 | negative_and_impossible | hard | CLOSED_CANCELLED | PASS | 27.0 |
| PASS 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 2.1 |
| PASS 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.5 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 22.9 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.3 |
| PASS 13-06 | negative_and_impossible | medium | WAITING_INPUT | PASS | 7.2 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 1.2 |
