# PDLt Catalogue Run - run-20260930-112451

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T15:24:51.135842+00:00  
**Total Time:** 102.9s  

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
| PASS | 1 |
| FAIL | 0 |
| MANUAL | 6 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 1 | 1 | 100% |
| hard | 3 | 3 | 100% |
| adversarial | 3 | 2 | 67% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 13-07 | negative_and_impossible | WAITING_INPUT | 9.4 |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Time (s) |
|----|----------|-----------|---------|----------|
| PASS 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | 21.5 |
| PASS 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | 19.7 |
| PASS 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | 10.8 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | 21.8 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | 1.0 |
| PASS 13-06 | negative_and_impossible | medium | WAITING_INPUT | 18.8 |
| FAIL 13-07 | negative_and_impossible | adversarial | WAITING_INPUT | 9.4 |
