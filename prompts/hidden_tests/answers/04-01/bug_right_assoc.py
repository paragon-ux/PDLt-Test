# Wrong: binary operators recurse on the right, so they associate right
# (8 - 3 - 2 gives 7).
import re


def evaluate(text):
    tokens = re.findall(r"\d+\.\d+|\d+|[-+*/()]", text)
    if not tokens:
        raise ValueError("empty")
    pos = [0]

    def peek():
        return tokens[pos[0]] if pos[0] < len(tokens) else None

    def take():
        pos[0] += 1
        return tokens[pos[0] - 1]

    def expr():
        left = term()
        if peek() in ("+", "-"):
            op = take()
            right = expr()
            return left + right if op == "+" else left - right
        return left

    def term():
        left = unary()
        if peek() in ("*", "/"):
            op = take()
            right = term()
            return left * right if op == "*" else left / right
        return left

    def unary():
        if peek() == "-":
            take()
            return -unary()
        token = take() if peek() is not None else None
        if token == "(":
            value = expr()
            if peek() != ")":
                raise ValueError("unmatched (")
            take()
            return value
        if token is None or token in "+-*/)":
            raise ValueError("missing operand")
        return float(token) if "." in token else int(token)

    value = expr()
    if peek() is not None:
        raise ValueError("trailing tokens")
    return value
