# PDLt Catalogue Run - run-20260930-145725

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T18:57:25.876416+00:00  
**Total Time:** 137.3s  

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
| **False positives** (stage pass, wrong answer) | **2** |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |
|  - 01-06 | optimal packing presented=False, First Fit=5 bins stated=False |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 1 | 50% |
| hard | 5 | 3 | 60% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 14.4 |
| 01-03 | combinatorial_search | CLOSED_CANCELLED | 22.9 |
| 01-06 | combinatorial_search | CLOSED_SUCCESS | 28.3 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 14.4 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 17.7 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_CANCELLED | PASS | 22.9 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 18.1 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 17.0 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | FAIL | 28.3 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 18.8 |
