# PDLt Catalogue Run - run-20261001-144842

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-01T18:48:42.758985+00:00  
**Total Time:** 84.5s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 5 |
| Failed | 2 |
| **Pass Rate** | **71.4%** |
| Model calls (total / EXECUTE / repairs) | 28 / 7 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 5532 / 1096 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 7) |

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
| medium | 2 | 2 | 100% |
| hard | 5 | 3 | 60% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 16.8 |
| 01-03 | combinatorial_search | CLOSED_CANCELLED | 11.0 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 16.8 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 13.2 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 11.0 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 12.4 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 9.3 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 11.3 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.5 |
