# Bytecode Virtual Machine for Tiny Arithmetic Language
# Supports: integer literals, +, -, *, /, variables, assignment, print
# Bytecode instructions: PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT

from typing import List, Tuple, Dict, Any

# Define instruction types
Instruction = Tuple[str, Any]

def compile_source(source: str) -> List[Instruction]:
    """Compile a very small language into bytecode.
    The source syntax is limited to statements separated by ';' and of the form:
        let <var> = <expr>
    or
        print <expr>
    Expressions support +, -, *, / and variable references, with integer literals.
    No parentheses are supported; precedence follows standard arithmetic (*/ before +-).
    """
    tokens = source.replace(';', ' ;').split()
    pos = 0
    bytecode: List[Instruction] = []
    def peek():
        return tokens[pos] if pos < len(tokens) else None
    def consume():
        nonlocal pos
        tok = tokens[pos]
        pos += 1
        return tok
    def parse_factor():
        tok = peek()
        if tok is None:
            raise SyntaxError('Unexpected end of input')
        if tok.isdigit():
            consume()
            bytecode.append(('PUSH_CONST', int(tok)))
        elif tok.isidentifier():
            consume()
            bytecode.append(('LOAD_VAR', tok))
        else:
            raise SyntaxError(f'Unexpected token {tok}')
    def parse_term():
        parse_factor()
        while peek() in ('*', '/'):            
            op = consume()
            parse_factor()
            bytecode.append(('MUL' if op == '*' else 'DIV', None))
    def parse_expr():
        parse_term()
        while peek() in ('+', '-'):            
            op = consume()
            parse_term()
            bytecode.append(('ADD' if op == '+' else 'SUB', None))
    while pos < len(tokens):
        tok = peek()
        if tok == 'let':
            consume()  # let
            var_name = consume()
            if consume() != '=':
                raise SyntaxError('Expected =')
            parse_expr()
            bytecode.append(('STORE_VAR', var_name))
        elif tok == 'print':
            consume()
            parse_expr()
            bytecode.append(('PRINT', None))
        elif tok == ';':
            consume()
        else:
            raise SyntaxError(f'Unexpected token {tok}')
    return bytecode

class VM:
    def __init__(self, bytecode: List[Instruction]):
        self.bytecode = bytecode
        self.stack: List[int] = []
        self.env: Dict[str, int] = {}
        self.ip = 0
    def run(self):
        while self.ip < len(self.bytecode):
            instr, arg = self.bytecode[self.ip]
            self.ip += 1
            if instr == 'PUSH_CONST':
                self.stack.append(arg)
            elif instr == 'ADD':
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a + b)
            elif instr == 'SUB':
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a - b)
            elif instr == 'MUL':
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a * b)
            elif instr == 'DIV':
                b = self.stack.pop()
                a = self.stack.pop()
                self.stack.append(a // b)
            elif instr == 'LOAD_VAR':
                self.stack.append(self.env[arg])
            elif instr == 'STORE_VAR':
                self.env[arg] = self.stack.pop()
            elif instr == 'PRINT':
                val = self.stack.pop()
                print(val)
            else:
                raise RuntimeError(f'Unknown instruction {instr}')

if __name__ == '__main__':
    source = "let x = 3 + 4 * 2 ; let y = x - 1 ; print y"
    bc = compile_source(source)
    vm = VM(bc)
    vm.run()
