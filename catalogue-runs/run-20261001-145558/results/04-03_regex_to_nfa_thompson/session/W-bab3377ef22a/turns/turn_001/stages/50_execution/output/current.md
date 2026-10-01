import re
from typing import List, Set, Tuple, Dict

class State:
    def __init__(self, is_end: bool = False):
        self.is_end = is_end
        self.transitions: Dict[str, List['State']] = {}
        self.epsilon: List['State'] = []

    def add_transition(self, symbol: str, state: 'State'):
        self.transitions.setdefault(symbol, []).append(state)

    def add_epsilon(self, state: 'State'):
        self.epsilon.append(state)

class NFA:
    def __init__(self, start: State, end: State):
        self.start = start
        self.end = end

    def _epsilon_closure(self, states: Set[State]) -> Set[State]:
        stack = list(states)
        closure = set(states)
        while stack:
            s = stack.pop()
            for e in s.epsilon:
                if e not in closure:
                    closure.add(e)
                    stack.append(e)
        return closure

    def match(self, s: str) -> bool:
        current = self._epsilon_closure({self.start})
        for ch in s:
            nxt: Set[State] = set()
            for st in current:
                for sym, dests in st.transitions.items():
                    if sym == '.' or (sym.startswith('[') and ch in sym[1:-1]) or sym == ch:
                        nxt.update(dests)
            current = self._epsilon_closure(nxt)
        return any(st.is_end for st in current)

# Parser utilities
TOKEN_REGEX = re.compile(r"\s*(?:(\d+|\w|\.|\*|\+|\?|\||\(|\)|\[.*?\])|(.))")

class Parser:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0
        self.tokens = self.tokenize(pattern)
        self.current = 0

    def tokenize(self, pattern: str) -> List[str]:
        tokens = []
        i = 0
        while i < len(pattern):
            if pattern[i] == '[':
                j = i + 1
                while j < len(pattern) and pattern[j] != ']':
                    j += 1
                if j >= len(pattern):
                    raise ValueError('Unclosed character class')
                tokens.append(pattern[i:j+1])
                i = j + 1
            else:
                tokens.append(pattern[i])
                i += 1
        return tokens

    def peek(self) -> str:
        return self.tokens[self.current] if self.current < len(self.tokens) else ''

    def advance(self) -> str:
        tok = self.peek()
        self.current += 1
        return tok

    def parse(self):
        expr = self.parse_expression()
        if self.current != len(self.tokens):
            raise ValueError('Unexpected token')
        return expr

    def parse_expression(self):
        terms = [self.parse_term()]
        while self.peek() == '|':
            self.advance()
            terms.append(self.parse_term())
        if len(terms) == 1:
            return terms[0]
        return ('|', terms)

    def parse_term(self):
        factors = []
        while self.peek() and self.peek() not in ')|':
            factors.append(self.parse_factor())
        if not factors:
            return ('ε',)
        if len(factors) == 1:
            return factors[0]
        return ('concat', factors)

    def parse_factor(self):
        base = self.parse_base()
        while self.peek() in '*+?':
            op = self.advance()
            base = (op, base)
        return base

    def parse_base(self):
        tok = self.peek()
        if tok == '(':
            self.advance()
            expr = self.parse_expression()
            if self.peek() != ')':
                raise ValueError('Missing closing parenthesis')
            self.advance()
            return expr
        elif tok.startswith('['):
            self.advance()
            # keep class as is for matching
            return tok
        else:
            self.advance()
            return tok

# Thompson construction
class ThompsonBuilder:
    def build(self, ast) -> NFA:
        typ = ast[0] if isinstance(ast, tuple) else ast
        if typ == 'ε':
            s = State()
            e = State(is_end=True)
            s.add_epsilon(e)
            return NFA(s, e)
        if isinstance(ast, str):
            s = State()
            e = State(is_end=True)
            s.add_transition(ast, e)
            return NFA(s, e)
        if typ == 'concat':
            nfas = [self.build(t) for t in ast[1]]
            for i in range(len(nfas)-1):
                nfas[i].end.is_end = False
                nfas[i].end.add_epsilon(nfas[i+1].start)
            return NFA(nfas[0].start, nfas[-1].end)
        if typ == '|':
            nfas = [self.build(t) for t in ast[1]]
            s = State()
            e = State(is_end=True)
            for n in nfas:
                s.add_epsilon(n.start)
                n.end.is_end = False
                n.end.add_epsilon(e)
            return NFA(s, e)
        if typ == '*':
            inner = self.build(ast[1])
            s = State()
            e = State(is_end=True)
            s.add_epsilon(inner.start)
            s.add_epsilon(e)
            inner.end.is_end = False
            inner.end.add_epsilon(inner.start)
            inner.end.add_epsilon(e)
            return NFA(s, e)
        if typ == '+':
            inner = self.build(ast[1])
            s = State()
            e = State(is_end=True)
            s.add_epsilon(inner.start)
            inner.end.is_end = False
            inner.end.add_epsilon(inner.start)
            inner.end.add_epsilon(e)
            return NFA(s, e)
        if typ == '?':
            inner = self.build(ast[1])
            s = State()
            e = State(is_end=True)
            s.add_epsilon(inner.start)
            s.add_epsilon(e)
            inner.end.is_end = False
            inner.end.add_epsilon(e)
            return NFA(s, e)
        raise ValueError('Unsupported AST node')

# API function
def compile_regex(pattern: str) -> NFA:
    parser = Parser(pattern)
    ast = parser.parse()
    builder = ThompsonBuilder()
    nfa = builder.build(ast)
    # ensure only end state is marked end
    nfa.end.is_end = True
    return nfa

# Tests
if __name__ == "__main__":
    tests: List[Tuple[str, List[Tuple[str, bool]]]] = [
        ("a(b|c)*d", [("ad", True), ("abcd", True), ("abcbcd", True), ("aed", False)]),
        ("[0-9]+", [("123", True), ("abc", False)])
    ]
    for pattern, cases in tests:
        nfa = compile_regex(pattern)
        for string, expected in cases:
            result = nfa.match(string)
            assert result == expected, f"Pattern {pattern!r} on {string!r} expected {expected}, got {result}"
    print("All tests passed.")
