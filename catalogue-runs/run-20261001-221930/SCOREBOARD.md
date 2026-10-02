# PDLt Catalogue Run - run-20261001-221930

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-02T02:19:30.908885+00:00  
**Total Time:** 94.7s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 6 |
| Failed | 1 |
| **Pass Rate** | **85.7%** |
| Model calls (total / EXECUTE / repairs) | 29 / 7 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 5289 / 1666 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 7) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 7 | 6 | 1 | 86% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 6 |
| FAIL | 1 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 2 | 100% |
| hard | 5 | 4 | 80% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 17.2 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 17.2 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 12.5 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 14.9 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 11.6 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 14.0 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 13.7 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.8 |
