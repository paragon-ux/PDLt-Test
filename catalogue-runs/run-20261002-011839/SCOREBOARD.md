# PDLt Catalogue Run - run-20261002-011839

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-10-02T05:18:39.383818+00:00  
**Total Time:** 42.2s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 3 |
| Failed | 4 |
| **Pass Rate** | **42.9%** |
| Model calls (total / EXECUTE / repairs) | 30 / 7 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 4197 / 955 |
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
| **False positives** (stage pass, wrong answer) | **3** |
|  - 01-03 | no proper 4-coloring among 0 candidate colorings |
|  - 01-05 | no valid 7x7 completion respecting the givens |
|  - 01-07 | no valid Hamiltonian path presented |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 2 | 2 | 100% |
| hard | 5 | 1 | 20% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 5.5 |
| 01-03 | combinatorial_search | CLOSED_SUCCESS | 7.4 |
| 01-05 | combinatorial_search | CLOSED_SUCCESS | 6.0 |
| 01-07 | combinatorial_search | CLOSED_SUCCESS | 6.1 |

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
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 5.5 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 4.7 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 5 | 7.4 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 6.2 |
| FAIL 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 4 | 6.0 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 6.2 |
| FAIL 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 4 | 6.1 |
