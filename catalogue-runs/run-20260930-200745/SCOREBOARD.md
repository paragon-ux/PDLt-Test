# PDLt Catalogue Run - run-20260930-200745

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-01T00:07:45.889329+00:00  
**Total Time:** 99.8s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 5 |
| Passed | 4 |
| Failed | 1 |
| **Pass Rate** | **80.0%** |
| Model calls (total / EXECUTE / repairs) | 24 / 8 / 3 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 1 (of 5) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 5 | 4 | 1 | 80% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 4 |
| FAIL | 1 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 1 | 1 | 100% |
| hard | 4 | 3 | 75% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-05 | combinatorial_search | CLOSED_CANCELLED | 18.4 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-05 | REG-012 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 25.4 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 23.1 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 16.6 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 16.2 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 18.4 |
