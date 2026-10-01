# PDLt Catalogue Run - run-20261001-094304

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-01T13:43:04.829681+00:00  
**Total Time:** 1060.5s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 10 |
| Passed | 2 |
| Failed | 8 |
| **Pass Rate** | **20.0%** |
| Model calls (total / EXECUTE / repairs) | 59 / 27 / 13 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 14856 / 0 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 1 (of 10) |

## Pass Rate per Prompt (repeats)

| Prompt | Passed | Runs |
|--------|--------|------|
| 01-01 | 2 | 10 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 10 | 2 | 8 | 20% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 2 |
| FAIL | 8 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **1** |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| hard | 10 | 2 | 20% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | WAITING_INPUT | 48.4 |
| 01-01 | combinatorial_search | WAITING_INPUT | 226.2 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 240.3 |
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 42.2 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 100.5 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 96.3 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 104.4 |
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 44.9 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | WAITING_INPUT |
| 01-01 | REG-003 | WAITING_INPUT |
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
| FAIL 01-01 | combinatorial_search | hard | WAITING_INPUT | FAIL | 5 | 48.4 |
| FAIL 01-01 | combinatorial_search | hard | WAITING_INPUT | FAIL | 6 | 226.2 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 7 | 240.3 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 4 | 42.2 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 8 | 100.5 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 96.3 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 104.4 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 44.9 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 6 | 79.8 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 6 | 77.5 |
