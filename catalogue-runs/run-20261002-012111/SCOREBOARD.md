# PDLt Catalogue Run - run-20261002-012111

**Model:** `openai/gpt-oss-120b`  
**Reasoning Effort:** `harness-default`  
**Timestamp:** 2026-10-02T05:21:11.244734+00:00  
**Total Time:** 1151.7s  

---

## Summary

| Metric | Value |
|--------|-------|
| Total Prompts | 105 |
| Passed | 97 |
| Failed | 8 |
| **Pass Rate** | **92.4%** |
| Model calls (total / EXECUTE / repairs) | 406 / 99 / 4 |
| EXECUTE output tokens / provider-reported reasoning (all prompts) | 91397 / 5961 |
| Plans identical to prompt / >=80% copied (of plans) | 4 / 4 (of 95) |

---

## By Category

| Category | Total | Pass | Fail | Rate |
|----------|-------|------|------|------|
| adversarial_and_injection | 7 | 6 | 1 | 86% |
| algorithm_design | 7 | 7 | 0 | 100% |
| combinatorial_search | 7 | 4 | 3 | 57% |
| cross_domain_composition | 7 | 7 | 0 | 100% |
| data_structures | 7 | 7 | 0 | 100% |
| debugging_and_repair | 7 | 7 | 0 | 100% |
| domain_knowledge | 7 | 7 | 0 | 100% |
| formal_verification | 7 | 6 | 1 | 86% |
| multi_turn_and_revision | 7 | 7 | 0 | 100% |
| negative_and_impossible | 7 | 5 | 2 | 71% |
| parsers_and_compilers | 7 | 6 | 1 | 86% |
| performance_and_scale | 7 | 7 | 0 | 100% |
| refactoring_and_design | 7 | 7 | 0 | 100% |
| specification_extraction | 7 | 7 | 0 | 100% |
| systems_programming | 7 | 7 | 0 | 100% |

---

## Ground Truth (evaluation-plane graders)

| Grade | Count |
|-------|-------|
| PASS | 12 |
| FAIL | 6 |
| MANUAL | 3 |
| ERROR | 0 |
| **False positives** (stage pass, wrong answer) | **5** |
|  - 01-03 | no proper 4-coloring among 0 candidate colorings |
|  - 01-04 | 0 of 19 solution subsets presented |
|  - 13-01 | does not report unsatisfiability |
|  - 13-06 | optimizes against a guessed schema ('FROM your_table_name') |
|  - 14-01 | proof omits: initialization, maintenance, termination |

---

## By Difficulty

| Difficulty | Total | Pass | Rate |
|-----------|-------|------|------|
| easy | 7 | 7 | 100% |
| medium | 44 | 41 | 93% |
| hard | 43 | 39 | 91% |
| adversarial | 11 | 10 | 91% |

---

## Failures

| ID | Category | Verdict | Time (s) |
|----|----------|---------|----------|
| 01-01 | combinatorial_search | CLOSED_CANCELLED | 21.3 |
| 01-03 | combinatorial_search | CLOSED_SUCCESS | 10.0 |
| 01-04 | combinatorial_search | CLOSED_SUCCESS | 10.9 |
| 04-02 | parsers_and_compilers | HARNESS_ERROR | 12.3 |
| 09-03 | adversarial_and_injection | HARNESS_ERROR | 11.8 |
| 13-01 | negative_and_impossible | CLOSED_SUCCESS | 10.4 |
| 13-06 | negative_and_impossible | CLOSED_SUCCESS | 7.3 |
| 14-01 | formal_verification | CLOSED_SUCCESS | 7.5 |

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
| FAIL 01-01 | combinatorial_search | hard | CLOSED_CANCELLED | FAIL | 5 | 21.3 |
| PASS 01-02 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 13.6 |
| FAIL 01-03 | combinatorial_search | hard | CLOSED_SUCCESS | FAIL | 4 | 10.0 |
| FAIL 01-04 | combinatorial_search | medium | CLOSED_SUCCESS | FAIL | 5 | 10.9 |
| PASS 01-05 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 4 | 9.2 |
| PASS 01-06 | combinatorial_search | medium | CLOSED_SUCCESS | PASS | 5 | 10.8 |
| PASS 01-07 | combinatorial_search | hard | CLOSED_SUCCESS | PASS | 5 | 11.8 |
| PASS 02-01 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 8.7 |
| PASS 02-02 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 8.9 |
| PASS 02-03 | data_structures | hard | CLOSED_SUCCESS | N/A | 4 | 10.0 |
| PASS 02-04 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 14.7 |
| PASS 02-05 | data_structures | hard | CLOSED_SUCCESS | N/A | 5 | 11.5 |
| PASS 02-06 | data_structures | medium | CLOSED_SUCCESS | N/A | 4 | 10.8 |
| PASS 02-07 | data_structures | medium | CLOSED_SUCCESS | N/A | 4 | 14.4 |
| PASS 03-01 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 11.7 |
| PASS 03-02 | systems_programming | hard | CLOSED_SUCCESS | N/A | 5 | 11.6 |
| PASS 03-03 | systems_programming | hard | CLOSED_SUCCESS | N/A | 5 | 13.5 |
| PASS 03-04 | systems_programming | medium | CLOSED_SUCCESS | N/A | 5 | 12.4 |
| PASS 03-05 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 15.3 |
| PASS 03-06 | systems_programming | medium | CLOSED_SUCCESS | N/A | 4 | 14.9 |
| PASS 03-07 | systems_programming | hard | CLOSED_SUCCESS | N/A | 4 | 10.6 |
| PASS 04-01 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 10.0 |
| FAIL 04-02 | parsers_and_compilers | hard | HARNESS_ERROR | N/A | 1 | 12.3 |
| PASS 04-03 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 10.3 |
| PASS 04-04 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 8.2 |
| PASS 04-05 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 12.3 |
| PASS 04-06 | parsers_and_compilers | hard | CLOSED_SUCCESS | N/A | 4 | 16.2 |
| PASS 04-07 | parsers_and_compilers | medium | CLOSED_SUCCESS | N/A | 4 | 11.8 |
| PASS 05-01 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 10.9 |
| PASS 05-02 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 8.6 |
| PASS 05-03 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 5 | 13.7 |
| PASS 05-04 | algorithm_design | hard | CLOSED_SUCCESS | N/A | 4 | 9.9 |
| PASS 05-05 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 12.2 |
| PASS 05-06 | algorithm_design | hard | CLOSED_SUCCESS | N/A | 4 | 12.8 |
| PASS 05-07 | algorithm_design | medium | CLOSED_SUCCESS | N/A | 4 | 11.8 |
| PASS 06-01 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 9.9 |
| PASS 06-02 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 5 | 13.2 |
| PASS 06-03 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 13.9 |
| PASS 06-04 | debugging_and_repair | easy | CLOSED_SUCCESS | N/A | 4 | 23.8 |
| PASS 06-05 | debugging_and_repair | hard | CLOSED_SUCCESS | N/A | 4 | 10.0 |
| PASS 06-06 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 12.3 |
| PASS 06-07 | debugging_and_repair | medium | CLOSED_SUCCESS | N/A | 4 | 9.4 |
| PASS 07-01 | refactoring_and_design | hard | CLOSED_SUCCESS | N/A | 4 | 16.4 |
| PASS 07-02 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 13.8 |
| PASS 07-03 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 12.6 |
| PASS 07-04 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 13.1 |
| PASS 07-05 | refactoring_and_design | easy | CLOSED_SUCCESS | N/A | 4 | 10.4 |
| PASS 07-06 | refactoring_and_design | medium | CLOSED_SUCCESS | N/A | 4 | 11.8 |
| PASS 07-07 | refactoring_and_design | easy | CLOSED_SUCCESS | N/A | 4 | 12.4 |
| PASS 08-01 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 11.0 |
| PASS 08-02 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 12.5 |
| PASS 08-03 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 8.3 |
| PASS 08-04 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 7.9 |
| PASS 08-05 | specification_extraction | easy | CLOSED_SUCCESS | N/A | 5 | 12.7 |
| PASS 08-06 | specification_extraction | hard | CLOSED_SUCCESS | N/A | 4 | 7.3 |
| PASS 08-07 | specification_extraction | medium | CLOSED_SUCCESS | N/A | 4 | 10.7 |
| PASS 09-01 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 1 | 2.6 |
| PASS 09-02 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 1 | 2.9 |
| FAIL 09-03 | adversarial_and_injection | adversarial | HARNESS_ERROR | N/A | 2 | 11.8 |
| PASS 09-04 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 9.8 |
| PASS 09-05 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 4 | 9.5 |
| PASS 09-06 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 1 | 3.6 |
| PASS 09-07 | adversarial_and_injection | adversarial | CLOSED_SUCCESS | N/A | 2 | 4.9 |
| PASS 10-01 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 8.3 |
| PASS 10-02 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 9.3 |
| PASS 10-03 | multi_turn_and_revision | medium | CLOSED_SUCCESS | N/A | 4 | 10.0 |
| PASS 10-04 | multi_turn_and_revision | hard | CLOSED_SUCCESS | N/A | 4 | 9.4 |
| PASS 10-05 | multi_turn_and_revision | medium | CLOSED_SUCCESS | N/A | 4 | 7.5 |
| PASS 10-06 | multi_turn_and_revision | easy | CLOSED_SUCCESS | N/A | 4 | 6.9 |
| PASS 10-07 | multi_turn_and_revision | hard | CLOSED_SUCCESS | N/A | 4 | 8.1 |
| PASS 11-01 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 10.2 |
| PASS 11-02 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 11.1 |
| PASS 11-03 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 46.4 |
| PASS 11-04 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 9.7 |
| PASS 11-05 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 4 | 11.4 |
| PASS 11-06 | cross_domain_composition | medium | CLOSED_SUCCESS | N/A | 5 | 11.1 |
| PASS 11-07 | cross_domain_composition | hard | CLOSED_SUCCESS | N/A | 4 | 11.4 |
| PASS 12-01 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 9.3 |
| PASS 12-02 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 4 | 9.9 |
| PASS 12-03 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 8.2 |
| PASS 12-04 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 4 | 10.4 |
| PASS 12-05 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 5 | 13.5 |
| PASS 12-06 | domain_knowledge | medium | CLOSED_SUCCESS | N/A | 4 | 10.3 |
| PASS 12-07 | domain_knowledge | hard | CLOSED_SUCCESS | N/A | 4 | 12.4 |
| FAIL 13-01 | negative_and_impossible | hard | CLOSED_SUCCESS | FAIL | 4 | 10.4 |
| PASS 13-02 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 0 | 4.1 |
| PASS 13-03 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.4 |
| PASS 13-04 | negative_and_impossible | hard | CLOSED_SUCCESS | PASS | 4 | 7.5 |
| PASS 13-05 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.5 |
| FAIL 13-06 | negative_and_impossible | medium | CLOSED_SUCCESS | FAIL | 4 | 7.3 |
| PASS 13-07 | negative_and_impossible | adversarial | CLOSED_SUCCESS | PASS | 0 | 1.7 |
| FAIL 14-01 | formal_verification | medium | CLOSED_SUCCESS | FAIL | 4 | 7.5 |
| PASS 14-02 | formal_verification | hard | CLOSED_SUCCESS | MANUAL | 4 | 9.6 |
| PASS 14-03 | formal_verification | hard | CLOSED_SUCCESS | PASS | 4 | 7.5 |
| PASS 14-04 | formal_verification | hard | CLOSED_SUCCESS | MANUAL | 4 | 10.6 |
| PASS 14-05 | formal_verification | medium | CLOSED_SUCCESS | PASS | 5 | 12.4 |
| PASS 14-06 | formal_verification | medium | CLOSED_SUCCESS | MANUAL | 4 | 9.5 |
| PASS 14-07 | formal_verification | adversarial | CLOSED_SUCCESS | PASS | 4 | 10.7 |
| PASS 15-01 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 4 | 7.4 |
| PASS 15-02 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 12.3 |
| PASS 15-03 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 4 | 15.2 |
| PASS 15-04 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 9.7 |
| PASS 15-05 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 4 | 13.0 |
| PASS 15-06 | performance_and_scale | hard | CLOSED_SUCCESS | N/A | 5 | 20.7 |
| PASS 15-07 | performance_and_scale | medium | CLOSED_SUCCESS | N/A | 5 | 10.4 |
