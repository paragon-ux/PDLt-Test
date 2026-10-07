# Wrong: never checks for leftover input, so "1 + 2)" and "2 3" return a value.
import re


def calculate(text):
    tokens = re.findall(r"\d+\.\d+|\d+|[-+*/()]", text)
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def take():
        nonlocal pos
        pos += 1
        return tokens[pos - 1]

    def expr():
        value = term()
        while peek() in ("+", "-"):
            value = value + term() if take() == "+" else value - term()
        return value

    def term():
        value = unary()
        while peek() in ("*", "/"):
            value = value * unary() if take() == "*" else value / unary()
        return value

    def unary():
        if peek() == "-":
            take()
            return -unary()
        if peek() is None:
            raise ValueError("missing operand")
        token = take()
        if token == "(":
            value = expr()
            if peek() != ")":
                raise ValueError("unmatched (")
            take()
            return value
        if token in "+-*/)":
            raise ValueError("missing operand")
        return float(token) if "." in token else int(token)

    return expr()
