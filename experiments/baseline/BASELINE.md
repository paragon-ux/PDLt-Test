# Catalogue baseline (regraded, read-only)

Past runs graded with the current graders: FA2, hidden tests for the coding prompts. Pass = the run reached its expected stage and the grader returned PASS; the rate is over prompts a grader decides (PASS or FAIL).

| Run | Model | Effort | Prompts | Decided | Passed | Decided pass rate | Pending (MANUAL) |
|---|---|---|---|---|---|---|---|
| run-20261002-012111 | openai/gpt-oss-120b | harness-default | 105 | 47 | 20 | 42.5% | 3 |
| run-20261001-151739 | openai/gpt-oss-120b | high | 105 | 50 | 13 | 26.0% | 0 |
| run-20261001-145558 | openai/gpt-oss-120b | low | 105 | 47 | 20 | 42.5% | 3 |
| run-20260930-171129 | openai/gpt-oss-120b | low | 105 | 47 | 24 | 51.1% | 3 |

## run-20261002-012111: grades that changed

| Prompt | Old | New | Reason |
|---|---|---|---|
| 02-01 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-02 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-03 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-04 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-06 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-07 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 03-02 | N/A | PASS | hidden tests: passed every hidden test |
| 03-03 | N/A | PASS | hidden tests: passed every hidden test |
| 03-05 | N/A | PASS | hidden tests: passed every hidden test |
| 03-06 | N/A | PASS | hidden tests: passed every hidden test |
| 04-01 | N/A | PASS | hidden tests: passed every hidden test |
| 04-02 | N/A | FAIL | no published deliverable |
| 04-03 | N/A | FAIL | hidden tests: matches: test_prompt_examples: AssertionError: '[0-9]+' on '123': got False, expected True, test_each_oper |
| 04-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 04-06 | N/A | FAIL | hidden tests: Compiler.compile -> VM.run: test_prompt_example: RuntimeError: Unknown stmt l, test_more_programs: Runtime |
| 04-07 | N/A | FAIL | hidden tests: matches/next_fire: test_prompt_examples: AssertionError: , test_field_syntax: AssertionError: , test_rando |
| 05-01 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-02 | N/A | FAIL | hidden tests: kahn_topological_sort: test_square_with_interior_points: TypeError: list indices must be integers or slice |
| 05-03 | N/A | FAIL | hidden tests: LCS: test_prompt_example: TypeError: 'int' object is not iterable, test_positions: TypeError: 'int' object |
| 05-04 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-06 | N/A | FAIL | hidden tests: find_median_sorted_arrays: test_prompt_example: ValueError: could not convert string to float: 'A', test_o |
| 05-07 | N/A | FAIL | hidden tests: build_failure_function: test_dag_ordering: AssertionError: [0, 0, 0, 0, 0, 0, 0, 0], test_reports_an_actua |
| 06-01 | N/A | PASS | hidden tests: passed every hidden test |
| 06-02 | N/A | PASS | hidden tests: passed every hidden test |
| 06-03 | N/A | FAIL | hidden tests: process_batch/EventEmitter: test_results_are_correct: AssertionError: 0, test_no_growth_over_many_calls: t |
| 06-06 | N/A | FAIL | hidden tests: serialize_iterative: test_small_trees_match_the_original_format: AssertionError:  |
| 06-07 | N/A | PASS | hidden tests: passed every hidden test |

## run-20261001-151739: grades that changed

| Prompt | Old | New | Reason |
|---|---|---|---|
| 02-01 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-02 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-03 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-04 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-06 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-07 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 03-02 | N/A | FAIL | hidden tests: WriteAheadLog: test_append_returns_sequence_numbers_and_recover_reads_back: AssertionError: , test_frame_l |
| 03-03 | N/A | PASS | hidden tests: passed every hidden test |
| 03-05 | N/A | PASS | hidden tests: passed every hidden test |
| 03-06 | N/A | PASS | hidden tests: passed every hidden test |
| 04-01 | N/A | PASS | hidden tests: passed every hidden test |
| 04-02 | N/A | FAIL | no published deliverable |
| 04-03 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 04-05 | N/A | FAIL | hidden tests: MarkdownConverter.convert: test_inline_formatting: AssertionError: '`*not italic*` stays'
 got:      '<p>< |
| 04-06 | N/A | FAIL | hidden tests: compile_source -> VM.run: test_prompt_example: SyntaxError: Expected SEMICOLON, got EOF, test_more_program |
| 04-07 | N/A | FAIL | hidden tests: matches/next_fire: test_prompt_examples: AssertionError: , test_random_against_reference: AssertionError:  |
| 05-01 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-02 | N/A | FAIL | hidden tests: kahn_topological_sort: test_square_with_interior_points: AttributeError: 'list' object has no attribute 'i |
| 05-03 | N/A | FAIL | hidden tests: LCS: test_prompt_example: TypeError: 'int' object is not iterable, test_positions: TypeError: 'int' object |
| 05-04 | N/A | FAIL | hidden tests: manhattan: test_prompt_example: TypeError: unsupported operand type(s) for -: 'str' and 'str', test_edge_c |
| 05-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-06 | N/A | FAIL | hidden tests: find_median_sorted_arrays: test_prompt_example: ValueError: could not convert string to float: 'A', test_o |
| 05-07 | N/A | FAIL | hidden tests: build_lps: test_dag_ordering: AssertionError: [0, 0, 0, 0, 0, 0, 0, 0], test_reports_an_actual_cycle: Asse |
| 06-01 | N/A | PASS | hidden tests: passed every hidden test |
| 06-02 | N/A | PASS | hidden tests: passed every hidden test |
| 06-03 | N/A | PASS | hidden tests: passed every hidden test |
| 06-06 | N/A | PASS | hidden tests: passed every hidden test |
| 06-07 | N/A | PASS | hidden tests: passed every hidden test |

## run-20261001-145558: grades that changed

| Prompt | Old | New | Reason |
|---|---|---|---|
| 02-01 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-02 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-03 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-04 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-06 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-07 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 03-02 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 03-03 | N/A | PASS | hidden tests: passed every hidden test |
| 03-05 | N/A | PASS | hidden tests: passed every hidden test |
| 03-06 | N/A | PASS | hidden tests: passed every hidden test |
| 04-01 | N/A | FAIL | hidden tests: evaluate: test_prompt_examples: CalcError: Unexpected character: (, test_precedence_and_associativity: Cal |
| 04-02 | N/A | FAIL | hidden tests: parse: test_events_for_a_mixed_document: AssertionError: ValueError: Unexpected character , at position 51 |
| 04-03 | N/A | FAIL | hidden tests: the hidden tests did not complete (step budget exceeded) |
| 04-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 04-06 | N/A | FAIL | hidden tests: execute_source: test_prompt_example: SyntaxError: Unexpected token IDENT, test_more_programs: SyntaxError: |
| 04-07 | N/A | FAIL | hidden tests: matches/next_fire: test_prompt_examples: AssertionError: , test_field_syntax: AssertionError: , test_rando |
| 05-01 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-02 | N/A | FAIL | hidden tests: kahn_topological_sort: test_square_with_interior_points: TypeError: list indices must be integers or slice |
| 05-03 | N/A | FAIL | hidden tests: lcs: test_prompt_example: TypeError: 'int' object is not iterable, test_positions: TypeError: 'int' object |
| 05-04 | N/A | FAIL | hidden tests: heuristic: test_prompt_example: TypeError: unsupported operand type(s) for -: 'str' and 'str', test_edge_c |
| 05-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-06 | N/A | FAIL | hidden tests: find_median_sorted_arrays: test_prompt_example: TypeError: can't multiply sequence by non-int of type 'flo |
| 05-07 | N/A | FAIL | hidden tests: build_failure_function: test_dag_ordering: AssertionError: [0, 0, 0, 0, 0, 0, 0, 0], test_reports_an_actua |
| 06-01 | N/A | FAIL | hidden tests: the hidden tests did not complete (step budget exceeded) |
| 06-02 | N/A | PASS | hidden tests: passed every hidden test |
| 06-03 | N/A | PASS | hidden tests: passed every hidden test |
| 06-06 | N/A | PASS | hidden tests: passed every hidden test |
| 06-07 | N/A | PASS | hidden tests: passed every hidden test |

## run-20260930-171129: grades that changed

| Prompt | Old | New | Reason |
|---|---|---|---|
| 02-01 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-02 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-03 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-04 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-06 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 02-07 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 03-02 | N/A | PASS | hidden tests: passed every hidden test |
| 03-03 | N/A | FAIL | hidden tests: FixedBlockMemoryPool: test_holds_a_fixed_byte_buffer: TypeError: vars() argument must have __dict__ attrib |
| 03-05 | N/A | PASS | hidden tests: passed every hidden test |
| 03-06 | N/A | PASS | hidden tests: passed every hidden test |
| 04-01 | N/A | PASS | hidden tests: passed every hidden test |
| 04-02 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 04-03 | N/A | FAIL | hidden tests: matches: test_prompt_examples: AttributeError: 'str' object has no attribute 'start', test_each_operator:  |
| 04-05 | N/A | FAIL | hidden tests: parse: test_headers: AssertionError: '# Title'
 got:      '<h1></h1>\n<p>T i t l e</p>'
 expected: '<h1>Ti |
| 04-06 | N/A | FAIL | hidden tests: compile_source -> VM.run: test_prompt_example: SyntaxError: Unexpected token Token(ID, let), test_more_pro |
| 04-07 | N/A | FAIL | hidden tests: matches/next_fire: test_prompt_examples: AssertionError: , test_field_syntax: AssertionError: , test_rando |
| 05-01 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-02 | N/A | FAIL | hidden tests: kahn_topological_sort: test_square_with_interior_points: AttributeError: 'list' object has no attribute 'i |
| 05-03 | N/A | FAIL | hidden tests: lcs: test_prompt_example: TypeError: 'int' object is not iterable, test_positions: TypeError: 'int' object |
| 05-04 | N/A | FAIL | hidden tests: heuristic: test_prompt_example: TypeError: unsupported operand type(s) for -: 'str' and 'str', test_edge_c |
| 05-05 | N/A | FAIL | hidden tests: no candidate implements the stated operations |
| 05-06 | N/A | FAIL | hidden tests: find_median: test_prompt_example: AssertionError: , test_overlapping_and_edge_matches: AssertionError: , t |
| 05-07 | N/A | FAIL | hidden tests: build_failure_function: test_dag_ordering: AssertionError: [0, 0, 0, 0, 0, 0, 0, 0], test_reports_an_actua |
| 06-01 | N/A | PASS | hidden tests: passed every hidden test |
| 06-02 | N/A | PASS | hidden tests: passed every hidden test |
| 06-03 | N/A | PASS | hidden tests: passed every hidden test |
| 06-06 | N/A | FAIL | hidden tests: serialize_iterative: test_small_trees_match_the_original_format: AssertionError: , test_deep_chain: Assert |
| 06-07 | N/A | PASS | hidden tests: passed every hidden test |
| 14-03 | FAIL | PASS | deadlock-free under the assumptions, blocks under message loss, timeout mitigation |
