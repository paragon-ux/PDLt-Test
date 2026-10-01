# Tiny arithmetic language compiler and VM
# Supports:
#   let <id> = <expr>;
#   print <expr>;
#   integer literals, +, -, *, /, variables
# Bytecode instructions: PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT

import re
from collections import namedtuple

# Token definitions
Token = namedtuple('Token', ['type', 'value'])
TOKEN_SPEC = [
    ('NUMBER',   r'\d+'),
    ('IDENT',    r'[A-Za-z_]\w*'),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('TIMES',    r'\*'),
    ('DIVIDE',   r'/'),
    ('EQ',       r'='),
    ('SEMICOLON',r';'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('SKIP',     r'[ \t]+'),
    ('MISMATCH', r'.'),
]
TOK_REGEX = re.compile('|'.join('(?P<%s>%s)' % pair for pair in TOKEN_SPEC))
KEYWORDS = {'let': 'LET', 'print': 'PRINT'}

def lexer(code):
    tokens = []
    for mo in TOK_REGEX.finditer(code):
        kind = mo.lastgroup
        value = mo.group()
        if kind == 'NUMBER':
            tokens.append(Token('NUMBER', int(value)))
        elif kind == 'IDENT':
            typ = KEYWORDS.get(value, 'IDENT')
            tokens.append(Token(typ, value))
        elif kind == 'SKIP':
            continue
        elif kind == 'MISMATCH':
            raise SyntaxError(f'Unexpected character {value!r}')
        else:
            tokens.append(Token(kind, value))
    tokens.append(Token('EOF', None))
    return tokens

# AST nodes
class AST: pass
class BinOp(AST):
    def __init__(self, left, op, right):
        self.left = left; self.op = op; self.right = right
class Num(AST):
    def __init__(self, value): self.value = value
class Var(AST):
    def __init__(self, name): self.name = name
class Assign(AST):
    def __init__(self, name, expr): self.name = name; self.expr = expr
class Print(AST):
    def __init__(self, expr): self.expr = expr
class Program(AST):
    def __init__(self, statements): self.statements = statements

# Parser
class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.cur = tokens[0]
    def advance(self):
        self.pos += 1
        self.cur = self.tokens[self.pos]
    def eat(self, token_type):
        if self.cur.type == token_type:
            val = self.cur.value
            self.advance()
            return val
        raise SyntaxError(f'Expected {token_type}, got {self.cur.type}')
    def parse(self):
        stmts = []
        while self.cur.type != 'EOF':
            stmts.append(self.statement())
        return Program(stmts)
    def statement(self):
        if self.cur.type == 'LET':
            self.eat('LET')
            name = self.eat('IDENT')
            self.eat('EQ')
            expr = self.expr()
            self.eat('SEMICOLON')
            return Assign(name, expr)
        if self.cur.type == 'PRINT':
            self.eat('PRINT')
            expr = self.expr()
            self.eat('SEMICOLON')
            return Print(expr)
        raise SyntaxError('Unknown statement')
    # precedence: +- low, */ high
    def expr(self):
        return self.add_sub()
    def add_sub(self):
        node = self.mul_div()
        while self.cur.type in ('PLUS', 'MINUS'):
            op = self.cur.type
            self.advance()
            right = self.mul_div()
            node = BinOp(node, op, right)
        return node
    def mul_div(self):
        node = self.factor()
        while self.cur.type in ('TIMES', 'DIVIDE'):
            op = self.cur.type
            self.advance()
            right = self.factor()
            node = BinOp(node, op, right)
        return node
    def factor(self):
        if self.cur.type == 'NUMBER':
            val = self.eat('NUMBER')
            return Num(val)
        if self.cur.type == 'IDENT':
            name = self.eat('IDENT')
            return Var(name)
        if self.cur.type == 'LPAREN':
            self.eat('LPAREN')
            node = self.expr()
            self.eat('RPAREN')
            return node
        raise SyntaxError('Invalid factor')

# Bytecode generation
class Compiler:
    def __init__(self):
        self.instructions = []
    def compile(self, node):
        if isinstance(node, Program):
            for stmt in node.statements:
                self.compile(stmt)
        elif isinstance(node, Assign):
            self.compile(node.expr)
            self.instructions.append(('STORE_VAR', node.name))
        elif isinstance(node, Print):
            self.compile(node.expr)
            self.instructions.append(('PRINT',))
        elif isinstance(node, BinOp):
            self.compile(node.left)
            self.compile(node.right)
            op_map = {'PLUS':'ADD','MINUS':'SUB','TIMES':'MUL','DIVIDE':'DIV'}
            self.instructions.append((op_map[node.op],))
        elif isinstance(node, Num):
            self.instructions.append(('PUSH_CONST', node.value))
        elif isinstance(node, Var):
            self.instructions.append(('LOAD_VAR', node.name))
        else:
            raise TypeError('Unknown node')
        return self.instructions

def compile_source(source):
    tokens = lexer(source)
    parser = Parser(tokens)
    ast = parser.parse()
    comp = Compiler()
    bytecode = comp.compile(ast)
    return bytecode

# Virtual Machine
class VM:
    def __init__(self, bytecode):
        self.bytecode = bytecode
        self.stack = []
        self.env = {}
        self.ip = 0
    def run(self):
        while self.ip < len(self.bytecode):
            instr = self.bytecode[self.ip]
            op = instr[0]
            if op == 'PUSH_CONST':
                self.stack.append(instr[1])
            elif op == 'LOAD_VAR':
                self.stack.append(self.env[instr[1]])
            elif op == 'STORE_VAR':
                val = self.stack.pop()
                self.env[instr[1]] = val
            elif op == 'ADD':
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a + b)
            elif op == 'SUB':
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a - b)
            elif op == 'MUL':
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a * b)
            elif op == 'DIV':
                b = self.stack.pop(); a = self.stack.pop(); self.stack.append(a // b)
            elif op == 'PRINT':
                val = self.stack.pop()
                print(val)
            else:
                raise RuntimeError(f'Unknown opcode {op}')
            self.ip += 1

def execute_bytecode(bytecode):
    vm = VM(bytecode)
    vm.run()

# Test example
if __name__ == '__main__':
    src = 'let x = 3 + 4 * 2; let y = x - 1; print y;'
    bc = compile_source(src)
    execute_bytecode(bc)
