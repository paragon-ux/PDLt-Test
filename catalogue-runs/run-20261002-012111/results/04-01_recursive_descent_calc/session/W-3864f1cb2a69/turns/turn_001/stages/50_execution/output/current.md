import re
import unittest

class CalculatorError(Exception):
    pass

TOKEN_REGEX = re.compile(r"\s*(?:(\d+\.\d+|\d+)|([+\-*/()]))")

def tokenize(expr):
    pos = 0
    tokens = []
    while pos < len(expr):
        match = TOKEN_REGEX.match(expr, pos)
        if not match:
            raise CalculatorError(f"Invalid token at position {pos}")
        number, operator = match.groups()
        if number:
            tokens.append(('NUMBER', float(number)))
        else:
            tokens.append(('OP', operator))
        pos = match.end()
    tokens.append(('EOF', None))
    return tokens

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[0]
    def advance(self):
        self.pos += 1
        self.current = self.tokens[self.pos]
    def expect(self, typ, value=None):
        if self.current[0] != typ or (value is not None and self.current[1] != value):
            raise CalculatorError(f"Expected {typ} {value!r}, got {self.current}")
        self.advance()
    def parse(self):
        result = self.parse_expression()
        if self.current[0] != 'EOF':
            raise CalculatorError("Unexpected token after end of expression")
        return result
    def parse_expression(self):
        left = self.parse_term()
        while self.current[0] == 'OP' and self.current[1] in ('+', '-'):
            op = self.current[1]
            self.advance()
            right = self.parse_term()
            if op == '+':
                left += right
            else:
                left -= right
        return left
    def parse_term(self):
        left = self.parse_factor()
        while self.current[0] == 'OP' and self.current[1] in ('*', '/'):
            op = self.current[1]
            self.advance()
            right = self.parse_factor()
            if op == '*':
                left *= right
            else:
                if right == 0:
                    raise CalculatorError("Division by zero")
                left /= right
        return left
    def parse_factor(self):
        if self.current[0] == 'OP' and self.current[1] == '-':
            self.advance()
            return -self.parse_factor()
        elif self.current[0] == 'OP' and self.current[1] == '(':
            self.advance()
            val = self.parse_expression()
            if self.current[0] != 'OP' or self.current[1] != ')':
                raise CalculatorError("Unmatched '('")
            self.advance()
            return val
        elif self.current[0] == 'NUMBER':
            val = self.current[1]
            self.advance()
            return val
        else:
            raise CalculatorError(f"Unexpected token: {self.current}")

def evaluate(expr):
    tokens = tokenize(expr)
    parser = Parser(tokens)
    return parser.parse()

class TestCalculator(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(evaluate("3 + 4 * 2"), 11)
    def test_unary_and_parens(self):
        self.assertEqual(evaluate("-(3 + 4) * 2"), -14)
    def test_division(self):
        self.assertAlmostEqual(evaluate("10 / 3"), 10/3, places=5)
    def test_unmatched_parentheses(self):
        with self.assertRaises(CalculatorError):
            evaluate("(1 + 2")
    def test_missing_operand(self):
        with self.assertRaises(CalculatorError):
            evaluate("1 + ")
    def test_invalid_token(self):
        with self.assertRaises(CalculatorError):
            evaluate("2 & 3")

if __name__ == "__main__":
    unittest.main()
