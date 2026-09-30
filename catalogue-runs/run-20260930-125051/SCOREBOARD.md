# PDLt Catalogue Run - run-20260930-125051

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T16:50:51.700438+00:00  
**Total Time:** 141.8s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 4 |
| Failed | 3 |
| **Pass Rate** | **57.1%** |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| negative_and_impossible | 7 | 4 | 3 | 57% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 4 |
| FAIL | 3 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **2** |
|  - 13-03 | uses the nonexistent frostbitedb API |
|  - 13-07 | answers or refuses without acknowledging the knowledge limitation |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| medium | 1 | 1 | 100% |
| hard | 3 | 2 | 67% |
| adversarial | 3 | 1 | 33% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 13-02 | negative_and_impossible | WAITING_INPUT | 11.5 |
| 13-03 | negative_and_impossible | CLOSED_SUCCESS | 12.5 |
| 13-07 | negative_and_impossible | CLOSED_SUCCESS | 0.9 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 13-03 | REG-003 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Time (s) |
|----|----------|-----------|---------|--------------|----------|
| PASS 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 96.4 |
| FAIL 13-02 | negative_and_impossible | hard | WAITING_INPUT | FAIL | 11.5 |
| FAIL 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | FAIL | 12.5 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 12.8 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0.8 |
| PASS 13-06 | negative_and_impossible | medium | WAITING_INPUT | PASS | 6.8 |
| FAIL 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | FAIL | 0.9 |
