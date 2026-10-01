# vm.py
# Simple stack‑based bytecode virtual machine for a tiny arithmetic language
# Supports integer literals, +, -, *, /, variables, assignment (let), and print

import re
from typing import List, Tuple, Any, Dict

# ------------------------------------------------------------
# Lexer
# ------------------------------------------------------------
TOKEN_SPEC = [
    ("NUMBER",   r"\d+"),
    ("IDENT",    r"[a-zA-Z_]\w*"),
    ("PLUS",     r"\+"),
    ("MINUS",    r"-"),
    ("MUL",      r"\*"),
    ("DIV",      r"/"),
    ("EQ",       r"="),
    ("LET",      r"let"),
    ("PRINT",    r"print"),
    ("SEMICOL",  r";"),
    ("LPAREN",   r"\("),
    ("RPAREN",   r"\)"),
    ("SKIP",     r"[ \t]+"),
    ("MISMATCH", r"."),
]
TOK_REGEX = re.compile("|".join(f"(?P<{name}>{pattern})" for name, pattern in TOKEN_SPEC))

def lex(text: str) -> List[Tuple[str, str]]:
    tokens = []
    for mo in TOK_REGEX.finditer(text):
        kind = mo.lastgroup
        value = mo.group()
        if kind == "SKIP":
            continue
        if kind == "MISMATCH":
            raise SyntaxError(f"Unexpected character: {value!r}")
        tokens.append((kind, value))
    return tokens

# ------------------------------------------------------------
# Parser (recursive descent)
# ------------------------------------------------------------
class Parser:
    def __init__(self, tokens: List[Tuple[str, str]]):
        self.tokens = tokens
        self.pos = 0

    def peek(self) -> Tuple[str, str]:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else ("EOF", "")

    def consume(self, expected: str) -> str:
        kind, value = self.peek()
        if kind != expected:
            raise SyntaxError(f"Expected {expected}, got {kind}")
        self.pos += 1
        return value

    def parse(self) -> List[Any]:
        stmts = []
        while self.pos < len(self.tokens):
            stmts.append(self.statement())
        return stmts

    def statement(self) -> Any:
        kind, _ = self.peek()
        if kind == "LET":
            self.consume("LET")
            var = self.consume("IDENT")
            self.consume("EQ")
            expr = self.expr()
            self.consume("SEMICOL")
            return ("let", var, expr)
        elif kind == "PRINT":
            self.consume("PRINT")
            expr = self.expr()
            self.consume("SEMICOL")
            return ("print", expr)
        else:
            raise SyntaxError(f"Unexpected token {kind}")

    # expr -> term ((PLUS|MINUS) term)*
    def expr(self) -> Any:
        node = self.term()
        while True:
            kind, _ = self.peek()
            if kind == "PLUS":
                self.consume("PLUS")
                node = ("add", node, self.term())
            elif kind == "MINUS":
                self.consume("MINUS")
                node = ("sub", node, self.term())
            else:
                break
        return node

    # term -> factor ((MUL|DIV) factor)*
    def term(self) -> Any:
        node = self.factor()
        while True:
            kind, _ = self.peek()
            if kind == "MUL":
                self.consume("MUL")
                node = ("mul", node, self.factor())
            elif kind == "DIV":
                self.consume("DIV")
                node = ("div", node, self.factor())
            else:
                break
        return node

    def factor(self) -> Any:
        kind, value = self.peek()
        if kind == "NUMBER":
            self.consume("NUMBER")
            return ("const", int(value))
        if kind == "IDENT":
            self.consume("IDENT")
            return ("var", value)
        if kind == "LPAREN":
            self.consume("LPAREN")
            node = self.expr()
            self.consume("RPAREN")
            return node
        raise SyntaxError(f"Unexpected token {kind}")

# ------------------------------------------------------------
# Compiler – AST -> bytecode
# ------------------------------------------------------------
# Opcodes definition
PUSH_CONST = "PUSH_CONST"
ADD = "ADD"
SUB = "SUB"
MUL = "MUL"
DIV = "DIV"
LOAD_VAR = "LOAD_VAR"
STORE_VAR = "STORE_VAR"
PRINT_OP = "PRINT"

def compile_ast(ast) -> List[Tuple[str, Any]]:
    code = []
    for stmt in ast:
        kind = stmt[0]
        if kind == "let":
            _, var, expr = stmt
            compile_expr(expr, code)
            code.append((STORE_VAR, var))
        elif kind == "print":
            _, expr = stmt
            compile_expr(expr, code)
            code.append((PRINT_OP, None))
        else:
            raise ValueError(f"Unknown statement {kind}")
    return code

def compile_expr(node, code: List[Tuple[str, Any]]):
    kind = node[0]
    if kind == "const":
        _, value = node
        code.append((PUSH_CONST, value))
    elif kind == "var":
        _, name = node
        code.append((LOAD_VAR, name))
    elif kind in ("add", "sub", "mul", "div"):
        op_map = {"add": ADD, "sub": SUB, "mul": MUL, "div": DIV}
        _, left, right = node
        compile_expr(left, code)
        compile_expr(right, code)
        code.append((op_map[kind], None))
    else:
        raise ValueError(f"Unknown expr {kind}")

# ------------------------------------------------------------
# Virtual Machine – execute bytecode
# ------------------------------------------------------------
def run_bytecode(bytecode: List[Tuple[str, Any]]):
    stack: List[int] = []
    env: Dict[str, int] = {}
    for opcode, arg in bytecode:
        if opcode == PUSH_CONST:
            stack.append(arg)
        elif opcode == LOAD_VAR:
            stack.append(env[arg])
        elif opcode == STORE_VAR:
            env[arg] = stack.pop()
        elif opcode == ADD:
            b = stack.pop(); a = stack.pop(); stack.append(a + b)
        elif opcode == SUB:
            b = stack.pop(); a = stack.pop(); stack.append(a - b)
        elif opcode == MUL:
            b = stack.pop(); a = stack.pop(); stack.append(a * b)
        elif opcode == DIV:
            b = stack.pop(); a = stack.pop(); stack.append(a // b)
        elif opcode == PRINT_OP:
            value = stack.pop()
            print(value)
        else:
            raise RuntimeError(f"Unknown opcode {opcode}")

# ------------------------------------------------------------
# Helper – compile source string and execute
# ------------------------------------------------------------
def execute_source(source: str):
    tokens = lex(source)
    parser = Parser(tokens)
    ast = parser.parse()
    bytecode = compile_ast(ast)
    run_bytecode(bytecode)

# ------------------------------------------------------------
# Demo
# ------------------------------------------------------------
if __name__ == "__main__":
    program = "let x = 3 + 4 * 2; let y = x - 1; print y;"
    execute_source(program)
