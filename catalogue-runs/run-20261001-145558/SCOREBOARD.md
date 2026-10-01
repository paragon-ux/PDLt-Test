# PDLt Catalogue Run - run-20261001-145558

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `low`  
**Timestamp:** 2026-10-01T18:55:58.962165+00:00  
**Total Time:** 784.2s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 105 |
| Passed | 100 |
| Failed | 5 |
| **Pass Rate** | **95.2%** |
| Model calls (total / EXECUTE / repairs) | 418 / 99 / 0 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 97959 / 6499 |
| Plans identical to prompt / >=80% copied (of plans) | 6 / 10 (of 99) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| adversarial_and_injection | 7 | 7 | 0 | 100% |
| algorithm_design | 7 | 7 | 0 | 100% |
| combinatorial_search | 7 | 5 | 2 | 71% |
| cross_domain_composition | 7 | 7 | 0 | 100% |
| data_structures | 7 | 7 | 0 | 100% |
| debugging_and_repair | 7 | 7 | 0 | 100% |
| domain_knowledge | 7 | 7 | 0 | 100% |
| formal_verification | 7 | 6 | 1 | 86% |
| multi_turn_and_revision | 7 | 7 | 0 | 100% |
| negative_and_impossible | 7 | 5 | 2 | 71% |
| parsers_and_compilers | 7 | 7 | 0 | 100% |
| performance_and_scale | 7 | 7 | 0 | 100% |
| refactoring_and_design | 7 | 7 | 0 | 100% |
| specification_extraction | 7 | 7 | 0 | 100% |
| systems_programming | 7 | 7 | 0 | 100% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 14 |
| FAIL | 4 |
| MANUAL | 3 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **3** |
|  - 13-01 | does not report unsatisfiability |
|  - 13-06 | optimizes against a guessed schema ('FROM your_table') |
|  - 14-07 | claims a termination proof for an open problem |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| easy | 7 | 7 | 100% |
| medium | 44 | 43 | 98% |
| hard | 43 | 40 | 93% |
| adversarial | 11 | 10 | 91% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 19.5 |
| 01-03 | combinatorial_search | CLOSED_CANCELLED | 8.6 |
| 13-01 | negative_and_impossible | CLOSED_SUCCESS | 6.0 |
| 13-06 | negative_and_impossible | CLOSED_SUCCESS | 6.7 |
| 14-07 | formal_verification | CLOSED_SUCCESS | 8.3 |

---

## KNOWN REGRESSIONS HIT

| ID | Regression Ref | Verdict |
|----|---------------|---------|
| 01-01 | REG-003 | CLOSED_CANCELLED |
| 13-01 | REG-003 | CLOSED_SUCCESS |
| 13-06 | REG-013 | CLOSED_SUCCESS |

---

## Per-Prompt Results

| ID | Category | Difficulty | Verdict | Ground truth | Model calls | Time (s) |
|----|----------|-----------|---------|--------------|-------------|----------|
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 4 | 19.5 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 11.2 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_CANCELLED | PASS | 4 | 8.6 |
| PASS 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 4 | 9.8 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 6.7 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 8.0 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 6.2 |
| PASS 02-01 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 10.4 |
| PASS 02-02 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 7.5 |
| PASS 02-03 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 9.4 |
| PASS 02-04 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 10.2 |
| PASS 02-05 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 6.8 |
| PASS 02-06 | data_structures | medium | CLOSED_SUCCESS | N/A | 5 | 7.5 |
| PASS 02-07 | data_structures | medium | CLOSED_SUCCESS | N/A | 5 | 9.8 |
| PASS 03-01 | systems_programming | hard | CLOSED_SUCCESS | N/A | 5 | 8.1 |
| PASS 03-02 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 7.6 |
| PASS 03-03 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 6.9 |
| PASS 03-04 | systems_programming | medium | CLOSED_SUCCESS | N/A | 4 | 5.9 |
| PASS 03-05 | systems_programming | hard | CLOSED_SUCCESS | N/A | 5 | 15.7 |
| PASS 03-06 | systems_programming | medium | CLOSED_SUCCESS | N/A | 4 | 9.4 |
| PASS 03-07 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 10.1 |
| PASS 04-01 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 7.6 |
| PASS 04-02 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 8.9 |
| PASS 04-03 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 12.4 |
| PASS 04-04 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 8.6 |
| PASS 04-05 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 5 | 13.5 |
| PASS 04-06 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 6.8 |
| PASS 04-07 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 7.3 |
| PASS 05-01 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 7.2 |
| PASS 05-02 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 5 | 9.6 |
| PASS 05-03 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 6.4 |
| PASS 05-04 | algorithm_design | hard | CLOSED_SUCCESS | N/A | 4 | 8.6 |
| PASS 05-05 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 6.5 |
| PASS 05-06 | algorithm_design | hard | CLOSED_SUCCESS | N/A | 4 | 5.8 |
| PASS 05-07 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 7.9 |
| PASS 06-01 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 12.5 |
| PASS 06-02 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 5 | 10.9 |
| PASS 06-03 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 8.6 |
| PASS 06-04 | debugging_and_repair | easy | CLOSED_SUCCESS | N/A | 4 | 16.8 |
| PASS 06-05 | debugging_and_repair | hard | CLOSED_SUCCESS | N/A | 4 | 6.8 |
| PASS 06-06 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 9.6 |
| PASS 06-07 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 6.6 |
| PASS 07-01 | refactoring_and_design | hard | CLOSED_SUCCESS | N/A | 4 | 7.9 |
| PASS 07-02 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 8.3 |
| PASS 07-03 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 6.0 |
| PASS 07-04 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 6.4 |
| PASS 07-05 | refactoring_and_design | easy | CLOSED_SUCCESS | N/A | 4 | 7.0 |
| PASS 07-06 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 6.9 |
| PASS 07-07 | refactoring_and_design | easy | CLOSED_SUCCESS | N/A | 4 | 6.7 |
| PASS 08-01 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 7.0 |
| PASS 08-02 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 7.0 |
| PASS 08-03 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 6.8 |
| PASS 08-04 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 6.4 |
| PASS 08-05 | specification_extraction | easy | CLOSED_SUCCESS | N/A | 4 | 6.1 |
| PASS 08-06 | specification_extraction | hard | CLOSED_SUCCESS | N/A | 4 | 6.5 |
| PASS 08-07 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 6.5 |
| PASS 09-01 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 1 | 3.6 |
| PASS 09-02 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 5.2 |
| PASS 09-03 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 6.5 |
| PASS 09-04 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 5 | 7.2 |
| PASS 09-05 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 5.3 |
| PASS 09-06 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 7 | 10.1 |
| PASS 09-07 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 1 | 2.9 |
| PASS 10-01 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 6.8 |
| PASS 10-02 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 6.2 |
| PASS 10-03 | multi_turn_and_revision | medium | CLOSED_SUCCESS | N/A | 4 | 7.8 |
| PASS 10-04 | multi_turn_and_revision | hard | CLOSED_SUCCESS | N/A | 4 | 7.3 |
| PASS 10-05 | multi_turn_and_revision | medium | CLOSED_SUCCESS | N/A | 4 | 8.8 |
| PASS 10-06 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 6.1 |
| PASS 10-07 | multi_turn_and_revision | hard | CLOSED_SUCCESS | N/A | 4 | 7.4 |
| PASS 11-01 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 7.0 |
| PASS 11-02 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 4.6 |
| PASS 11-03 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 10.3 |
| PASS 11-04 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 6.0 |
| PASS 11-05 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 6.0 |
| PASS 11-06 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 6.5 |
| PASS 11-07 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 7.0 |
| PASS 12-01 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 6.1 |
| PASS 12-02 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 5 | 6.9 |
| PASS 12-03 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 6.6 |
| PASS 12-04 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 4 | 5.4 |
| PASS 12-05 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 5 | 8.3 |
| PASS 12-06 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 4 | 7.8 |
| PASS 12-07 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 5.4 |
| FAIL 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | FAIL | 4 | 6.0 |
| PASS 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 0 | 2.4 |
| PASS 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.7 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 4 | 5.8 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 2.0 |
| FAIL 13-06 | negative_and_impossible | medium | CLOSED_SUCCESS | FAIL | 4 | 6.7 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.4 |
| PASS 14-01 | formal_verification | medium | CLOSED_SUCCESS | PASS | 4 | 6.2 |
| PASS 14-02 | formal_verification | hard | CLOSED_SUCCESS | MANUAL | 4 | 6.0 |
| PASS 14-03 | formal_verification | hard | CLOSED_SUCCESS | PASS | 4 | 6.0 |
| PASS 14-04 | formal_verification | hard | CLOSED_SUCCESS | MANUAL | 5 | 7.5 |
| PASS 14-05 | formal_verification | medium | CLOSED_SUCCESS | PASS | 4 | 5.1 |
| PASS 14-06 | formal_verification | medium | CLOSED_SUCCESS | MANUAL | 6 | 8.6 |
| FAIL 14-07 | formal_verification | adversarial | CLOSED_SUCCESS | FAIL | 4 | 8.3 |
| PASS 15-01 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 4 | 6.0 |
| PASS 15-02 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 6.2 |
| PASS 15-03 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 4 | 6.3 |
| PASS 15-04 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 6.6 |
| PASS 15-05 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 6.8 |
| PASS 15-06 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 8.4 |
| PASS 15-07 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 4 | 5.6 |
