# thompson_nfa.py
# Implementation of Thompson's construction for regular expressions to NFA
# Supports concatenation, alternation (|), Kleene star (*), plus (+), optional (?),
# character classes ([a-z]), dot (.), and grouping with parentheses.
# Matching is performed via simultaneous NFA simulation (epsilon-closure and active state set).

import sys
import string
from typing import List, Set, Dict, Tuple, Optional

# ---------- Lexer ----------
TOKEN_CHAR = "CHAR"
TOKEN_DOT = "DOT"
TOKEN_ALT = "ALT"
TOKEN_STAR = "STAR"
TOKEN_PLUS = "PLUS"
TOKEN_QMARK = "QMARK"
TOKEN_LPAREN = "LPAREN"
TOKEN_RPAREN = "RPAREN"
TOKEN_LBRACK = "LBRACK"
TOKEN_RBRACK = "RBRACK"
TOKEN_EOF = "EOF"

class Token:
    def __init__(self, typ: str, value: Optional[str] = None):
        self.typ = typ
        self.value = value
    def __repr__(self):
        return f"Token({self.typ}, {self.value})"

class Lexer:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0
    def next(self) -> Token:
        if self.pos >= len(self.pattern):
            return Token(TOKEN_EOF)
        c = self.pattern[self.pos]
        self.pos += 1
        if c == '|':
            return Token(TOKEN_ALT)
        if c == '*':
            return Token(TOKEN_STAR)
        if c == '+':
            return Token(TOKEN_PLUS)
        if c == '?':
            return Token(TOKEN_QMARK)
        if c == '(': 
            return Token(TOKEN_LPAREN)
        if c == ')':
            return Token(TOKEN_RPAREN)
        if c == '[':
            # read until ]
            start = self.pos
            while self.pos < len(self.pattern) and self.pattern[self.pos] != ']':
                self.pos += 1
            if self.pos >= len(self.pattern):
                raise ValueError('Unclosed character class')
            chars = self.pattern[start:self.pos]
            self.pos += 1  # skip ]
            return Token(TOKEN_CHAR, f'[{chars}]')
        if c == '.':
            return Token(TOKEN_DOT)
        # any other literal character
        return Token(TOKEN_CHAR, c)

# ---------- Parser ----------
# Grammar (explicit concatenation):
# expr   ::= term ('|' term)*
# term   ::= factor+   (concatenation is implicit)
# factor ::= base ('*' | '+' | '?')*
# base   ::= CHAR | '.' | '(' expr ')' | '[' ... ']'

class ASTNode:
    pass

class CharNode(ASTNode):
    def __init__(self, chars: str):
        self.chars = chars  # may be single char or class like [a-z]

class DotNode(ASTNode):
    pass

class AltNode(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

class ConcatNode(ASTNode):
    def __init__(self, left: ASTNode, right: ASTNode):
        self.left = left
        self.right = right

class StarNode(ASTNode):
    def __init__(self, child: ASTNode):
        self.child = child

class PlusNode(ASTNode):
    def __init__(self, child: ASTNode):
        self.child = child

class QuestionNode(ASTNode):
    def __init__(self, child: ASTNode):
        self.child = child

class Parser:
    def __init__(self, lexer: Lexer):
        self.lexer = lexer
        self.cur = self.lexer.next()
    def eat(self, typ):
        if self.cur.typ == typ:
            self.cur = self.lexer.next()
        else:
            raise ValueError(f'Unexpected token: {self.cur}, expected {typ}')
    def parse(self) -> ASTNode:
        return self.expr()
    def expr(self) -> ASTNode:
        node = self.term()
        while self.cur.typ == TOKEN_ALT:
            self.eat(TOKEN_ALT)
            right = self.term()
            node = AltNode(node, right)
        return node
    def term(self) -> ASTNode:
        nodes = []
        while self.cur.typ in (TOKEN_CHAR, TOKEN_DOT, TOKEN_LPAREN, TOKEN_LBRACK):
            nodes.append(self.factor())
        if not nodes:
            # epsilon, represented as empty CharNode with empty string
            return CharNode('')
        node = nodes[0]
        for nxt in nodes[1:]:
            node = ConcatNode(node, nxt)
        return node
    def factor(self) -> ASTNode:
        base = self.base()
        while self.cur.typ in (TOKEN_STAR, TOKEN_PLUS, TOKEN_QMARK):
            if self.cur.typ == TOKEN_STAR:
                self.eat(TOKEN_STAR)
                base = StarNode(base)
            elif self.cur.typ == TOKEN_PLUS:
                self.eat(TOKEN_PLUS)
                base = PlusNode(base)
            else:
                self.eat(TOKEN_QMARK)
                base = QuestionNode(base)
        return base
    def base(self) -> ASTNode:
        if self.cur.typ == TOKEN_CHAR:
            val = self.cur.value
            self.eat(TOKEN_CHAR)
            return CharNode(val)
        if self.cur.typ == TOKEN_DOT:
            self.eat(TOKEN_DOT)
            return DotNode()
        if self.cur.typ == TOKEN_LPAREN:
            self.eat(TOKEN_LPAREN)
            node = self.expr()
            self.eat(TOKEN_RPAREN)
            return node
        raise ValueError('Unexpected token in base')

# ---------- Thompson Construction ----------
class State:
    def __init__(self):
        self.id = State.next_id()
        self.transitions: Dict[Optional[str], List['State']] = {}
    _counter = 0
    @classmethod
    def next_id(cls):
        cls._counter += 1
        return cls._counter
    def add_transition(self, symbol: Optional[str], state: 'State'):
        self.transitions.setdefault(symbol, []).append(state)
    def __repr__(self):
        return f"State({self.id})"

class NFAFragment:
    def __init__(self, start: State, accepts: Set[State]):
        self.start = start
        self.accepts = accepts

class ThompsonBuilder:
    def build(self, node: ASTNode) -> NFAFragment:
        if isinstance(node, CharNode):
            start = State()
            accept = State()
            if node.chars == '':  # epsilon
                start.add_transition(None, accept)
            elif node.chars.startswith('['):
                charset = node.chars[1:-1]
                for ch in self.expand_charset(charset):
                    start.add_transition(ch, accept)
            else:
                start.add_transition(node.chars, accept)
            return NFAFragment(start, {accept})
        if isinstance(node, DotNode):
            start = State()
            accept = State()
            for ch in map(chr, range(32, 127)):
                start.add_transition(ch, accept)
            return NFAFragment(start, {accept})
        if isinstance(node, ConcatNode):
            left = self.build(node.left)
            right = self.build(node.right)
            for a in left.accepts:
                a.add_transition(None, right.start)
            return NFAFragment(left.start, right.accepts)
        if isinstance(node, AltNode):
            start = State()
            left = self.build(node.left)
            right = self.build(node.right)
            start.add_transition(None, left.start)
            start.add_transition(None, right.start)
            accepts = left.accepts.union(right.accepts)
            return NFAFragment(start, accepts)
        if isinstance(node, StarNode):
            start = State()
            sub = self.build(node.child)
            start.add_transition(None, sub.start)
            for a in sub.accepts:
                a.add_transition(None, sub.start)
                a.add_transition(None, start)
            return NFAFragment(start, {start})
        if isinstance(node, PlusNode):
            sub = self.build(node.child)
            start = State()
            start.add_transition(None, sub.start)
            for a in sub.accepts:
                a.add_transition(None, sub.start)
            return NFAFragment(start, sub.accepts)
        if isinstance(node, QuestionNode):
            sub = self.build(node.child)
            start = State()
            start.add_transition(None, sub.start)
            start.add_transition(None, sub.accepts.pop())
            return NFAFragment(start, {sub.accepts.pop()})
        raise ValueError('Unknown AST node')
    def expand_charset(self, s: str) -> Set[str]:
        chars = set()
        i = 0
        while i < len(s):
            if i+2 < len(s) and s[i+1] == '-':
                start = s[i]
                end = s[i+2]
                for c in range(ord(start), ord(end)+1):
                    chars.add(chr(c))
                i += 3
            else:
                chars.add(s[i])
                i += 1
        return chars

# ---------- Simulation ----------
def epsilon_closure(states: Set[State]) -> Set[State]:
    stack = list(states)
    closure = set(states)
    while stack:
        s = stack.pop()
        for nxt in s.transitions.get(None, []):
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure

def move(states: Set[State], ch: str) -> Set[State]:
    result = set()
    for s in states:
        for nxt in s.transitions.get(ch, []):
            result.add(nxt)
    return result

def matches(nfa: NFAFragment, string: str) -> bool:
    current = epsilon_closure({nfa.start})
    for ch in string:
        current = epsilon_closure(move(current, ch))
        if not current:
            break
    return any(state in nfa.accepts for state in current)

# ---------- Test Harness ----------
def test(pattern: str, should_match: List[str], should_not_match: List[str]):
    lexer = Lexer(pattern)
    parser = Parser(lexer)
    ast = parser.parse()
    builder = ThompsonBuilder()
    nfa = builder.build(ast)
    for s in should_match:
        assert matches(nfa, s), f"Pattern {pattern} should match {s}"
    for s in should_not_match:
        assert not matches(nfa, s), f"Pattern {pattern} should NOT match {s}"
    print(f"All tests passed for pattern: {pattern}")

if __name__ == '__main__':
    test('a(b|c)*d', ['ad', 'abcd', 'abcbcd'], ['aed'])
    test('[0-9]+', ['123'], ['abc'])
