TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a Python recursive descent parser that acts as a calculator, supporting the operators +, -, *, /, unary minus, and parentheses, handling integer and float literals with correct precedence (unary minus highest, then * and /, then + and -) and left-associative binary operators, returning a numeric result (not an AST), raising a clear error message for malformed expressions such as unmatched parentheses or missing operands, and providing tests that verify "3 + 4 * 2" evaluates to 11, "-(3 + 4) * 2" evaluates to -14, "10 / 3" yields approximately 3.333..., plus at least three error cases.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- calculator
- +
- -
- *
- /
- unary minus
- parentheses
- integer and float literals
- numeric result
- AST
- clear error message
- malformed expressions
- missing operand
- 3 + 4 * 2
- 11
- -(3 + 4) * 2
- -14
- 10 / 3
- 3.333...
