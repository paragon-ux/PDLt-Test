import re

class CalcError(Exception):
    pass

Token = tuple[str, str]  # (type, value)

TOKEN_SPEC = [
    ("NUMBER", r"\d+\.\d*|\d*\.\d+|\d+"),
    ("PLUS", r"\+"),
    ("MINUS", r"-"),
    ("TIMES", r"\*"),
    ("DIVIDE", r"/"),
    ("LPAREN", r"\\("),
    ("RPAREN", r"\\)"),
    ("SKIP", r"[ \t]+"),
    ("MISMATCH", r".")
]
TOK_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

class Lexer:
    def __init__(self, text: str):
        self.tokens = self.tokenize(text)
        self.pos = 0

    def tokenize(self, text: str):
        tokens: list[Token] = []
        for mo in TOK_REGEX.finditer(text):
            kind = mo.lastgroup
            value = mo.group()
            if kind == "NUMBER":
                tokens.append((kind, value))
            elif kind in {"PLUS", "MINUS", "TIMES", "DIVIDE", "LPAREN", "RPAREN"}:
                tokens.append((kind, value))
            elif kind == "SKIP":
                continue
            else:
                raise CalcError(f"Unexpected character: {value}")
        tokens.append(("EOF", ""))
        return tokens

    def peek(self):
        return self.tokens[self.pos]

    def advance(self):
        self.pos += 1
        return self.peek()

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer

    def parse(self) -> float:
        result = self.expression()
        if self.lexer.peek()[0] != "EOF":
            raise CalcError("Unexpected token after end of expression")
        return result

    # expression -> term ((PLUS|MINUS) term)*
    def expression(self) -> float:
        result = self.term()
        while True:
            typ, _ = self.lexer.peek()
            if typ == "PLUS":
                self.lexer.advance()
                result += self.term()
            elif typ == "MINUS":
                self.lexer.advance()
                result -= self.term()
            else:
                break
        return result

    # term -> factor ((TIMES|DIVIDE) factor)*
    def term(self) -> float:
        result = self.factor()
        while True:
            typ, _ = self.lexer.peek()
            if typ == "TIMES":
                self.lexer.advance()
                result *= self.factor()
            elif typ == "DIVIDE":
                self.lexer.advance()
                denominator = self.factor()
                if denominator == 0:
                    raise CalcError("Division by zero")
                result /= denominator
            else:
                break
        return result

    # factor -> (MINUS) factor | primary
    def factor(self) -> float:
        typ, _ = self.lexer.peek()
        if typ == "MINUS":
            self.lexer.advance()
            return -self.factor()
        return self.primary()

    # primary -> NUMBER | LPAREN expression RPAREN
    def primary(self) -> float:
        typ, val = self.lexer.peek()
        if typ == "NUMBER":
            self.lexer.advance()
            return float(val)
        if typ == "LPAREN":
            self.lexer.advance()
            result = self.expression()
            if self.lexer.peek()[0] != "RPAREN":
                raise CalcError("Unmatched '('")
            self.lexer.advance()
            return result
        raise CalcError(f"Unexpected token: {typ}")

def evaluate(expr: str) -> float:
    lexer = Lexer(expr)
    parser = Parser(lexer)
    return parser.parse()

# Tests
if __name__ == "__main__":
    test_cases = [
        ("3 + 4 * 2", 11.0),
        ("-(3 + 4) * 2", -14.0),
        ("10 / 3", 10/3),
    ]
    for expr, expected in test_cases:
        result = evaluate(expr)
        assert abs(result - expected) < 1e-9, f"Failed: {expr} -> {result}, expected {expected}"
    error_cases = [
        "(1+2",  # missing closing parenthesis
        "1+*2",  # stray operator
        ""       # empty input
    ]
    for expr in error_cases:
        try:
            evaluate(expr)
            assert False, f"Expected error for: {expr}"
        except CalcError:
            pass
    print("All tests passed.")
