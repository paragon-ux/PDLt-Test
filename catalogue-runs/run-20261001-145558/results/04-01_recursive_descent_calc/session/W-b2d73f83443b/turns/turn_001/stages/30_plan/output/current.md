READ the task specification
DEFINE tokenization rules for integers, floats, operators, parentheses, and whitespace
IMPLEMENT a lexer that produces a stream of tokens
DESIGN parsing functions for each precedence level: parse_expression (handles + and -), parse_term (handles * and /), parse_factor (handles unary minus and parentheses), and parse_primary (handles literals)
CONSTRUCT recursive descent calls so that higher-precedence functions are invoked within lower-precedence ones
EVALUATE each parsed component directly to produce a numeric result rather than an AST
INCLUDE error checks for unmatched parentheses, unexpected tokens, and missing operands
RETURN the computed numeric value for the input expression
WRITE test cases verifying correct results for "3 + 4 * 2", "-(3 + 4) * 2", and "10 / 3"
WRITE test cases confirming error detection for malformed expressions such as missing closing parenthesis or stray operator
