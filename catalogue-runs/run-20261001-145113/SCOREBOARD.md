# PDLt Catalogue Run - run-20261001-145113

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-01T18:51:13.268936+00:00  
**Total Time:** 102.9s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 3 |
| Failed | 4 |
| **Pass Rate** | **42.9%** |
| Model calls (total / EXECUTE / repairs) | 25 / 3 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 15310 / 14218 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 7) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 7 | 3 | 4 | 43% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 3 |
| FAIL | 4 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 1 | 50% |
| hard | 5 | 2 | 40% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 16.8 |
| 01-02 | combinatorial_search | CLOSED_CANCELLED | 15.4 |
| 01-05 | combinatorial_search | CLOSED_CANCELLED | 15.4 |
| 01-06 | combinatorial_search | CLOSED_CANCELLED | 14.4 |

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
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 16.8 |
| FAIL 01-02 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 15.4 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 16.0 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 11.0 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 15.4 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 3 | 14.4 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 14.0 |
