import re

class ParseError(Exception):
    pass

def tokenize(expr):
    token_spec = [
        ("NUMBER",   r"\d+\.\d*|\d*\.\d+|\d+"),
        ("PLUS",     r"\+"),
        ("MINUS",    r"-"),
        ("TIMES",    r"\*"),
        ("DIVIDE",   r"/"),
        ("LPAREN",   r"\("),
        ("RPAREN",   r"\)"),
        ("SKIP",     r"[ \t]+"),
        ("MISMATCH", r"."),
    ]
    tok_regex = "|".join(f"(?P<{name}>{pattern})" for name, pattern in token_spec)
    for mo in re.finditer(tok_regex, expr):
        kind = mo.lastgroup
        value = mo.group()
        if kind == "NUMBER":
            yield ("NUMBER", float(value) if "." in value else int(value))
        elif kind in {"PLUS","MINUS","TIMES","DIVIDE","LPAREN","RPAREN"}:
            yield (kind, value)
        elif kind == "SKIP":
            continue
        else:
            raise ParseError(f"Unexpected character: {value}")
    yield ("EOF", None)

class Parser:
    def __init__(self, tokens):
        self.tokens = list(tokens)
        self.pos = 0
        self.current = self.tokens[self.pos]

    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current = self.tokens[self.pos]
        else:
            self.current = ("EOF", None)

    def eat(self, token_type):
        if self.current[0] == token_type:
            val = self.current[1]
            self.advance()
            return val
        else:
            raise ParseError(f"Expected {token_type}, got {self.current[0]}")

    # Grammar with precedence
    # expr -> term ((PLUS|MINUS) term)*
    # term -> factor ((TIMES|DIVIDE) factor)*
    # factor -> MINUS factor | primary
    # primary -> NUMBER | LPAREN expr RPAREN

    def parse(self):
        if self.current[0] == "EOF":
            raise ParseError("Empty expression")
        result = self.expr()
        if self.current[0] != "EOF":
            raise ParseError("Unexpected token after end of expression")
        return result

    def expr(self):
        node = self.term()
        while self.current[0] in ("PLUS", "MINUS"):
            op = self.current[0]
            self.advance()
            right = self.term()
            if op == "PLUS":
                node = node + right
            else:
                node = node - right
        return node

    def term(self):
        node = self.factor()
        while self.current[0] in ("TIMES", "DIVIDE"):
            op = self.current[0]
            self.advance()
            right = self.factor()
            if op == "TIMES":
                node = node * right
            else:
                if right == 0:
                    raise ZeroDivisionError("division by zero")
                node = node / right
        return node

    def factor(self):
        if self.current[0] == "MINUS":
            self.advance()
            return -self.factor()
        else:
            return self.primary()

    def primary(self):
        if self.current[0] == "NUMBER":
            val = self.current[1]
            self.advance()
            return val
        elif self.current[0] == "LPAREN":
            self.advance()
            val = self.expr()
            self.eat("RPAREN")
            return val
        else:
            raise ParseError(f"Unexpected token: {self.current[0]}")

def evaluate(expression: str):
    """Parse and evaluate an arithmetic expression.
    Supports +, -, *, /, unary minus, parentheses, integers and floats.
    Raises ParseError for syntax errors.
    """
    tokens = tokenize(expression)
    parser = Parser(tokens)
    return parser.parse()

# Tests
if __name__ == "__main__":
    test_cases = [
        ("3 + 4 * 2", 11),
        ("-(3 + 4) * 2", -14),
        ("10 / 3", 10/3),
    ]
    for expr, expected in test_cases:
        result = evaluate(expr)
        assert abs(result - expected) < 1e-9, f"{expr} => {result}, expected {expected}"
    # Error cases
    error_cases = ["(1+2", "5 + * 3", "4 /"]
    for expr in error_cases:
        try:
            evaluate(expr)
            assert False, f"Expression should have failed: {expr}"
        except Exception:
            pass
    print("All tests passed.")
