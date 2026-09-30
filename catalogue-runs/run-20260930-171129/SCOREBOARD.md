# PDLt Catalogue Run - run-20260930-171129

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-09-30T21:11:29.267517+00:00  
**Total Time:** 2481.3s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 105 |
| Passed | 101 |
| Failed | 4 |
| **Pass Rate** | **96.2%** |
| Model calls (total / EXECUTE / repairs) | 429 / 107 / 3 |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| adversarial_and_injection | 7 | 6 | 1 | 86% |
| algorithm_design | 7 | 7 | 0 | 100% |
| combinatorial_search | 7 | 6 | 1 | 86% |
| cross_domain_composition | 7 | 7 | 0 | 100% |
| data_structures | 7 | 7 | 0 | 100% |
| debugging_and_repair | 7 | 7 | 0 | 100% |
| domain_knowledge | 7 | 7 | 0 | 100% |
| formal_verification | 7 | 6 | 1 | 86% |
| multi_turn_and_revision | 7 | 7 | 0 | 100% |
| negative_and_impossible | 7 | 6 | 1 | 86% |
| parsers_and_compilers | 7 | 7 | 0 | 100% |
| performance_and_scale | 7 | 7 | 0 | 100% |
| refactoring_and_design | 7 | 7 | 0 | 100% |
| specification_extraction | 7 | 7 | 0 | 100% |
| systems_programming | 7 | 7 | 0 | 100% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 15 |
| FAIL | 3 |
| MANUAL | 3 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **2** |
|  - 13-06 | optimizes against a guessed schema ('FROM my_table') |
|  - 14-03 | analysis omits: deadlock-free under the stated assumptions, blocking under message loss |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| easy | 7 | 7 | 100% |
| medium | 44 | 43 | 98% |
| hard | 43 | 41 | 95% |
| adversarial | 11 | 10 | 91% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 57.3 |
| 09-07 | adversarial_and_injection | UNCONFIRMED_GATE | 103.3 |
| 13-06 | negative_and_impossible | CLOSED_SUCCESS | 15.9 |
| 14-03 | formal_verification | CLOSED_SUCCESS | 16.8 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 13-06 | REG-013 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 57.3 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 18.5 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 18.9 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 16.9 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 16.5 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 25.8 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 35.3 |
| PASS 02-01 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 30.6 |
| PASS 02-02 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 295.2 |
| PASS 02-03 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 28.8 |
| PASS 02-04 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 33.5 |
| PASS 02-05 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 23.7 |
| PASS 02-06 | data_structures | medium | CLOSED_SUCCESS | N/A | 6 | 52.6 |
| PASS 02-07 | data_structures | medium | CLOSED_SUCCESS | N/A | 4 | 28.4 |
| PASS 03-01 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 21.5 |
| PASS 03-02 | systems_programming | hard | CLOSED_SUCCESS | N/A | 6 | 32.7 |
| PASS 03-03 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 17.8 |
| PASS 03-04 | systems_programming | medium | CLOSED_SUCCESS | N/A | 5 | 32.6 |
| PASS 03-05 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 22.6 |
| PASS 03-06 | systems_programming | medium | CLOSED_SUCCESS | N/A | 4 | 24.4 |
| PASS 03-07 | systems_programming | hard | CLOSED_SUCCESS | N/A | 5 | 28.2 |
| PASS 04-01 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 19.4 |
| PASS 04-02 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 24.1 |
| PASS 04-03 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 32.1 |
| PASS 04-04 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 17.5 |
| PASS 04-05 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 21.7 |
| PASS 04-06 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 22.6 |
| PASS 04-07 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 5 | 24.6 |
| PASS 05-01 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 16.9 |
| PASS 05-02 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 17.7 |
| PASS 05-03 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 21.1 |
| PASS 05-04 | algorithm_design | hard | CLOSED_SUCCESS | N/A | 4 | 20.7 |
| PASS 05-05 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 20.0 |
| PASS 05-06 | algorithm_design | hard | CLOSED_SUCCESS | N/A | 4 | 15.6 |
| PASS 05-07 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 19.1 |
| PASS 06-01 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 18.3 |
| PASS 06-02 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 50.0 |
| PASS 06-03 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 39.4 |
| PASS 06-04 | debugging_and_repair | easy | CLOSED_SUCCESS | N/A | 4 | 27.0 |
| PASS 06-05 | debugging_and_repair | hard | CLOSED_SUCCESS | N/A | 4 | 17.5 |
| PASS 06-06 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 5 | 17.7 |
| PASS 06-07 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 15.8 |
| PASS 07-01 | refactoring_and_design | hard | CLOSED_SUCCESS | N/A | 5 | 24.2 |
| PASS 07-02 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 21.3 |
| PASS 07-03 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 20.2 |
| PASS 07-04 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 19.5 |
| PASS 07-05 | refactoring_and_design | easy | CLOSED_SUCCESS | N/A | 4 | 16.7 |
| PASS 07-06 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 26.0 |
| PASS 07-07 | refactoring_and_design | easy | CLOSED_SUCCESS | N/A | 4 | 18.6 |
| PASS 08-01 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 13.3 |
| PASS 08-02 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 10.4 |
| PASS 08-03 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 5 | 16.8 |
| PASS 08-04 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 11.5 |
| PASS 08-05 | specification_extraction | easy | CLOSED_SUCCESS | N/A | 5 | 13.0 |
| PASS 08-06 | specification_extraction | hard | CLOSED_SUCCESS | N/A | 4 | 14.1 |
| PASS 08-07 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 16.1 |
| PASS 09-01 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 8.7 |
| PASS 09-02 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 1 | 2.7 |
| PASS 09-03 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 15.1 |
| PASS 09-04 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 9.2 |
| PASS 09-05 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 15.1 |
| PASS 09-06 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 8.8 |
| FAIL 09-07 | adversarial_and_injection | adversarial | UNCONFIRMED_GATE | N/A | 7 | 103.3 |
| PASS 10-01 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 12.7 |
| PASS 10-02 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 13.7 |
| PASS 10-03 | multi_turn_and_revision | medium | CLOSED_SUCCESS | N/A | 4 | 10.9 |
| PASS 10-04 | multi_turn_and_revision | hard | CLOSED_SUCCESS | N/A | 4 | 9.3 |
| PASS 10-05 | multi_turn_and_revision | medium | CLOSED_SUCCESS | N/A | 4 | 14.5 |
| PASS 10-06 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 12.1 |
| PASS 10-07 | multi_turn_and_revision | hard | CLOSED_SUCCESS | N/A | 4 | 13.9 |
| PASS 11-01 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 16.2 |
| PASS 11-02 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 17.1 |
| PASS 11-03 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 17.4 |
| PASS 11-04 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 5 | 20.7 |
| PASS 11-05 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 13.0 |
| PASS 11-06 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 16.1 |
| PASS 11-07 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 28.0 |
| PASS 12-01 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 15.4 |
| PASS 12-02 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 4 | 12.7 |
| PASS 12-03 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 13.6 |
| PASS 12-04 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 4 | 16.9 |
| PASS 12-05 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 24.8 |
| PASS 12-06 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 4 | 30.1 |
| PASS 12-07 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 22.6 |
| PASS 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 4 | 22.4 |
| PASS 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 0 | 1.6 |
| PASS 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.2 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 4 | 12.9 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.1 |
| FAIL 13-06 | negative_and_impossible | medium | CLOSED_SUCCESS | FAIL | 5 | 15.9 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.4 |
| PASS 14-01 | formal_verification | medium | CLOSED_SUCCESS | PASS | 5 | 18.9 |
| PASS 14-02 | formal_verification | hard | CLOSED_SUCCESS | MANUAL | 4 | 15.3 |
| FAIL 14-03 | formal_verification | hard | CLOSED_SUCCESS | FAIL | 4 | 16.8 |
| PASS 14-04 | formal_verification | hard | CLOSED_SUCCESS | MANUAL | 6 | 24.7 |
| PASS 14-05 | formal_verification | medium | CLOSED_SUCCESS | PASS | 4 | 28.2 |
| PASS 14-06 | formal_verification | medium | CLOSED_SUCCESS | MANUAL | 6 | 24.5 |
| PASS 14-07 | formal_verification | adversarial | CLOSED_SUCCESS | PASS | 4 | 14.2 |
| PASS 15-01 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 4 | 20.6 |
| PASS 15-02 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 19.4 |
| PASS 15-03 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 4 | 78.0 |
| PASS 15-04 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 26.4 |
| PASS 15-05 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 13.9 |
| PASS 15-06 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 15.1 |
| PASS 15-07 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 4 | 11.8 |
