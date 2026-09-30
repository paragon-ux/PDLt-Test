# PDLt Catalogue Run - run-20260930-161239

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T20:12:39.352489+00:00  
**Total Time:** 266.8s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 5 |
| Failed | 2 |
| **Pass Rate** | **71.4%** |
| Model calls (total / EXECUTE / repairs) | 35 / 12 / 5 |

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
| **False positives** (stage pass, wrong answer) | **2** |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |
|  - 01-03 | no proper 4-coloring among 3 candidate colorings |

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
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 31.7 |
| 01-03 | combinatorial_search | CLOSED_SUCCESS | 45.1 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 5 | 31.7 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 52.0 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 6 | 45.1 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 34.5 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 32.1 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 37.0 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 34.2 |
