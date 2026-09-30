# PDLt Catalogue Run - run-20260930-152233

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T19:22:33.272651+00:00  
**Total Time:** 600.7s  

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
| combinatorial_search | 7 | 4 | 3 | 57% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 5 |
| FAIL | 2 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **1** |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 0 | 0% |
| hard | 5 | 4 | 80% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 30.8 |
| 01-04 | combinatorial_search | TIMEOUT | 300.0 |
| 01-06 | combinatorial_search | CLOSED_CANCELLED | 129.1 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 30.8 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 30.6 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 48.4 |
| FAIL 01-04 | combinatorial_search | medium | TIMEOUT | FAIL | 300.0 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 36.5 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_CANCELLED | PASS | 129.1 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 25.2 |
