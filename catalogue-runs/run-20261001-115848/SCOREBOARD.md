# PDLt Catalogue Run - run-20261001-115848

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-01T15:58:48.763733+00:00  
**Total Time:** 1477.6s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 10 |
| Passed | 0 |
| Failed | 10 |
| **Pass Rate** | **0.0%** |
| Model calls (total / EXECUTE / repairs) | 54 / 22 / 12 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 12708 / 0 |
| Plans identical to prompt / >=80% copied (of plans) | 1 / 1 (of 9) |

## Pass Rate per Prompt (repeats)

| Prompt | Passed | Runs |
|--------|--------|------|
| 01-01 | 0 | 10 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 10 | 0 | 10 | 0% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 0 |
| FAIL | 10 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **2** |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| hard | 10 | 0 | 0% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | WAITING_INPUT | 60.2 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 636.9 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 88.9 |
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 70.7 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 284.9 |
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 14.2 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 76.0 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 66.6 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 93.8 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 85.4 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | WAITING_INPUT |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_SUCCESS |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_SUCCESS |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | WAITING_INPUT | FAIL | 5 | 60.2 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 636.9 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 88.9 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 5 | 70.7 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 7 | 284.9 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 2 | 14.2 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 76.0 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 66.6 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 93.8 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 85.4 |
