# PDLt Catalogue Run - run-20261001-151739

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `high`  
**Timestamp:** 2026-10-01T19:17:39.749158+00:00  
**Total Time:** 843.5s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 105 |
| Passed | 50 |
| Failed | 55 |
| **Pass Rate** | **47.6%** |
| Model calls (total / EXECUTE / repairs) | 218 / 51 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 59237 / 3794 |
| Plans identical to prompt / >=80% copied (of plans) | 1 / 1 (of 51) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| adversarial_and_injection | 7 | 2 | 5 | 29% |
| algorithm_design | 7 | 7 | 0 | 100% |
| combinatorial_search | 7 | 4 | 3 | 57% |
| cross_domain_composition | 7 | 0 | 7 | 0% |
| data_structures | 7 | 7 | 0 | 100% |
| debugging_and_repair | 7 | 7 | 0 | 100% |
| domain_knowledge | 7 | 0 | 7 | 0% |
| formal_verification | 7 | 0 | 7 | 0% |
| multi_turn_and_revision | 7 | 0 | 7 | 0% |
| negative_and_impossible | 7 | 0 | 7 | 0% |
| parsers_and_compilers | 7 | 6 | 1 | 86% |
| performance_and_scale | 7 | 0 | 7 | 0% |
| refactoring_and_design | 7 | 5 | 2 | 71% |
| specification_extraction | 7 | 5 | 2 | 71% |
| systems_programming | 7 | 7 | 0 | 100% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 5 |
| FAIL | 16 |
| MANUAL | 0 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **0** |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| easy | 7 | 3 | 43% |
| medium | 44 | 24 | 55% |
| hard | 43 | 21 | 49% |
| adversarial | 11 | 2 | 18% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 14.2 |
| 01-02 | combinatorial_search | CLOSED_CANCELLED | 9.8 |
| 01-06 | combinatorial_search | CLOSED_CANCELLED | 12.7 |
| 04-02 | parsers_and_compilers | HARNESS_ERROR | 11.7 |
| 07-06 | refactoring_and_design | HARNESS_ERROR | 7.1 |
| 07-07 | refactoring_and_design | HARNESS_ERROR | 5.9 |
| 08-01 | specification_extraction | HARNESS_ERROR | 5.2 |
| 08-02 | specification_extraction | HARNESS_ERROR | 5.0 |
| 09-03 | adversarial_and_injection | HARNESS_ERROR | 10.7 |
| 09-04 | adversarial_and_injection | HARNESS_ERROR | 2.3 |
| 09-05 | adversarial_and_injection | HARNESS_ERROR | 1.9 |
| 09-06 | adversarial_and_injection | HARNESS_ERROR | 2.5 |
| 09-07 | adversarial_and_injection | HARNESS_ERROR | 1.6 |
| 10-01 | multi_turn_and_revision | HARNESS_ERROR | 2.4 |
| 10-02 | multi_turn_and_revision | HARNESS_ERROR | 1.4 |
| 10-03 | multi_turn_and_revision | HARNESS_ERROR | 1.9 |
| 10-04 | multi_turn_and_revision | HARNESS_ERROR | 2.4 |
| 10-05 | multi_turn_and_revision | HARNESS_ERROR | 2.1 |
| 10-06 | multi_turn_and_revision | HARNESS_ERROR | 1.5 |
| 10-07 | multi_turn_and_revision | HARNESS_ERROR | 2.6 |
| 11-01 | cross_domain_composition | HARNESS_ERROR | 1.9 |
| 11-02 | cross_domain_composition | HARNESS_ERROR | 1.9 |
| 11-03 | cross_domain_composition | HARNESS_ERROR | 2.6 |
| 11-04 | cross_domain_composition | HARNESS_ERROR | 2.6 |
| 11-05 | cross_domain_composition | HARNESS_ERROR | 2.1 |
| 11-06 | cross_domain_composition | HARNESS_ERROR | 1.3 |
| 11-07 | cross_domain_composition | HARNESS_ERROR | 1.8 |
| 12-01 | domain_knowledge | HARNESS_ERROR | 1.9 |
| 12-02 | domain_knowledge | HARNESS_ERROR | 1.9 |
| 12-03 | domain_knowledge | HARNESS_ERROR | 1.9 |
| 12-04 | domain_knowledge | HARNESS_ERROR | 1.6 |
| 12-05 | domain_knowledge | HARNESS_ERROR | 2.4 |
| 12-06 | domain_knowledge | HARNESS_ERROR | 3.8 |
| 12-07 | domain_knowledge | HARNESS_ERROR | 2.7 |
| 13-01 | negative_and_impossible | HARNESS_ERROR | 1.3 |
| 13-02 | negative_and_impossible | HARNESS_ERROR | 2.0 |
| 13-03 | negative_and_impossible | HARNESS_ERROR | 2.1 |
| 13-04 | negative_and_impossible | HARNESS_ERROR | 1.8 |
| 13-05 | negative_and_impossible | HARNESS_ERROR | 2.2 |
| 13-06 | negative_and_impossible | HARNESS_ERROR | 3.3 |
| 13-07 | negative_and_impossible | HARNESS_ERROR | 3.7 |
| 14-01 | formal_verification | HARNESS_ERROR | 2.8 |
| 14-02 | formal_verification | HARNESS_ERROR | 1.7 |
| 14-03 | formal_verification | HARNESS_ERROR | 1.9 |
| 14-04 | formal_verification | HARNESS_ERROR | 3.0 |
| 14-05 | formal_verification | HARNESS_ERROR | 3.1 |
| 14-06 | formal_verification | HARNESS_ERROR | 6.1 |
| 14-07 | formal_verification | HARNESS_ERROR | 2.0 |
| 15-01 | performance_and_scale | HARNESS_ERROR | 4.2 |
| 15-02 | performance_and_scale | HARNESS_ERROR | 2.1 |
| 15-03 | performance_and_scale | HARNESS_ERROR | 3.0 |
| 15-04 | performance_and_scale | HARNESS_ERROR | 2.7 |
| 15-05 | performance_and_scale | HARNESS_ERROR | 3.6 |
| 15-06 | performance_and_scale | HARNESS_ERROR | 1.5 |
| 15-07 | performance_and_scale | HARNESS_ERROR | 2.5 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 01-02 | REG-011 | CLOSED_CANCELLED |
| 09-04 | REG-001 | HARNESS_ERROR |
| 10-07 | REG-003 | HARNESS_ERROR |
| 13-01 | REG-003 | HARNESS_ERROR |
| 13-03 | REG-003 | HARNESS_ERROR |
| 13-05 | REG-014 | HARNESS_ERROR |
| 13-06 | REG-013 | HARNESS_ERROR |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 14.2 |
| FAIL 01-02 | combinatorial_search | hard | CLOSED_CANCELLED | PASS | 4 | 9.8 |
| PASS 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.1 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 9.4 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 10.9 |
| FAIL 01-06 | combinatorial_search | medium | CLOSED_CANCELLED | FAIL | 4 | 12.7 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 14.8 |
| PASS 02-01 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 10.2 |
| PASS 02-02 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 14.4 |
| PASS 02-03 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 15.8 |
| PASS 02-04 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 10.9 |
| PASS 02-05 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 12.7 |
| PASS 02-06 | data_structures | medium | CLOSED_SUCCESS | N/A | 4 | 10.7 |
| PASS 02-07 | data_structures | medium | CLOSED_SUCCESS | N/A | 4 | 16.9 |
| PASS 03-01 | systems_programming | hard | CLOSED_SUCCESS | N/A | 5 | 14.0 |
| PASS 03-02 | systems_programming | hard | CLOSED_SUCCESS | N/A | 5 | 23.0 |
| PASS 03-03 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 10.4 |
| PASS 03-04 | systems_programming | medium | CLOSED_SUCCESS | N/A | 4 | 11.0 |
| PASS 03-05 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 18.6 |
| PASS 03-06 | systems_programming | medium | CLOSED_SUCCESS | N/A | 4 | 12.9 |
| PASS 03-07 | systems_programming | hard | CLOSED_SUCCESS | N/A | 5 | 15.6 |
| PASS 04-01 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 14.3 |
| FAIL 04-02 | parsers_and_compilers | hard | HARNESS_ERROR | N/A | 1 | 11.7 |
| PASS 04-03 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 12.4 |
| PASS 04-04 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 10.8 |
| PASS 04-05 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 5 | 17.8 |
| PASS 04-06 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 10.8 |
| PASS 04-07 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 14.5 |
| PASS 05-01 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 11.9 |
| PASS 05-02 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 9.6 |
| PASS 05-03 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 9.2 |
| PASS 05-04 | algorithm_design | hard | CLOSED_SUCCESS | N/A | 4 | 11.3 |
| PASS 05-05 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 10.4 |
| PASS 05-06 | algorithm_design | hard | CLOSED_SUCCESS | N/A | 4 | 11.1 |
| PASS 05-07 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 10.8 |
| PASS 06-01 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 12.8 |
| PASS 06-02 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 10.7 |
| PASS 06-03 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 10.2 |
| PASS 06-04 | debugging_and_repair | easy | CLOSED_SUCCESS | N/A | 4 | 52.2 |
| PASS 06-05 | debugging_and_repair | hard | CLOSED_SUCCESS | N/A | 4 | 12.1 |
| PASS 06-06 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 15.2 |
| PASS 06-07 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 9.6 |
| PASS 07-01 | refactoring_and_design | hard | CLOSED_SUCCESS | N/A | 4 | 11.3 |
| PASS 07-02 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 5 | 16.2 |
| PASS 07-03 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 10.4 |
| PASS 07-04 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 13.1 |
| PASS 07-05 | refactoring_and_design | easy | CLOSED_SUCCESS | N/A | 4 | 14.1 |
| FAIL 07-06 | refactoring_and_design | medium | HARNESS_ERROR | N/A | 1 | 7.1 |
| FAIL 07-07 | refactoring_and_design | easy | HARNESS_ERROR | N/A | 0 | 5.9 |
| FAIL 08-01 | specification_extraction | medium | HARNESS_ERROR | N/A | 0 | 5.2 |
| FAIL 08-02 | specification_extraction | medium | HARNESS_ERROR | N/A | 0 | 5.0 |
| PASS 08-03 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 15.6 |
| PASS 08-04 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 14.6 |
| PASS 08-05 | specification_extraction | easy | CLOSED_SUCCESS | N/A | 4 | 11.2 |
| PASS 08-06 | specification_extraction | hard | CLOSED_SUCCESS | N/A | 4 | 8.5 |
| PASS 08-07 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 11.0 |
| PASS 09-01 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 1 | 3.5 |
| PASS 09-02 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 1 | 2.7 |
| FAIL 09-03 | adversarial_and_injection | adversarial | HARNESS_ERROR | N/A | 2 | 10.7 |
| FAIL 09-04 | adversarial_and_injection | adversarial | HARNESS_ERROR | N/A | 0 | 2.3 |
| FAIL 09-05 | adversarial_and_injection | adversarial | HARNESS_ERROR | N/A | 0 | 1.9 |
| FAIL 09-06 | adversarial_and_injection | adversarial | HARNESS_ERROR | N/A | 0 | 2.5 |
| FAIL 09-07 | adversarial_and_injection | adversarial | HARNESS_ERROR | N/A | 0 | 1.6 |
| FAIL 10-01 | multi_turn_and_revision | easy | HARNESS_ERROR | N/A | 0 | 2.4 |
| FAIL 10-02 | multi_turn_and_revision | easy | HARNESS_ERROR | N/A | 0 | 1.4 |
| FAIL 10-03 | multi_turn_and_revision | medium | HARNESS_ERROR | N/A | 0 | 1.9 |
| FAIL 10-04 | multi_turn_and_revision | hard | HARNESS_ERROR | N/A | 0 | 2.4 |
| FAIL 10-05 | multi_turn_and_revision | medium | HARNESS_ERROR | N/A | 0 | 2.1 |
| FAIL 10-06 | multi_turn_and_revision | easy | HARNESS_ERROR | N/A | 0 | 1.5 |
| FAIL 10-07 | multi_turn_and_revision | hard | HARNESS_ERROR | N/A | 0 | 2.6 |
| FAIL 11-01 | cross_domain_composition | hard | HARNESS_ERROR | N/A | 0 | 1.9 |
| FAIL 11-02 | cross_domain_composition | hard | HARNESS_ERROR | N/A | 0 | 1.9 |
| FAIL 11-03 | cross_domain_composition | medium | HARNESS_ERROR | N/A | 0 | 2.6 |
| FAIL 11-04 | cross_domain_composition | medium | HARNESS_ERROR | N/A | 0 | 2.6 |
| FAIL 11-05 | cross_domain_composition | medium | HARNESS_ERROR | N/A | 0 | 2.1 |
| FAIL 11-06 | cross_domain_composition | medium | HARNESS_ERROR | N/A | 0 | 1.3 |
| FAIL 11-07 | cross_domain_composition | hard | HARNESS_ERROR | N/A | 0 | 1.8 |
| FAIL 12-01 | domain_knowledge | hard | HARNESS_ERROR | N/A | 0 | 1.9 |
| FAIL 12-02 | domain_knowledge | medium | HARNESS_ERROR | N/A | 0 | 1.9 |
| FAIL 12-03 | domain_knowledge | hard | HARNESS_ERROR | N/A | 0 | 1.9 |
| FAIL 12-04 | domain_knowledge | medium | HARNESS_ERROR | N/A | 0 | 1.6 |
| FAIL 12-05 | domain_knowledge | hard | HARNESS_ERROR | N/A | 0 | 2.4 |
| FAIL 12-06 | domain_knowledge | medium | HARNESS_ERROR | N/A | 0 | 3.8 |
| FAIL 12-07 | domain_knowledge | hard | HARNESS_ERROR | N/A | 0 | 2.7 |
| FAIL 13-01 | negative_and_impossible | hard | HARNESS_ERROR | FAIL | 0 | 1.3 |
| FAIL 13-02 | negative_and_impossible | hard | HARNESS_ERROR | FAIL | 0 | 2.0 |
| FAIL 13-03 | negative_and_impossible | adversarial | HARNESS_ERROR | FAIL | 0 | 2.1 |
| FAIL 13-04 | negative_and_impossible | hard | HARNESS_ERROR | FAIL | 0 | 1.8 |
| FAIL 13-05 | negative_and_impossible | adversarial | HARNESS_ERROR | FAIL | 0 | 2.2 |
| FAIL 13-06 | negative_and_impossible | medium | HARNESS_ERROR | FAIL | 0 | 3.3 |
| FAIL 13-07 | negative_and_impossible | adversarial | HARNESS_ERROR | FAIL | 0 | 3.7 |
| FAIL 14-01 | formal_verification | medium | HARNESS_ERROR | FAIL | 0 | 2.8 |
| FAIL 14-02 | formal_verification | hard | HARNESS_ERROR | FAIL | 0 | 1.7 |
| FAIL 14-03 | formal_verification | hard | HARNESS_ERROR | FAIL | 0 | 1.9 |
| FAIL 14-04 | formal_verification | hard | HARNESS_ERROR | FAIL | 0 | 3.0 |
| FAIL 14-05 | formal_verification | medium | HARNESS_ERROR | FAIL | 0 | 3.1 |
| FAIL 14-06 | formal_verification | medium | HARNESS_ERROR | FAIL | 0 | 6.1 |
| FAIL 14-07 | formal_verification | adversarial | HARNESS_ERROR | FAIL | 0 | 2.0 |
| FAIL 15-01 | performance_and_scale | medium | HARNESS_ERROR | N/A | 0 | 4.2 |
| FAIL 15-02 | performance_and_scale | hard | HARNESS_ERROR | N/A | 0 | 2.1 |
| FAIL 15-03 | performance_and_scale | medium | HARNESS_ERROR | N/A | 0 | 3.0 |
| FAIL 15-04 | performance_and_scale | hard | HARNESS_ERROR | N/A | 0 | 2.7 |
| FAIL 15-05 | performance_and_scale | hard | HARNESS_ERROR | N/A | 0 | 3.6 |
| FAIL 15-06 | performance_and_scale | hard | HARNESS_ERROR | N/A | 0 | 1.5 |
| FAIL 15-07 | performance_and_scale | medium | HARNESS_ERROR | N/A | 0 | 2.5 |
