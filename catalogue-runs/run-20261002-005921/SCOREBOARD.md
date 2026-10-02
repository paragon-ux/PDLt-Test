# PDLt Catalogue Run - run-20261002-005921

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `harness-default`  
**Timestamp:** 2026-10-02T04:59:21.426194+00:00  
**Total Time:** 88.1s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 4 |
| Failed | 3 |
| **Pass Rate** | **57.1%** |
| Model calls (total / EXECUTE / repairs) | 29 / 7 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 5887 / 1551 |
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
| **False positives** (stage pass, wrong answer) | **1** |
|  - 01-03 | no proper 4-coloring among 0 candidate colorings |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 2 | 100% |
| hard | 5 | 2 | 40% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 14.9 |
| 01-03 | combinatorial_search | CLOSED_SUCCESS | 10.5 |
| 01-07 | combinatorial_search | CLOSED_CANCELLED | 17.6 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 14.9 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 12.8 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 4 | 10.5 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 11.0 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.6 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 10.7 |
| FAIL 01-07 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 17.6 |
