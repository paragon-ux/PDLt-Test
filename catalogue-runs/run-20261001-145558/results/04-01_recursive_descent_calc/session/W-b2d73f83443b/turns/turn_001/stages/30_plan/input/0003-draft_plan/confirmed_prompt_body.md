READ the request to implement a calculator in Python using recursive descent parsing with correct operator precedence.
DEFINE support for operators +, -, *, /, unary minus, and parentheses.
HANDLE integer and float literals.
ENFORCE operator precedence: unary minus > * / > + -.
ENSURE binary operators are left-associative.
RETURN a numeric result (not an AST) for each expression.
RAISE clear error messages for malformed expressions such as unmatched parentheses or missing operands.
VERIFY that "3 + 4 * 2" evaluates to 11.
VERIFY that "-(3 + 4) * 2" evaluates to -14.
VERIFY that "10 / 3" evaluates to approximately 3.333....
INCLUDE at least three tests that confirm error cases are correctly detected.
