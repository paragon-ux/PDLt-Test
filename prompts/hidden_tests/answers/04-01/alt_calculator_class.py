# Correct with a different interface: Calculator().calculate(expr), a char-level
# scanner, helper functions with one parameter, and SyntaxError for bad input.
def is_digit(c):
    return c.isdigit() or c == "."


def is_space(c):
    return c in " 	"


class Calculator:
    def calculate(self, expression):
        self.s, self.i = expression, 0
        if not self.s.strip():
            raise SyntaxError("empty expression")
        result = self._sum()
        self._skip()
        if self.i != len(self.s):
            raise SyntaxError(f"unexpected {self.s[self.i]!r} at {self.i}")
        return result

    def _skip(self):
        while self.i < len(self.s) and is_space(self.s[self.i]):
            self.i += 1

    def _at(self, chars):
        self._skip()
        return self.i < len(self.s) and self.s[self.i] in chars

    def _sum(self):
        left = self._product()
        while self._at("+-"):
            op = self.s[self.i]
            self.i += 1
            right = self._product()
            left = left + right if op == "+" else left - right
        return left

    def _product(self):
        left = self._neg()
        while self._at("*/"):
            op = self.s[self.i]
            self.i += 1
            right = self._neg()
            left = left * right if op == "*" else left / right
        return left

    def _neg(self):
        if self._at("-"):
            self.i += 1
            return -self._neg()
        return self._atom()

    def _atom(self):
        if self._at("("):
            self.i += 1
            value = self._sum()
            if not self._at(")"):
                raise SyntaxError("missing )")
            self.i += 1
            return value
        self._skip()
        start = self.i
        while self.i < len(self.s) and is_digit(self.s[self.i]):
            self.i += 1
        if start == self.i:
            raise SyntaxError("missing operand")
        text = self.s[start:self.i]
        return float(text) if "." in text else int(text)
