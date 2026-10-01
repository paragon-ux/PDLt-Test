TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a calculator in Python using recursive descent parsing with correct operator precedence. Support operators +, -, *, /, unary minus, and parentheses. Handle integer and float literals. Operator precedence: unary minus > * / > + -. Binary operators are left-associative. The calculator must return a numeric result (not an AST) and raise clear error messages for malformed expressions such as unmatched parentheses or missing operands. Include tests verifying that "3 + 4 * 2" evaluates to 11, "-(3 + 4) * 2" evaluates to -14, "10 / 3" evaluates to approximately 3.333..., and provide at least three error case tests.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- recursive descent parsing
- +
- -
- *
- /
- unary minus
- parentheses
- float literals
- "3 + 4 * 2"
- "-(3 + 4) * 2"
- "10 / 3"
