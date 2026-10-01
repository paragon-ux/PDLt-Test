DEFINE the lexical token types: numbers, operators (+, -, *, /), parentheses, end-of-input.
IMPLEMENT a lexer that scans the input string and produces a token stream.
DEFINE the grammar hierarchy:
    parse_expression   handles addition and subtraction.
    parse_term         handles multiplication and division.
    parse_factor       handles unary minus and primary expressions.
    parse_primary      handles numeric literals and parenthesized subexpressions.
IMPLEMENT parse_expression using left-associative evaluation of parse_term combined with +/- operators.
IMPLEMENT parse_term using left-associative evaluation of parse_factor combined with */ operators.
IMPLEMENT parse_factor to detect unary minus and delegate to parse_primary.
IMPLEMENT parse_primary to:
    IF next token is a number THEN convert to numeric value.
    ELSE IF next token is '(' THEN parse nested expression and expect matching ')'.
    ELSE raise a syntax error for unexpected token.
ENSURE that each parser function returns the computed numeric value directly.
HANDLE division by zero by raising a clear runtime error with an explanatory message.
HANDLE malformed expressions (unmatched parentheses, missing operands) by raising syntax errors with clear messages.
DEVELOP a test suite that:
    VERIFY that "3 + 4 * 2" evaluates to 11.
    VERIFY that "-(3 + 4) * 2" evaluates to -14.
    VERIFY that "10 / 3" evaluates to a value within tolerance of 3.333... .
    VERIFY that an expression with unmatched parentheses raises a syntax error.
    VERIFY that an expression with a missing operand raises a syntax error.
    VERIFY that an expression dividing by zero raises a runtime error.
EXECUTE the test suite and ensure all tests pass.
