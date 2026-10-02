# PDLt Catalogue Run - run-20261002-005707

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-02T04:57:07.797296+00:00  
**Total Time:** 76.7s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 4 |
| Failed | 3 |
| **Pass Rate** | **57.1%** |
| Model calls (total / EXECUTE / repairs) | 29 / 7 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 6067 / 1910 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 7) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 7 | 4 | 3 | 57% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 4 |
| FAIL | 3 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

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
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 14.4 |
| 01-04 | combinatorial_search | CLOSED_CANCELLED | 8.0 |
| 01-07 | combinatorial_search | CLOSED_CANCELLED | 11.8 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 14.4 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.8 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 11.7 |
| FAIL 01-04 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 4 | 8.0 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.0 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 10.1 |
| FAIL 01-07 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 11.8 |
