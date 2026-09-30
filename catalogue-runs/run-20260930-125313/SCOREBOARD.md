# PDLt Catalogue Run - run-20260930-125313

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T16:53:13.635386+00:00  
**Total Time:** 121.2s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 7 |
| Passed | 6 |
| Failed | 1 |
| **Pass Rate** | **85.7%** |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| multi_turn_and_revision | 7 | 6 | 1 | 86% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 0 |
| FAIL | 0 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| easy | 3 | 2 | 67% |
| medium | 2 | 2 | 100% |
| hard | 2 | 2 | 100% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 10-02 | multi_turn_and_revision | WAITING_INPUT | 8.4 |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Time (s) |
|----|----------|-----------|---------|----------|
| PASS 10-01 | multi_turn_and_revision | easy | CLOSED_SUCCESS | 16.8 |
| FAIL 10-02 | multi_turn_and_revision | easy | WAITING_INPUT | 8.4 |
| PASS 10-03 | multi_turn_and_revision | medium | CLOSED_SUCCESS | 17.4 |
| PASS 10-04 | multi_turn_and_revision | hard | CLOSED_SUCCESS | 19.6 |
| PASS 10-05 | multi_turn_and_revision | medium | CLOSED_SUCCESS | 29.4 |
| PASS 10-06 | multi_turn_and_revision | easy | CLOSED_SUCCESS | 11.1 |
| PASS 10-07 | multi_turn_and_revision | hard | CLOSED_SUCCESS | 18.5 |
