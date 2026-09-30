# PDLt Catalogue Run - run-20260930-132715

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T17:27:15.456010+00:00  
**Total Time:** 177.6s  

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
| formal_verification | 7 | 5 | 2 | 71% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 2 |
| FAIL | 2 |
| MANUAL | 3 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **2** |
|  - 14-05 | states amortized cost 2, expected 3 |
|  - 14-07 | claims a termination proof for an open problem |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 3 | 2 | 67% |
| hard | 3 | 3 | 100% |
| adversarial | 1 | 0 | 0% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 14-05 | formal_verification | CLOSED_SUCCESS | 15.2 |
| 14-07 | formal_verification | CLOSED_SUCCESS | 17.0 |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| PASS 14-01 | formal_verification | medium | CLOSED_SUCCESS | PASS | 17.8 |
| PASS 14-02 | formal_verification | hard | CLOSED_SUCCESS | MANUAL | 47.4 |
| PASS 14-03 | formal_verification | hard | CLOSED_SUCCESS | PASS | 25.8 |
| PASS 14-04 | formal_verification | hard | CLOSED_SUCCESS | MANUAL | 36.8 |
| FAIL 14-05 | formal_verification | medium | CLOSED_SUCCESS | FAIL | 15.2 |
| PASS 14-06 | formal_verification | medium | CLOSED_SUCCESS | MANUAL | 17.6 |
| FAIL 14-07 | formal_verification | adversarial | CLOSED_SUCCESS | FAIL | 17.0 |
