import re

class CalculatorError(Exception):
    pass

class Token:
    NUMBER = 'NUMBER'
    PLUS = 'PLUS'
    MINUS = 'MINUS'
    MUL = 'MUL'
    DIV = 'DIV'
    LPAREN = 'LPAREN'
    RPAREN = 'RPAREN'
    EOF = 'EOF'

    def __init__(self, type_, value=None):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f'Token({self.type}, {self.value})'

class Lexer:
    token_specification = [
        ('NUMBER',  r'\d+(?:\.\d*)?|\.\d+'),
        ('PLUS',    r'\+'),
        ('MINUS',   r'-'),
        ('MUL',     r'\*'),
        ('DIV',     r'/'),
        ('LPAREN',  r'\('),
        ('RPAREN',  r'\)'),
        ('SKIP',    r'[ \t]+'),
        ('MISMATCH',r'.'),
    ]
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(tok_regex).match

    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.current_match = None
        self.next_token = self._advance()

    def _advance(self):
        while self.pos < len(self.text):
            self.current_match = self.get_token(self.text, self.pos)
            if not self.current_match:
                raise CalculatorError(f'Unexpected character at position {self.pos}')
            typ = self.current_match.lastgroup
            val = self.current_match.group(typ)
            self.pos = self.current_match.end()
            if typ == 'NUMBER':
                return Token(Token.NUMBER, float(val))
            elif typ == 'PLUS':
                return Token(Token.PLUS)
            elif typ == 'MINUS':
                return Token(Token.MINUS)
            elif typ == 'MUL':
                return Token(Token.MUL)
            elif typ == 'DIV':
                return Token(Token.DIV)
            elif typ == 'LPAREN':
                return Token(Token.LPAREN)
            elif typ == 'RPAREN':
                return Token(Token.RPAREN)
            elif typ == 'SKIP':
                continue
            else:
                raise CalculatorError(f'Invalid token {val}')
        return Token(Token.EOF)

    def peek(self):
        return self.next_token

    def consume(self, token_type=None):
        current = self.next_token
        if token_type and current.type != token_type:
            raise CalculatorError(f'Expected token {token_type} but got {current.type}')
        self.next_token = self._advance()
        return current

class Parser:
    def __init__(self, lexer):
        self.lexer = lexer

    def parse(self):
        value = self.parse_expression()
        if self.lexer.peek().type != Token.EOF:
            raise CalculatorError('Unexpected token after end of expression')
        return value

    def parse_expression(self):
        value = self.parse_term()
        while self.lexer.peek().type in (Token.PLUS, Token.MINUS):
            op = self.lexer.consume().type
            right = self.parse_term()
            if op == Token.PLUS:
                value += right
            else:
                value -= right
        return value

    def parse_term(self):
        value = self.parse_factor()
        while self.lexer.peek().type in (Token.MUL, Token.DIV):
            op = self.lexer.consume().type
            right = self.parse_factor()
            if op == Token.MUL:
                value *= right
            else:
                if right == 0:
                    raise CalculatorError('Division by zero')
                value /= right
        return value

    def parse_factor(self):
        if self.lexer.peek().type == Token.MINUS:
            self.lexer.consume(Token.MINUS)
            return -self.parse_factor()
        return self.parse_primary()

    def parse_primary(self):
        token = self.lexer.peek()
        if token.type == Token.NUMBER:
            self.lexer.consume(Token.NUMBER)
            return token.value
        if token.type == Token.LPAREN:
            self.lexer.consume(Token.LPAREN)
            value = self.parse_expression()
            if self.lexer.peek().type != Token.RPAREN:
                raise CalculatorError('Unmatched parentheses')
            self.lexer.consume(Token.RPAREN)
            return value
        raise CalculatorError(f'Unexpected token {token.type}')

def evaluate(expression: str) -> float:
    lexer = Lexer(expression)
    parser = Parser(lexer)
    return parser.parse()

# Test suite
if __name__ == '__main__':
    import math
    tests = [
        ("3 + 4 * 2", 11),
        ("-(3 + 4) * 2", -14),
        ("10 / 3", 10/3),
    ]
    for expr, expected in tests:
        result = evaluate(expr)
        if isinstance(expected, float):
            assert math.isclose(result, expected, rel_tol=1e-9), f'Failed: {expr} -> {result}, expected approx {expected}'
        else:
            assert result == expected, f'Failed: {expr} -> {result}, expected {expected}'
    # Error cases
    error_cases = [
        "(1 + 2",          # unmatched parentheses
        "1 + * 2",         # missing operand
        "1 / 0",           # division by zero
    ]
    for expr in error_cases:
        try:
            evaluate(expr)
            assert False, f'Expression {expr} should have raised an error'
        except CalculatorError:
            pass
    print('All tests passed')
