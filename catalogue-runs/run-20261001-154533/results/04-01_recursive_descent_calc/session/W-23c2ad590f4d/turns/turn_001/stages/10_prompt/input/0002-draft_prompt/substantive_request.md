TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a calculator in Python using recursive descent parsing with correct operator precedence. Support addition (+), subtraction (-), multiplication (*), division (/), unary minus, parentheses, integer and float literals. Enforce precedence order: unary minus > multiplication/division > addition/subtraction, with left-associative binary operators. Return a numeric result (not an AST). Raise clear error messages for malformed expressions such as unmatched parentheses or missing operands. Include tests verifying that "3 + 4 * 2" evaluates to 11, "-(3 + 4) * 2" evaluates to -14, and "10 / 3" evaluates to a floating-point result (approximately 3.333...).
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- 3 + 4 * 2
- -(3 + 4) * 2
- 10 / 3
