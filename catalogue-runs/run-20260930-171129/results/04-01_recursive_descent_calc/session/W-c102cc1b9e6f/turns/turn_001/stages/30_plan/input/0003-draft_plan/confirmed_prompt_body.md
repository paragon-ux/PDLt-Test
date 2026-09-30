READ the arithmetic expression string provided as input
PARSE the expression using recursive descent parsing with operator precedence: unary minus highest, then multiplication/division, then addition/subtraction
ENSURE binary operators are left‑associative
EVALUATE the parsed expression and RETURN the numeric result (integer or floating‑point as appropriate)
RAISE a clear error message if the expression has unmatched parentheses, missing operands, or any other syntax violation
INCLUDE tests that VERIFY the following cases:
"3 + 4 * 2" evaluates to 11
"-(3 + 4) * 2" evaluates to -14
"10 / 3" evaluates to a floating‑point approximation of 3.333…
AT LEAST THREE error cases produce appropriate error messages (e.g., "(1+2", "5 + * 3", "4 /")
