import re
import unittest

Token = tuple[str, str]  # (type, value)

class CalculatorError(Exception):
    pass

def tokenize(expr: str) -> list[Token]:
    token_spec = [
        ("NUMBER", r"\d+(?:\.\d*)?|\.\d+"),
        ("PLUS",   r"\+"),
        ("MINUS",  r"-"),
        ("TIMES",  r"\*"),
        ("DIVIDE", r"/"),
        ("LPAREN", r"\("),
        ("RPAREN", r"\)"),
        ("SKIP",   r"[ \t]+"),
        ("MISMATCH", r"."),
    ]
    tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_spec)
    get_token = re.compile(tok_regex).match
    pos = 0
    tokens: list[Token] = []
    mo = get_token(expr, pos)
    while mo is not None:
        typ = mo.lastgroup
        val = mo.group(typ)
        if typ == "NUMBER":
            tokens.append(("NUMBER", val))
        elif typ in {"PLUS", "MINUS", "TIMES", "DIVIDE", "LPAREN", "RPAREN"}:
            tokens.append((typ, val))
        elif typ == "SKIP":
            pass
        else:
            raise CalculatorError(f"Unexpected character '{val}' at position {pos}")
        pos = mo.end()
        mo = get_token(expr, pos)
    tokens.append(("EOF", ""))
    return tokens

class Parser:
    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0
        self.current = tokens[0]

    def advance(self):
        self.pos += 1
        self.current = self.tokens[self.pos]

    def expect(self, typ: str):
        if self.current[0] == typ:
            val = self.current[1]
            self.advance()
            return val
        raise CalculatorError(f"Expected {typ} but found {self.current[0]}")

    def parse(self) -> float:
        result = self.parse_expression()
        if self.current[0] != "EOF":
            raise CalculatorError("Unexpected token after end of expression")
        return result

    # expression -> term ((PLUS|MINUS) term)*
    def parse_expression(self) -> float:
        result = self.parse_term()
        while self.current[0] in {"PLUS", "MINUS"}:
            if self.current[0] == "PLUS":
                self.advance()
                result += self.parse_term()
            else:
                self.advance()
                result -= self.parse_term()
        return result

    # term -> factor ((TIMES|DIVIDE) factor)*
    def parse_term(self) -> float:
        result = self.parse_factor()
        while self.current[0] in {"TIMES", "DIVIDE"}:
            if self.current[0] == "TIMES":
                self.advance()
                result *= self.parse_factor()
            else:
                self.advance()
                divisor = self.parse_factor()
                if divisor == 0:
                    raise CalculatorError("Division by zero")
                result /= divisor
        return result

    # factor -> MINUS factor | NUMBER | LPAREN expression RPAREN
    def parse_factor(self) -> float:
        if self.current[0] == "MINUS":
            self.advance()
            return -self.parse_factor()
        elif self.current[0] == "NUMBER":
            val = float(self.current[1])
            self.advance()
            return val
        elif self.current[0] == "LPAREN":
            self.advance()
            val = self.parse_expression()
            self.expect("RPAREN")
            return val
        else:
            raise CalculatorError(f"Unexpected token {self.current[0]}")

def evaluate(expr: str) -> float:
    tokens = tokenize(expr)
    parser = Parser(tokens)
    return parser.parse()

class TestCalculator(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(evaluate("3 + 4 * 2"), 11)
    def test_unary(self):
        self.assertEqual(evaluate("-(3 + 4) * 2"), -14)
    def test_division(self):
        result = evaluate("10 / 3")
        self.assertAlmostEqual(result, 10/3, places=5)
    def test_unmatched_paren(self):
        with self.assertRaises(CalculatorError):
            evaluate("(1 + 2")
    def test_missing_operand(self):
        with self.assertRaises(CalculatorError):
            evaluate("5 +")
    def test_invalid_char(self):
        with self.assertRaises(CalculatorError):
            evaluate("2 & 3")

if __name__ == "__main__":
    unittest.main()
