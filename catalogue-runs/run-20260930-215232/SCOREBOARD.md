# PDLt Catalogue Run - run-20260930-215232

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-01T01:52:32.086647+00:00  
**Total Time:** 4393.8s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 10 |
| Passed | 6 |
| Failed | 4 |
| **Pass Rate** | **60.0%** |
| Model calls (total / EXECUTE / repairs) | 47 / 16 / 9 |
| Reasoning tokens spent in EXECUTE (all prompts) | 0 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 10) |

## Pass Rate per Prompt (repeats)

| Prompt | Passed | Runs |
|--------|--------|------|
| 01-01 | 6 | 10 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 10 | 6 | 4 | 60% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 6 |
| FAIL | 4 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| hard | 10 | 6 | 60% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 409.7 |
| 01-01 | combinatorial_search | TIMEOUT | 600.0 |
| 01-01 | combinatorial_search | TIMEOUT | 600.0 |
| 01-01 | combinatorial_search | TIMEOUT | 600.0 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | TIMEOUT |
| 01-01 | REG-003 | TIMEOUT |
| 01-01 | REG-003 | TIMEOUT |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 217.3 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 296.2 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 409.7 |
| FAIL 01-01 | combinatorial_search | hard | TIMEOUT | FAIL | 3 | 600.0 |
| FAIL 01-01 | combinatorial_search | hard | TIMEOUT | FAIL | 5 | 600.0 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 6 | 494.4 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 220.6 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 497.9 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 457.6 |
| FAIL 01-01 | combinatorial_search | hard | TIMEOUT | FAIL | 5 | 600.0 |
