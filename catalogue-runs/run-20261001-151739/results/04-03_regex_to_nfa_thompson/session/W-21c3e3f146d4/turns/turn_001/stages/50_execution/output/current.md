import re
from collections import defaultdict

class State:
    __slots__ = ('edges', 'epsilon')
    def __init__(self):
        self.edges = defaultdict(list)  # symbol -> list of State
        self.epsilon = []  # list of State

def epsilon_closure(states):
    stack = list(states)
    closure = set(states)
    while stack:
        s = stack.pop()
        for ns in s.epsilon:
            if ns not in closure:
                closure.add(ns)
                stack.append(ns)
    return closure

def move(states, char):
    nxt = set()
    for s in states:
        for ns in s.edges.get(char, []):
            nxt.add(ns)
        for ns in s.edges.get('.', []):  # dot matches any char
            nxt.add(ns)
    return nxt

class NFA:
    def __init__(self, start, accept):
        self.start = start
        self.accept = accept

    @staticmethod
    def literal(ch):
        s1 = State()
        s2 = State()
        s1.edges[ch].append(s2)
        return NFA(s1, s2)

    @staticmethod
    def dot():
        s1 = State()
        s2 = State()
        s1.edges['.'].append(s2)
        return NFA(s1, s2)

    @staticmethod
    def character_class(chars):
        s1 = State()
        s2 = State()
        for c in chars:
            s1.edges[c].append(s2)
        return NFA(s1, s2)

    @staticmethod
    def concat(nfa1, nfa2):
        nfa1.accept.epsilon.append(nfa2.start)
        return NFA(nfa1.start, nfa2.accept)

    @staticmethod
    def alternate(nfa1, nfa2):
        s = State()
        s.epsilon.extend([nfa1.start, nfa2.start])
        a = State()
        nfa1.accept.epsilon.append(a)
        nfa2.accept.epsilon.append(a)
        return NFA(s, a)

    @staticmethod
    def kleene_star(nfa):
        s = State()
        a = State()
        s.epsilon.extend([nfa.start, a])
        nfa.accept.epsilon.extend([nfa.start, a])
        return NFA(s, a)

    @staticmethod
    def plus(nfa):
        # n+ = n n*
        return NFA.concat(nfa, NFA.kleene_star(nfa))

    @staticmethod
    def optional(nfa):
        # n? = n | ε
        return NFA.alternate(nfa, NFA.epsilon())

    @staticmethod
    def epsilon():
        s = State()
        a = State()
        s.epsilon.append(a)
        return NFA(s, a)

    def matches(self, string):
        current = epsilon_closure({self.start})
        for ch in string:
            current = epsilon_closure(move(current, ch))
        return self.accept in current

# Parser using recursive descent
class Parser:
    def __init__(self, pattern):
        self.pattern = pattern
        self.pos = 0
        self.current = self.pattern[0] if self.pattern else None

    def advance(self):
        self.pos += 1
        self.current = self.pattern[self.pos] if self.pos < len(self.pattern) else None

    def parse(self):
        nfa = self.expression()
        if self.current is not None:
            raise ValueError('Unexpected character at end')
        return nfa

    def expression(self):
        terms = [self.term()]
        while self.current == '|':
            self.advance()
            terms.append(self.term())
        nfa = terms[0]
        for t in terms[1:]:
            nfa = NFA.alternate(nfa, t)
        return nfa

    def term(self):
        factors = []
        while self.current and self.current not in '|)'
            :
            factors.append(self.factor())
        if not factors:
            return NFA.epsilon()
        nfa = factors[0]
        for f in factors[1:]:
            nfa = NFA.concat(nfa, f)
        return nfa

    def factor(self):
        base = self.base()
        while self.current in '*+?':
            if self.current == '*':
                base = NFA.kleene_star(base)
            elif self.current == '+':
                base = NFA.plus(base)
            elif self.current == '?':
                base = NFA.optional(base)
            self.advance()
        return base

    def base(self):
        if self.current == '(':
            self.advance()
            nfa = self.expression()
            if self.current != ')':
                raise ValueError('Missing closing parenthesis')
            self.advance()
            return nfa
        if self.current == '.':
            self.advance()
            return NFA.dot()
        if self.current == '[':
            self.advance()
            chars = []
            while self.current and self.current != ']':
                chars.append(self.current)
                self.advance()
            if self.current != ']':
                raise ValueError('Unclosed character class')
            self.advance()
            return NFA.character_class(chars)
        # literal character
        ch = self.current
        self.advance()
        return NFA.literal(ch)

def build_nfa(pattern):
    parser = Parser(pattern)
    return parser.parse()

# Tests
if __name__ == '__main__':
    tests = [
        ('a(b|c)*d', ['ad', 'abcd', 'abcbcd'], ['aed']),
        ('[0-9]+', ['123'], ['abc'])
    ]
    for pat, should_match, should_reject in tests:
        nfa = build_nfa(pat)
        for s in should_match:
            assert nfa.matches(s), f"Pattern {pat} should match {s}"
        for s in should_reject:
            assert not nfa.matches(s), f"Pattern {pat} should reject {s}"
    print('All tests passed')
