TOKENIZE the input expression into tokens.
BUILD a recursive descent parser.
    DEFINE parse_expression to handle addition and subtraction as left-associative operators.
    DEFINE parse_term to handle multiplication and division as left-associative operators.
    DEFINE parse_factor to handle unary minus, parentheses, and numeric literals.
    VALIDATE matching parentheses during parsing.
    RAISE clear error messages for unmatched parentheses, missing operands, or invalid tokens.
EVALUATE the parsed expression and RETURN the numeric result.
CONSTRUCT a test suite.
    INCLUDE a test confirming that "3 + 4 * 2" evaluates to 11.
    INCLUDE a test confirming that "-(3 + 4) * 2" evaluates to -14.
    INCLUDE a test confirming that "10 / 3" evaluates to approximately 3.333...
    INCLUDE error tests for unmatched parentheses, missing operand, and invalid token.
EXECUTE the test suite and REPORT pass/fail outcomes.
