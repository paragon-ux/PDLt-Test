# PDLt Catalogue Run - run-20261001-144600

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-10-01T18:46:00.537192+00:00  
**Total Time:** 74.3s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 2 |
| Failed | 5 |
| **Pass Rate** | **28.6%** |
| Model calls (total / EXECUTE / repairs) | 23 / 2 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 9955 / 9180 |
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
| medium | 2 | 0 | 0% |
| hard | 5 | 2 | 40% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 11.6 |
| 01-02 | combinatorial_search | CLOSED_CANCELLED | 11.5 |
| 01-04 | combinatorial_search | CLOSED_CANCELLED | 11.1 |
| 01-05 | combinatorial_search | CLOSED_CANCELLED | 9.6 |
| 01-06 | combinatorial_search | CLOSED_CANCELLED | 10.6 |

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
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 11.6 |
| FAIL 01-02 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 11.5 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 9.8 |
| FAIL 01-04 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 3 | 11.1 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 3 | 9.6 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 3 | 10.6 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.1 |
