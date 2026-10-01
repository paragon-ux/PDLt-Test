# PDLt Catalogue Run - run-20261001-135851

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-10-01T17:58:51.357382+00:00  
**Total Time:** 37.6s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 0 |
| Failed | 7 |
| **Pass Rate** | **0.0%** |
| Model calls (total / EXECUTE / repairs) | 23 / 0 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 0 / 0 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 7) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 7 | 0 | 7 | 0% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 0 |
| FAIL | 7 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 0 | 0% |
| hard | 5 | 0 | 0% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | HARNESS_ERROR | 6.8 |
| 01-02 | combinatorial_search | HARNESS_ERROR | 5.4 |
| 01-03 | combinatorial_search | HARNESS_ERROR | 6.5 |
| 01-04 | combinatorial_search | HARNESS_ERROR | 4.1 |
| 01-05 | combinatorial_search | HARNESS_ERROR | 5.2 |
| 01-06 | combinatorial_search | HARNESS_ERROR | 5.0 |
| 01-07 | combinatorial_search | HARNESS_ERROR | 4.6 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | HARNESS_ERROR |
| 01-02 | REG-011 | HARNESS_ERROR |
| 01-05 | REG-012 | HARNESS_ERROR |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | HARNESS_ERROR | FAIL | 4 | 6.8 |
| FAIL 01-02 | combinatorial_search | hard | HARNESS_ERROR | FAIL | 3 | 5.4 |
| FAIL 01-03 | combinatorial_search | hard | HARNESS_ERROR | FAIL | 3 | 6.5 |
| FAIL 01-04 | combinatorial_search | medium | HARNESS_ERROR | FAIL | 3 | 4.1 |
| FAIL 01-05 | combinatorial_search | hard | HARNESS_ERROR | FAIL | 3 | 5.2 |
| FAIL 01-06 | combinatorial_search | medium | HARNESS_ERROR | FAIL | 4 | 5.0 |
| FAIL 01-07 | combinatorial_search | hard | HARNESS_ERROR | FAIL | 3 | 4.6 |
