# PDLt Catalogue Run - run-20260930-143434

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T18:34:34.134101+00:00  
**Total Time:** 247.8s  

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
| combinatorial_search | 7 | 6 | 1 | 86% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 6 |
| FAIL | 1 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 2 | 100% |
| hard | 5 | 4 | 80% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | WAITING_INPUT | 27.0 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | WAITING_INPUT |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| FAIL 01-01 | combinatorial_search | hard | WAITING_INPUT | FAIL | 27.0 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 72.7 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 22.7 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 34.0 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 26.7 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 49.7 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 15.1 |
