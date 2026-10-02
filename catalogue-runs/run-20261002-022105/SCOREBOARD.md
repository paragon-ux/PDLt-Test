# PDLt Catalogue Run - run-20261002-022105

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `harness-default`  
**Timestamp:** 2026-10-02T06:21:05.003487+00:00  
**Total Time:** 240.1s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 21 |
| Passed | 17 |
| Failed | 4 |
| **Pass Rate** | **81.0%** |
| Model calls (total / EXECUTE / repairs) | 94 / 29 / 8 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 17572 / 3375 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 21) |

## Pass Rate per Prompt (repeats)

| Prompt | Passed | Runs |
|--------|--------|------|
| 01-01 | 1 | 3 |
| 01-02 | 2 | 3 |
| 01-03 | 3 | 3 |
| 01-04 | 3 | 3 |
| 01-05 | 2 | 3 |
| 01-06 | 3 | 3 |
| 01-07 | 3 | 3 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 21 | 17 | 4 | 81% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 19 |
| FAIL | 2 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **1** |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 6 | 6 | 100% |
| hard | 15 | 11 | 73% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 22.1 |
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 18.8 |
| 01-02 | combinatorial_search | CLOSED_CANCELLED | 12.7 |
| 01-05 | combinatorial_search | CLOSED_CANCELLED | 10.3 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | CLOSED_SUCCESS |
| 01-02 | REG-011 | CLOSED_CANCELLED |
| 01-05 | REG-012 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 12.7 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 22.1 |
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 6 | 18.8 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 12.2 |
| FAIL 01-02 | combinatorial_search | hard | CLOSED_CANCELLED | PASS | 6 | 12.7 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.9 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 11.1 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 8.4 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 9.9 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 10.6 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 10.9 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 7.9 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 9.7 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_CANCELLED | PASS | 5 | 10.3 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 9.9 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 10.7 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 13.3 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 11.6 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 9.7 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 8.1 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 8.6 |
