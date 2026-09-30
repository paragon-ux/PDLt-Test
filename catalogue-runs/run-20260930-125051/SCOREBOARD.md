# PDLt Catalogue Run - run-20260930-125051

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T16:50:51.700438+00:00  
**Total Time:** 141.8s  

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
| hard | 3 | 2 | 67% |
| adversarial | 3 | 3 | 100% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 13-02 | negative_and_impossible | WAITING_INPUT | 11.5 |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Time (s) |
|----|----------|-----------|---------|----------|
| PASS 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | 96.4 |
| FAIL 13-02 | negative_and_impossible | hard | WAITING_INPUT | 11.5 |
| PASS 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | 12.5 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | 12.8 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | 0.8 |
| PASS 13-06 | negative_and_impossible | medium | WAITING_INPUT | 6.8 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | 0.9 |
