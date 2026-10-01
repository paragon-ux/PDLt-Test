# PDLt Catalogue Run - run-20261001-104454

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-10-01T14:44:54.788713+00:00  
**Total Time:** 4223.8s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 10 |
| Passed | 7 |
| Failed | 3 |
| **Pass Rate** | **70.0%** |
| Model calls (total / EXECUTE / repairs) | 49 / 19 / 8 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 307435 / 0 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 10) |

## Pass Rate per Prompt (repeats)

| Prompt | Passed | Runs |
|--------|--------|------|
| 01-01 | 7 | 10 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 10 | 7 | 3 | 70% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 7 |
| FAIL | 3 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| hard | 10 | 7 | 70% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 892.0 |
| 01-01 | combinatorial_search | WAITING_INPUT | 631.5 |
| 01-01 | combinatorial_search | WAITING_INPUT | 162.0 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-01 | REG-003 | WAITING_INPUT |
| 01-01 | REG-003 | WAITING_INPUT |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 6 | 892.0 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 127.0 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 381.2 |
| FAIL 01-01 | combinatorial_search | hard | WAITING_INPUT | FAIL | 5 | 631.5 |
| FAIL 01-01 | combinatorial_search | hard | WAITING_INPUT | FAIL | 5 | 162.0 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 217.1 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 6 | 566.7 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 687.0 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 75.8 |
| PASS 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 483.5 |
