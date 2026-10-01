# PDLt Catalogue Run - run-20260930-202254

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `medium`  
**Timestamp:** 2026-10-01T00:22:54.099851+00:00  
**Total Time:** 28.3s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 1 |
| Passed | 0 |
| Failed | 1 |
| **Pass Rate** | **0.0%** |
| Model calls (total / EXECUTE / repairs) | 5 / 2 / 1 |
| Plans identical to prompt / >=80% copied (of plans) | 0 / 0 (of 1) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| combinatorial_search | 1 | 0 | 1 | 0% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 0 |
| FAIL | 1 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| hard | 1 | 0 | 0% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 28.3 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 28.3 |
