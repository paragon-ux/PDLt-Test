import re
from typing import List, Set, Dict, Tuple

class State:
    def __init__(self):
        self.edges: List[Tuple[str, 'State']] = []  # (symbol, destination)
        self.epsilon: List['State'] = []
        self.is_accept: bool = False

    def add_edge(self, symbol: str, state: 'State'):
        self.edges.append((symbol, state))

    def add_epsilon(self, state: 'State'):
        self.epsilon.append(state)

class NFA:
    def __init__(self, start: State, accept: State):
        self.start = start
        self.accept = accept

    @staticmethod
    def _epsilon_closure(states: Set[State]) -> Set[State]:
        stack = list(states)
        closure = set(states)
        while stack:
            s = stack.pop()
            for nxt in s.epsilon:
                if nxt not in closure:
                    closure.add(nxt)
                    stack.append(nxt)
        return closure

    def matches(self, s: str) -> bool:
        current = self._epsilon_closure({self.start})
        for ch in s:
            nxt = set()
            for state in current:
                for sym, dest in state.edges:
                    if sym == '.':
                        nxt.add(dest)
                    elif sym.startswith('['):
                        # character class like [a-z] or [0-9]
                        if re.fullmatch(sym, ch):
                            nxt.add(dest)
                    elif sym == ch:
                        nxt.add(dest)
            current = self._epsilon_closure(nxt)
        return self.accept in current

# Thompson construction utilities

def literal(ch: str) -> NFA:
    s = State()
    a = State()
    s.add_edge(ch, a)
    a.is_accept = True
    return NFA(s, a)

def dot() -> NFA:
    s = State()
    a = State()
    s.add_edge('.', a)
    a.is_accept = True
    return NFA(s, a)

def char_class(pattern: str) -> NFA:
    s = State()
    a = State()
    s.add_edge(pattern, a)
    a.is_accept = True
    return NFA(s, a)

def concatenate(n1: NFA, n2: NFA) -> NFA:
    n1.accept.is_accept = False
    n1.accept.add_epsilon(n2.start)
    return NFA(n1.start, n2.accept)

def alternate(n1: NFA, n2: NFA) -> NFA:
    s = State()
    a = State()
    s.add_epsilon(n1.start)
    s.add_epsilon(n2.start)
    n1.accept.is_accept = False
    n2.accept.is_accept = False
    n1.accept.add_epsilon(a)
    n2.accept.add_epsilon(a)
    a.is_accept = True
    return NFA(s, a)

def kleene_star(n: NFA) -> NFA:
    s = State()
    a = State()
    s.add_epsilon(n.start)
    s.add_epsilon(a)
    n.accept.is_accept = False
    n.accept.add_epsilon(n.start)
    n.accept.add_epsilon(a)
    a.is_accept = True
    return NFA(s, a)

def plus(n: NFA) -> NFA:
    return concatenate(n, kleene_star(n))

def optional(n: NFA) -> NFA:
    s = State()
    a = State()
    s.add_epsilon(n.start)
    s.add_epsilon(a)
    n.accept.is_accept = False
    n.accept.add_epsilon(a)
    a.is_accept = True
    return NFA(s, a)

# Shunting‑yard to convert regex to postfix
precedence = {'*': 3, '+': 3, '?': 3, '.': 2, '|': 1}
right_assoc = {'*', '+', '?'}

def insert_concat(regex: str) -> str:
    result = ''
    prev = None
    for c in regex:
        if prev:
            if (prev.isalnum() or prev in '])}') or prev == '.' or prev == '*':
                if (c.isalnum() or c == '(' or c == '[' or c == '.' ):  # start of new token
                    result += '.'
        result += c
        prev = c
    return result

def to_postfix(regex: str) -> List[str]:
    output: List[str] = []
    stack: List[str] = []
    i = 0
    while i < len(regex):
        c = regex[i]
        if c == '[':
            j = i
            while regex[j] != ']':
                j += 1
            token = regex[i:j+1]
            output.append(token)
            i = j
        elif c.isalnum():
            output.append(c)
        elif c == '.':
            output.append(c)
        elif c == '(':
            stack.append(c)
        elif c == ')':
            while stack and stack[-1] != '(':
                output.append(stack.pop())
            stack.pop()  # '(' removal
        elif c in precedence:
            while stack and stack[-1] != '(' and (
                (precedence[stack[-1]] > precedence[c]) or
                (precedence[stack[-1]] == precedence[c] and c not in right_assoc)
            ):
                output.append(stack.pop())
            stack.append(c)
        i += 1
    while stack:
        output.append(stack.pop())
    return output

def build_nfa(postfix: List[str]) -> NFA:
    stack: List[NFA] = []
    for token in postfix:
        if token == '.':
            stack.append(dot())
        elif token.startswith('['):
            stack.append(char_class(token))
        elif token.isalnum():
            stack.append(literal(token))
        elif token == '*':
            n = stack.pop()
            stack.append(kleene_star(n))
        elif token == '+':
            n = stack.pop()
            stack.append(plus(n))
        elif token == '?':
            n = stack.pop()
            stack.append(optional(n))
        elif token == '.':
            n2 = stack.pop()
            n1 = stack.pop()
            stack.append(concatenate(n1, n2))
        elif token == '|':
            n2 = stack.pop()
            n1 = stack.pop()
            stack.append(alternate(n1, n2))
        else:
            # Concatenation operator inserted as '.'
            n2 = stack.pop()
            n1 = stack.pop()
            stack.append(concatenate(n1, n2))
    return stack[0]

def compile_regex(pattern: str) -> NFA:
    pattern = insert_concat(pattern)
    postfix = to_postfix(pattern)
    return build_nfa(postfix)

# Unit tests
import unittest

class TestThompsonNFA(unittest.TestCase):
    def test_abcd(self):
        nfa = compile_regex('a(b|c)*d')
        self.assertTrue(nfa.matches('ad'))
        self.assertTrue(nfa.matches('abcd'))
        self.assertTrue(nfa.matches('abcbcd'))
        self.assertFalse(nfa.matches('aed'))

    def test_digits(self):
        nfa = compile_regex('[0-9]+')
        self.assertTrue(nfa.matches('123'))
        self.assertFalse(nfa.matches('abc'))

if __name__ == '__main__':
    unittest.main()
