IMPLEMENT a recursive descent parser calculator in Python
SUPPORT operators +, -, *, / and unary minus, parentheses, integer and float literals
ENFORCE operator precedence: unary minus > multiplication/division > addition/subtraction (left-associative)
RETURN the numeric result of an expression (not an AST)
RAISE clear error messages for malformed expressions such as unmatched parentheses or missing operands
INCLUDE tests verifying that "3 + 4 * 2" evaluates to 11, "-(3 + 4) * 2" evaluates to -14, and "10 / 3" evaluates to a floating-point result (approximately 3.333...).
