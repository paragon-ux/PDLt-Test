# PDLt Catalogue Run - run-20260930-153950

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T19:39:50.537767+00:00  
**Total Time:** 197.3s  

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
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 48.2 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 48.2 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 33.9 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 24.2 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 17.4 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 23.6 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 17.4 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 32.5 |
