# PDLt Catalogue Run - run-20261001-221730

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-10-02T02:17:30.158125+00:00  
**Total Time:** 74.2s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 2 |
| Failed | 5 |
| **Pass Rate** | **28.6%** |
| Model calls (total / EXECUTE / repairs) | 23 / 2 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 10665 / 10065 |
| Plans identical to prompt / >=80% copied (of plans) | 1 / 1 (of 7) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 7 | 2 | 5 | 29% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 2 |
| FAIL | 5 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 1 | 50% |
| hard | 5 | 1 | 20% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 10.9 |
| 01-02 | combinatorial_search | CLOSED_CANCELLED | 10.9 |
| 01-05 | combinatorial_search | CLOSED_CANCELLED | 10.3 |
| 01-06 | combinatorial_search | CLOSED_CANCELLED | 10.4 |
| 01-07 | combinatorial_search | CLOSED_CANCELLED | 10.2 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-02 | REG-011 | CLOSED_CANCELLED |
| 01-05 | REG-012 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 10.9 |
| FAIL 01-02 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 10.9 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.3 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 11.2 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 10.3 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 3 | 10.4 |
| FAIL 01-07 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 10.2 |
