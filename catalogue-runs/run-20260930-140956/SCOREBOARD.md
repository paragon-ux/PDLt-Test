# PDLt Catalogue Run - run-20260930-140956

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T18:09:56.070958+00:00  
**Total Time:** 247.4s  

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
| combinatorial_search | 7 | 5 | 2 | 71% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 5 |
| FAIL | 2 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 1 | 50% |
| hard | 5 | 4 | 80% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-05 | combinatorial_search | CLOSED_CANCELLED | 39.3 |
| 01-06 | combinatorial_search | CLOSED_CANCELLED | 52.4 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-05 | REG-012 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 51.1 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 23.9 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 39.5 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 21.9 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 39.3 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 52.4 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 19.2 |
