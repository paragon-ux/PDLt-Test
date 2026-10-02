# Tiny arithmetic language compiler and stack-based VM
# Supports integer literals, +, -, *, /, variables, let assignments, and print statements.

import sys

# --------------------- Lexer ---------------------
TOKEN_REGEX = [
    (r"\s+", None),  # skip whitespace
    (r"let\b", "LET"),
    (r"print\b", "PRINT"),
    (r"[A-Za-z_][A-Za-z0-9_]*", "IDENT"),
    (r"[0-9]+", "INT"),
    (r"\+", "PLUS"),
    (r"-", "MINUS"),
    (r"\*", "MUL"),
    (r"/", "DIV"),
    (r"=", "EQ"),
    (r";", "SEMI"),
    (r"\(", "LPAREN"),
    (r"\)", "RPAREN"),
]

def lexer(text):
    import re
    pos = 0
    tokens = []
    while pos < len(text):
        match = None
        for pattern, typ in TOKEN_REGEX:
            regex = re.compile(pattern)
            m = regex.match(text, pos)
            if m:
                match = m
                if typ:
                    tokens.append((typ, m.group(0)))
                break
        if not match:
            raise SyntaxError(f"Unexpected character: {text[pos]!r} at {pos}")
        pos = match.end()
    tokens.append(("EOF", ""))
    return tokens

# --------------------- Parser ---------------------
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    def peek(self):
        return self.tokens[self.pos][0]
    def consume(self, typ=None):
        cur_typ, cur_val = self.tokens[self.pos]
        if typ and cur_typ != typ:
            raise SyntaxError(f"Expected {typ}, got {cur_typ}")
        self.pos += 1
        return cur_typ, cur_val
    def parse(self):
        stmts = []
        while self.peek() != "EOF":
            stmts.append(self.statement())
            if self.peek() == "SEMI":
                self.consume("SEMI")
        return stmts
    def statement(self):
        if self.peek() == "LET":
            self.consume("LET")
            _, name = self.consume("IDENT")
            self.consume("EQ")
            expr = self.expression()
            return ("let", name, expr)
        elif self.peek() == "PRINT":
            self.consume("PRINT")
            expr = self.expression()
            return ("print", expr)
        else:
            raise SyntaxError(f"Unexpected token {self.peek()} in statement")
    def expression(self):
        return self.add_sub()
    def add_sub(self):
        node = self.mul_div()
        while self.peek() in ("PLUS", "MINUS"):
            op = self.consume()[0]
            right = self.mul_div()
            node = (op.lower(), node, right)
        return node
    def mul_div(self):
        node = self.unary()
        while self.peek() in ("MUL", "DIV"):
            op = self.consume()[0]
            right = self.unary()
            node = (op.lower(), node, right)
        return node
    def unary(self):
        if self.peek() == "MINUS":
            self.consume("MINUS")
            node = self.unary()
            return ("neg", node)
        return self.primary()
    def primary(self):
        if self.peek() == "INT":
            _, val = self.consume("INT")
            return ("int", int(val))
        if self.peek() == "IDENT":
            _, name = self.consume("IDENT")
            return ("var", name)
        if self.peek() == "LPAREN":
            self.consume("LPAREN")
            node = self.expression()
            self.consume("RPAREN")
            return node
        raise SyntaxError(f"Unexpected token {self.peek()} in primary")

# --------------------- Compiler ---------------------
class Compiler:
    def __init__(self):
        self.instructions = []
    def compile(self, stmts):
        for stmt in stmts:
            self.compile_stmt(stmt)
        return self.instructions
    def compile_stmt(self, stmt):
        kind = stmt[0]
        if kind == "let":
            _, name, expr = stmt
            self.compile_expr(expr)
            self.instructions.append(("STORE_VAR", name))
        elif kind == "print":
            _, expr = stmt
            self.compile_expr(expr)
            self.instructions.append(("PRINT",))
        else:
            raise RuntimeError(f"Unknown stmt {kind}")
    def compile_expr(self, expr):
        typ = expr[0]
        if typ == "int":
            _, value = expr
            self.instructions.append(("PUSH_CONST", value))
        elif typ == "var":
            _, name = expr
            self.instructions.append(("LOAD_VAR", name))
        elif typ in ("plus", "minus", "mul", "div"):
            _, left, right = expr
            self.compile_expr(left)
            self.compile_expr(right)
            op_map = {"plus": "ADD", "minus": "SUB", "mul": "MUL", "div": "DIV"}
            self.instructions.append((op_map[typ],))
        elif typ == "neg":
            _, sub = expr
            self.compile_expr(sub)
            self.instructions.append(("PUSH_CONST", -1))
            self.instructions.append(("MUL",))
        else:
            raise RuntimeError(f"Unknown expr {typ}")

# --------------------- Virtual Machine ---------------------
class VM:
    def __init__(self, instructions):
        self.instructions = instructions
        self.stack = []
        self.env = {}
        self.ip = 0
    def run(self):
        while self.ip < len(self.instructions):
            instr = self.instructions[self.ip]
            self.ip += 1
            op = instr[0]
            if op == "PUSH_CONST":
                self.stack.append(instr[1])
            elif op == "LOAD_VAR":
                name = instr[1]
                self.stack.append(self.env.get(name, 0))
            elif op == "STORE_VAR":
                name = instr[1]
                val = self.stack.pop()
                self.env[name] = val
            elif op == "ADD":
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a + b)
            elif op == "SUB":
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a - b)
            elif op == "MUL":
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a * b)
            elif op == "DIV":
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a // b)
            elif op == "PRINT":
                val = self.stack.pop()
                print(val)
            else:
                raise RuntimeError(f"Unknown opcode {op}")

# --------------------- Driver ---------------------
if __name__ == "__main__":
    source = "let x = 3 + 4 * 2; let y = x - 1; print y"
    tokens = lexer(source)
    parser = Parser(tokens)
    stmts = parser.parse()
    compiler = Compiler()
    bytecode = compiler.compile(stmts)
    vm = VM(bytecode)
    vm.run()
