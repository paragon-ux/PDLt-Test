import re

_TOKEN = re.compile(r"\s*(?:(\d+\.\d*|\.\d+|\d+)|(.))")


class ParseError(ValueError):
    pass


def tokenize(text):
    tokens = []
    for number, op in _TOKEN.findall(text):
        if number:
            tokens.append(float(number) if "." in number else int(number))
        elif op.strip():
            if op not in "+-*/()":
                raise ParseError(f"unexpected character {op!r}")
            tokens.append(op)
    return tokens


class Parser:
    def __init__(self, text):
        self.tokens = tokenize(text)
        self.pos = 0

    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def take(self):
        token = self.peek()
        self.pos += 1
        return token

    def parse(self):
        value = self.expr()
        if self.peek() is not None:
            raise ParseError(f"unexpected token {self.peek()!r}")
        return value

    def expr(self):
        value = self.term()
        while self.peek() in ("+", "-"):
            value = value + self.term() if self.take() == "+" else value - self.term()
        return value

    def term(self):
        value = self.unary()
        while self.peek() in ("*", "/"):
            value = value * self.unary() if self.take() == "*" else value / self.unary()
        return value

    def unary(self):
        if self.peek() == "-":
            self.take()
            return -self.unary()
        return self.primary()

    def primary(self):
        token = self.take()
        if token == "(":
            value = self.expr()
            if self.take() != ")":
                raise ParseError("unmatched parenthesis")
            return value
        if isinstance(token, (int, float)):
            return token
        raise ParseError(f"missing operand near {token!r}")


def evaluate(text):
    return Parser(text).parse()
