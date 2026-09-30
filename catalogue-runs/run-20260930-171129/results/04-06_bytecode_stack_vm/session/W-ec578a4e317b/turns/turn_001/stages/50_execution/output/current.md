# Compiler and Virtual Machine for Tiny Arithmetic Language
# Supports: integer literals, +, -, *, /, variables, let assignments, print statements

from __future__ import annotations
from typing import List, Tuple, Dict, Any

# Bytecode instruction definitions
PUSH_CONST = 'PUSH_CONST'
ADD = 'ADD'
SUB = 'SUB'
MUL = 'MUL'
DIV = 'DIV'
LOAD_VAR = 'LOAD_VAR'
STORE_VAR = 'STORE_VAR'
PRINT = 'PRINT'

Instruction = Tuple[str, Any]  # (opcode, operand?)

# -----------------------
# Compiler
# -----------------------
import re

TOKEN_SPEC = [
    ('NUMBER',   r'\d+'),
    ('ID',       r'[A-Za-z_]\w*'),
    ('OP',       r'[+\-*/]'),
    ('EQ',       r'='),
    ('SEMICOL',  r';'),
    ('LET',      r'let'),
    ('PRINT',    r'print'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('SKIP',     r'[ \t]+'),
    ('MISMATCH',r'.'),
]
TOK_REGEX = '|'.join('(?P<%s>%s)' % pair for pair in TOKEN_SPEC)

class Token:
    def __init__(self, type_: str, value: str):
        self.type = type_
        self.value = value
    def __repr__(self):
        return f'Token({self.type}, {self.value})'

def lexer(text: str) -> List[Token]:
    tokens = []
    for mo in re.finditer(TOK_REGEX, text):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NUMBER':
            tokens.append(Token('NUMBER', value))
        elif kind == 'ID':
            tokens.append(Token('ID', value))
        elif kind == 'OP':
            tokens.append(Token('OP', value))
        elif kind in ('EQ','SEMICOL','LPAREN','RPAREN'):
            tokens.append(Token(kind, value))
        elif kind == 'LET':
            tokens.append(Token('LET', value))
        elif kind == 'PRINT':
            tokens.append(Token('PRINT', value))
        elif kind == 'SKIP':
            continue
        else:
            raise SyntaxError(f'Unexpected character: {value}')
    return tokens

# Recursive‑descent parser producing a list of bytecode instructions
class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        self.bytecode: List[Instruction] = []

    def peek(self) -> Token | None:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else None

    def consume(self, expected_type: str = None) -> Token:
        tok = self.peek()
        if tok is None:
            raise SyntaxError('Unexpected end of input')
        if expected_type and tok.type != expected_type:
            raise SyntaxError(f'Expected {expected_type}, got {tok.type}')
        self.pos += 1
        return tok

    def parse(self) -> List[Instruction]:
        while self.peek() is not None:
            self.statement()
        return self.bytecode

    def statement(self):
        tok = self.peek()
        if tok.type == 'LET':
            self.consume('LET')
            var = self.consume('ID').value
            self.consume('EQ')
            self.expr()
            self.bytecode.append((STORE_VAR, var))
            self.consume('SEMICOL')
        elif tok.type == 'PRINT':
            self.consume('PRINT')
            self.expr()
            self.bytecode.append((PRINT, None))
            self.consume('SEMICOL')
        else:
            raise SyntaxError(f'Unexpected token {tok}')

    # Operator precedence: * / > + -
    def expr(self):
        self.term()
        while self.peek() and self.peek().type == 'OP' and self.peek().value in ('+','-'):
            op = self.consume('OP').value
            self.term()
            if op == '+':
                self.bytecode.append((ADD, None))
            else:
                self.bytecode.append((SUB, None))

    def term(self):
        self.factor()
        while self.peek() and self.peek().type == 'OP' and self.peek().value in ('*','/'):
            op = self.consume('OP').value
            self.factor()
            if op == '*':
                self.bytecode.append((MUL, None))
            else:
                self.bytecode.append((DIV, None))

    def factor(self):
        tok = self.peek()
        if tok.type == 'NUMBER':
            val = int(self.consume('NUMBER').value)
            self.bytecode.append((PUSH_CONST, val))
        elif tok.type == 'ID':
            name = self.consume('ID').value
            self.bytecode.append((LOAD_VAR, name))
        elif tok.type == 'LPAREN':
            self.consume('LPAREN')
            self.expr()
            self.consume('RPAREN')
        else:
            raise SyntaxError(f'Unexpected token in factor: {tok}')

def compile_source(source: str) -> List[Instruction]:
    tokens = lexer(source)
    parser = Parser(tokens)
    return parser.parse()

# -----------------------
# Virtual Machine
# -----------------------
class VM:
    def __init__(self):
        self.stack: List[int] = []
        self.env: Dict[str, int] = {}

    def run(self, bytecode: List[Instruction]):
        for opcode, operand in bytecode:
            if opcode == PUSH_CONST:
                self.stack.append(operand)
            elif opcode == LOAD_VAR:
                if operand not in self.env:
                    raise NameError(f'Variable {operand} not defined')
                self.stack.append(self.env[operand])
            elif opcode == STORE_VAR:
                val = self.stack.pop()
                self.env[operand] = val
            elif opcode == ADD:
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a + b)
            elif opcode == SUB:
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a - b)
            elif opcode == MUL:
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a * b)
            elif opcode == DIV:
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a // b)
            elif opcode == PRINT:
                val = self.stack.pop()
                print(val)
            else:
                raise RuntimeError(f'Unknown opcode {opcode}')

# -----------------------
# Test program
# -----------------------
if __name__ == '__main__':
    source = "let x = 3 + 4 * 2; let y = x - 1; print y;"
    bytecode = compile_source(source)
    vm = VM()
    vm.run(bytecode)
    # Expected output: 10
