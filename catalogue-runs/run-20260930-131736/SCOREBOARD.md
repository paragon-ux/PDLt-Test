# PDLt Catalogue Run - run-20260930-131736

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T17:17:36.249868+00:00  
**Total Time:** 32.6s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 1 |
| Passed | 0 |
| Failed | 1 |
| **Pass Rate** | **0.0%** |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| formal_verification | 1 | 0 | 1 | 0% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 0 |
| FAIL | 1 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **1** |
|  - 14-07 | claims a termination proof for an open problem |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| adversarial | 1 | 0 | 0% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 14-07 | formal_verification | CLOSED_SUCCESS | 32.6 |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| FAIL 14-07 | formal_verification | adversarial | CLOSED_SUCCESS | FAIL | 32.6 |
