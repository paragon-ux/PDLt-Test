# PDLt Catalogue Run - run-20260930-165728

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T20:57:28.093995+00:00  
**Total Time:** 171.3s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 5 |
| Failed | 2 |
| **Pass Rate** | **71.4%** |
| Model calls (total / EXECUTE / repairs) | 32 / 11 / 3 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 7 | 5 | 2 | 71% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 6 |
| FAIL | 1 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **1** |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 2 | 100% |
| hard | 5 | 3 | 60% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 20.9 |
| 01-02 | combinatorial_search | CLOSED_CANCELLED | 42.5 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_SUCCESS |
| 01-02 | REG-011 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 5 | 20.9 |
| FAIL 01-02 | combinatorial_search | hard | CLOSED_CANCELLED | PASS | 5 | 42.5 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 29.5 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 14.2 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 29.3 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 18.1 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 16.8 |
