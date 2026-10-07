# Wrong: SUB and DIV pop their operands in the wrong order (computes b - a).
import re

TOKEN = re.compile(r"\s*(?:(\d+)|([A-Za-z_]\w*)|(.))")


def tokenize(src):
    out = []
    for num, name, op in TOKEN.findall(src):
        if num:
            out.append(("num", int(num)))
        elif name:
            out.append(("name", name))
        elif op.strip():
            out.append(("op", op))
    return out


class Compiler:
    def compile(self, src):
        self.toks, self.i, self.code = tokenize(src), 0, []
        while self.i < len(self.toks):
            self.statement()
            if self.i < len(self.toks):
                self.expect("op", ";")
        return self.code

    def peek(self):
        return self.toks[self.i] if self.i < len(self.toks) else (None, None)

    def expect(self, kind, value=None):
        tok = self.peek()
        if tok[0] != kind or (value is not None and tok[1] != value):
            raise SyntaxError(f"expected {value or kind}, got {tok}")
        self.i += 1
        return tok[1]

    def statement(self):
        kind, value = self.peek()
        if (kind, value) == ("name", "let"):
            self.i += 1
            name = self.expect("name")
            self.expect("op", "=")
            self.expr()
            self.code.append(("STORE_VAR", name))
        elif (kind, value) == ("name", "print"):
            self.i += 1
            self.expr()
            self.code.append(("PRINT",))
        else:
            raise SyntaxError(f"unexpected {value!r}")

    def expr(self):
        self.term()
        while self.peek() in (("op", "+"), ("op", "-")):
            op = self.peek()[1]
            self.i += 1
            self.term()
            self.code.append(("ADD",) if op == "+" else ("SUB",))

    def term(self):
        self.atom()
        while self.peek() in (("op", "*"), ("op", "/")):
            op = self.peek()[1]
            self.i += 1
            self.atom()
            self.code.append(("MUL",) if op == "*" else ("DIV",))

    def atom(self):
        kind, value = self.peek()
        self.i += 1
        if kind == "num":
            self.code.append(("PUSH_CONST", value))
        elif kind == "name":
            self.code.append(("LOAD_VAR", value))
        else:
            raise SyntaxError(f"unexpected {value!r}")


class VM:
    def __init__(self):
        self.stack, self.env = [], {}

    def run(self, code):
        for instr in code:
            op = instr[0]
            if op == "PUSH_CONST":
                self.stack.append(instr[1])
            elif op == "LOAD_VAR":
                self.stack.append(self.env[instr[1]])
            elif op == "STORE_VAR":
                self.env[instr[1]] = self.stack.pop()
            elif op == "PRINT":
                print(self.stack.pop())
            else:
                a, b = self.stack.pop(), self.stack.pop()
                if op == "ADD":
                    self.stack.append(a + b)
                elif op == "SUB":
                    self.stack.append(a - b)
                elif op == "MUL":
                    self.stack.append(a * b)
                elif op == "DIV":
                    self.stack.append(a // b)
                else:
                    raise RuntimeError(f"bad opcode {op}")
