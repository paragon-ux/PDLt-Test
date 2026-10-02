"""thompson_nfa.py
Implements a regular expression parser and Thompson construction to build an NFA.
Supports concatenation, alternation '|', Kleene star '*', plus '+', optional '?',
character classes like [a-z], dot '.' and grouping with parentheses.
Provides an NFA simulation that tracks a set of active states (epsilon‑closure).
Includes simple unit tests for the patterns 'a(b|c)*d' and '[0-9]+' as specified.
"""
import sys
import re
from collections import defaultdict

# ---------- Lexer ----------
TOKEN_REGEX = re.compile(r"""
    \s*                             # skip whitespace
    (                               # start group
        \.|\*|\+|\?|\||\(|\)    # single‑character operators
        |\[([^\]]+)\]            # character class, capture inside brackets
        |[^\s\|\*\+\?\(\)\[\]] # literals (any non‑operator char)
    )
""", re.VERBOSE)

def tokenize(pattern):
    pos = 0
    while pos < len(pattern):
        m = TOKEN_REGEX.match(pattern, pos)
        if not m:
            raise ValueError(f"Invalid token at pos {pos}: {pattern[pos:]}")
        token = m.group(1)
        if token.startswith('['):
            token = token  # keep brackets for class handling
        yield token
        pos = m.end()

# ---------- Parser ----------
class Node:
    pass

class Literal(Node):
    def __init__(self, char):
        self.char = char

class Dot(Node):
    pass

class CharClass(Node):
    def __init__(self, chars):
        self.chars = chars  # string inside []

class Concatenation(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Alternation(Node):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class Star(Node):
    def __init__(self, child):
        self.child = child

class Plus(Node):
    def __init__(self, child):
        self.child = child

class Optional(Node):
    def __init__(self, child):
        self.child = child

def parse(pattern):
    tokens = list(tokenize(pattern))
    pos = 0

    def peek():
        return tokens[pos] if pos < len(tokens) else None

    def advance():
        nonlocal pos
        pos += 1
        return tokens[pos-1]

    def parse_expression():
        node = parse_term()
        while peek() == '|':
            advance()
            right = parse_term()
            node = Alternation(node, right)
        return node

    def parse_term():
        factors = []
        while True:
            if peek() is None or peek() in ')|':
                break
            factors.append(parse_factor())
        if not factors:
            return Literal('')  # empty string
        node = factors[0]
        for f in factors[1:]:
            node = Concatenation(node, f)
        return node

    def parse_factor():
        base = parse_base()
        while peek() in ('*', '+', '?'):
            op = advance()
            if op == '*':
                base = Star(base)
            elif op == '+':
                base = Plus(base)
            elif op == '?':
                base = Optional(base)
        return base

    def parse_base():
        tok = peek()
        if tok == '(':
            advance()
            node = parse_expression()
            if peek() != ')':
                raise ValueError('Unmatched (')
            advance()
            return node
        elif tok == '.':
            advance()
            return Dot()
        elif tok and tok.startswith('['):
            advance()
            inner = tok[1:-1]
            return CharClass(inner)
        else:
            advance()
            return Literal(tok)

    return parse_expression()

# ---------- NFA Construction ----------
class State:
    def __init__(self):
        self.id = id(self)
        self.transitions = defaultdict(set)  # char -> set of states
        self.epsilon = set()

    def add_transition(self, symbol, state):
        if symbol is None:
            self.epsilon.add(state)
        else:
            self.transitions[symbol].add(state)

class Fragment:
    def __init__(self, start, accepts):
        self.start = start
        self.accepts = accepts  # set of accept states


def new_state():
    return State()

def build(node):
    if isinstance(node, Literal):
        s = new_state()
        a = new_state()
        s.add_transition(node.char, a)
        return Fragment(s, {a})
    if isinstance(node, Dot):
        s = new_state()
        a = new_state()
        s.add_transition(None, a)  # placeholder, will treat None as any char in simulation
        s.transitions[None] = set([a])
        return Fragment(s, {a})
    if isinstance(node, CharClass):
        s = new_state()
        a = new_state()
        for ch in node.chars:
            s.add_transition(ch, a)
        return Fragment(s, {a})
    if isinstance(node, Concatenation):
        left = build(node.left)
        right = build(node.right)
        for acc in left.accepts:
            acc.add_transition(None, right.start)
        return Fragment(left.start, right.accepts)
    if isinstance(node, Alternation):
        s = new_state()
        a = new_state()
        left = build(node.left)
        right = build(node.right)
        s.add_transition(None, left.start)
        s.add_transition(None, right.start)
        for acc in left.accepts:
            acc.add_transition(None, a)
        for acc in right.accepts:
            acc.add_transition(None, a)
        return Fragment(s, {a})
    if isinstance(node, Star):
        s = new_state()
        a = new_state()
        sub = build(node.child)
        s.add_transition(None, sub.start)
        s.add_transition(None, a)
        for acc in sub.accepts:
            acc.add_transition(None, sub.start)
            acc.add_transition(None, a)
        return Fragment(s, {a})
    if isinstance(node, Plus):
        sub = build(node.child)
        star = Star(node.child)
        star_frag = build(star)
        # connect sub accept to star start via epsilon
        for acc in sub.accepts:
            acc.add_transition(None, star_frag.start)
        return Fragment(sub.start, star_frag.accepts)
    if isinstance(node, Optional):
        s = new_state()
        a = new_state()
        sub = build(node.child)
        s.add_transition(None, sub.start)
        s.add_transition(None, a)
        for acc in sub.accepts:
            acc.add_transition(None, a)
        return Fragment(s, {a})
    raise ValueError('Unsupported node type')

# ---------- Simulation ----------
def epsilon_closure(states):
    stack = list(states)
    closure = set(states)
    while stack:
        st = stack.pop()
        for nxt in st.epsilon:
            if nxt not in closure:
                closure.add(nxt)
                stack.append(nxt)
    return closure

def move(states, char):
    dest = set()
    for st in states:
        # explicit transitions
        for nxt in st.transitions.get(char, []):
            dest.add(nxt)
        # dot handling: transition on None should match any char
        for nxt in st.transitions.get(None, []):
            dest.add(nxt)
    return dest

def matches(pattern, string):
    ast = parse(pattern)
    frag = build(ast)
    current = epsilon_closure({frag.start})
    for ch in string:
        current = epsilon_closure(move(current, ch))
    return any(state in frag.accepts for state in current)

# ---------- Tests ----------
def test():
    assert matches('a(b|c)*d', 'ad')
    assert matches('a(b|c)*d', 'abcd')
    assert matches('a(b|c)*d', 'abcbcd')
    assert not matches('a(b|c)*d', 'aed')
    assert matches('[0-9]+', '123')
    assert not matches('[0-9]+', 'abc')
    print('All tests passed')

if __name__ == '__main__':
    test()
