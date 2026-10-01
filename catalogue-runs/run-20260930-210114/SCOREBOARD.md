# PDLt Catalogue Run - run-20260930-210114

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-10-01T01:01:14.005958+00:00  
**Total Time:** 383.7s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 10 |
| Passed | 1 |
| Failed | 9 |
| **Pass Rate** | **10.0%** |
| Model calls (total / EXECUTE / repairs) | 60 / 27 / 17 |
| Reasoning tokens spent in EXECUTE (all prompts) | 0 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 1 (of 10) |

## Pass Rate per Prompt (repeats)

| Prompt | Passed | Runs |
|--------|--------|------|
| 01-01 | 1 | 10 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 10 | 1 | 9 | 10% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 1 |
| FAIL | 9 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| hard | 10 | 1 | 10% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 68.8 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 19.6 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 48.0 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 33.9 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 37.6 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 35.4 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 44.9 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 30.9 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 38.5 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 68.8 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 19.6 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 48.0 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 33.9 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 7 | 37.6 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 35.4 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 7 | 44.9 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 30.9 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 38.5 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 6 | 26.1 |
