IMPLEMENT a Python recursive descent parser that acts as a calculator.
SUPPORT the operators +, -, *, /, unary minus, and parentheses.
HANDLE integer and float literals.
RESPECT precedence: unary minus highest, then * and /, then + and -.
APPLY left-associative evaluation for binary operators.
RETURN a numeric result (not an AST).
RAISE a clear error message for malformed expressions such as unmatched parentheses or missing operand.
PROVIDE tests that verify:
- Verify that 3 + 4 * 2 evaluates to 11.
- Verify that -(3 + 4) * 2 evaluates to -14.
- Verify that 10 / 3 yields approximately 3.333...
INCLUDE at least three error cases (e.g., unmatched parentheses, missing operand, division by zero).
