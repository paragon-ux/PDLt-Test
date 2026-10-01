# PDLt Catalogue Run - run-20261001-132344

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-10-01T17:23:44.179950+00:00  
**Total Time:** 53.6s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 0 |
| Failed | 7 |
| **Pass Rate** | **0.0%** |
| Model calls (total / EXECUTE / repairs) | 14 / 0 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 0 / 0 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 0) |

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
| **False positives** (stage pass, wrong answer) | **7** |
|  - 01-01 | no exact partition into valid triples among 0 valid triples presented |
|  - 01-02 | missing 3 of 3 exact covers |
|  - 01-03 | no proper 4-coloring among 0 candidate colorings |
|  - 01-04 | 0 of 19 solution subsets presented |
|  - 01-05 | no valid 7x7 completion respecting the givens |
|  - 01-06 | optimal packing presented=False, First Fit=5 bins stated=False |
|  - 01-07 | no valid Hamiltonian path presented |

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
| 01-01 | combinatorial_search | CLOSED_SUCCESS | 6.1 |
| 01-02 | combinatorial_search | CLOSED_SUCCESS | 4.4 |
| 01-03 | combinatorial_search | CLOSED_SUCCESS | 4.4 |
| 01-04 | combinatorial_search | CLOSED_SUCCESS | 4.5 |
| 01-05 | combinatorial_search | CLOSED_SUCCESS | 8.1 |
| 01-06 | combinatorial_search | CLOSED_SUCCESS | 21.2 |
| 01-07 | combinatorial_search | CLOSED_SUCCESS | 4.9 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_SUCCESS |
| 01-02 | REG-011 | CLOSED_SUCCESS |
| 01-05 | REG-012 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 2 | 6.1 |
| FAIL 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 2 | 4.4 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 2 | 4.4 |
| FAIL 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | FAIL | 2 | 4.5 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 2 | 8.1 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | FAIL | 2 | 21.2 |
| FAIL 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 2 | 4.9 |
