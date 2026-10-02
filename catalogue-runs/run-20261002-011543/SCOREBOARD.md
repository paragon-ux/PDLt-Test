# PDLt Catalogue Run - run-20261002-011543

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-02T05:15:43.072099+00:00  
**Total Time:** 91.4s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 1 |
| Failed | 6 |
| **Pass Rate** | **14.3%** |
| Model calls (total / EXECUTE / repairs) | 25 / 3 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 11560 / 10286 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 7) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 7 | 1 | 6 | 14% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 1 |
| FAIL | 6 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **2** |
|  - 01-03 | no proper 4-coloring among 0 candidate colorings |
|  - 01-05 | no valid 7x7 completion respecting the givens |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 0 | 0% |
| hard | 5 | 1 | 20% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 13.5 |
| 01-03 | combinatorial_search | CLOSED_SUCCESS | 10.9 |
| 01-04 | combinatorial_search | CLOSED_CANCELLED | 16.0 |
| 01-05 | combinatorial_search | CLOSED_SUCCESS | 12.0 |
| 01-06 | combinatorial_search | CLOSED_CANCELLED | 13.8 |
| 01-07 | combinatorial_search | CLOSED_CANCELLED | 12.5 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-05 | REG-012 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 13.5 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 12.7 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 4 | 10.9 |
| FAIL 01-04 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 4 | 16.0 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 4 | 12.0 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 3 | 13.8 |
| FAIL 01-07 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 12.5 |
