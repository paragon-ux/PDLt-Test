TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a calculator in Python that evaluates arithmetic expressions and returns a numeric result. The calculator must support binary operators +, -, *, /, unary minus, parentheses, and both integer and float literals. Operator precedence must be unary minus > * / > + -. All binary operators are left-associative. The implementation must raise clear error messages for malformed expressions such as unmatched parentheses or missing operands. The solution must include tests confirming that the expression 3 + 4 * 2 evaluates to 11, the expression -(3 + 4) * 2 evaluates to -14, the expression 10 / 3 evaluates to approximately 3.333..., and at least three additional test cases covering error scenarios.
APPROACH/RISK NOTES:
Use recursive descent parsing to construct the calculator, with separate parsing functions for each precedence level and handling of unary minus in a dedicated routine.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- 3 + 4 * 2
- -(3 + 4) * 2
- 10 / 3
