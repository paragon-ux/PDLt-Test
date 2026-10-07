# Wrong: + is built like *, so it also accepts zero repetitions.
class State:
    def __init__(self):
        self.edges = []      # (predicate, target): predicate(ch) -> bool
        self.eps = []


class Fragment:
    def __init__(self, start, accept):
        self.start, self.accept = start, accept


class Parser:
    """regex := alt ; alt := concat ('|' concat)* ; concat := repeat+ ; repeat := atom [*+?]*"""

    def __init__(self, pattern):
        self.p, self.i = pattern, 0

    def peek(self):
        return self.p[self.i] if self.i < len(self.p) else None

    def parse(self):
        frag = self.alt()
        if self.peek() is not None:
            raise ValueError(f"unexpected {self.peek()!r} at {self.i}")
        return frag

    def alt(self):
        frag = self.concat()
        while self.peek() == "|":
            self.i += 1
            right = self.concat()
            s, a = State(), State()
            s.eps += [frag.start, right.start]
            frag.accept.eps.append(a)
            right.accept.eps.append(a)
            frag = Fragment(s, a)
        return frag

    def concat(self):
        frag = None
        while self.peek() not in (None, "|", ")"):
            nxt = self.repeat()
            if frag is None:
                frag = nxt
            else:
                frag.accept.eps.append(nxt.start)
                frag = Fragment(frag.start, nxt.accept)
        if frag is None:
            s = State()
            frag = Fragment(s, s)
        return frag

    def repeat(self):
        frag = self.atom()
        while self.peek() in ("*", "+", "?"):
            op = self.p[self.i]
            self.i += 1
            s, a = State(), State()
            s.eps.append(frag.start)
            frag.accept.eps.append(a)
            if op in "*+?":
                s.eps.append(a)
            if op in "*+":
                frag.accept.eps.append(frag.start)
            frag = Fragment(s, a)
        return frag

    def atom(self):
        ch = self.peek()
        if ch == "(":
            self.i += 1
            frag = self.alt()
            if self.peek() != ")":
                raise ValueError("missing )")
            self.i += 1
            return frag
        if ch == "[":
            end = self.p.index("]", self.i)
            body = self.p[self.i + 1:end]
            self.i = end + 1
            ranges, k = [], 0
            while k < len(body):
                if k + 2 < len(body) and body[k + 1] == "-":
                    ranges.append((body[k], body[k + 2]))
                    k += 3
                else:
                    ranges.append((body[k], body[k]))
                    k += 1
            pred = lambda c, r=tuple(ranges): any(lo <= c <= hi for lo, hi in r)
        elif ch == ".":
            self.i += 1
            pred = lambda c: True
        elif ch is None or ch in "*+?)|":
            raise ValueError(f"unexpected {ch!r} at {self.i}")
        else:
            self.i += 1
            pred = lambda c, x=ch: c == x
        s, a = State(), State()
        s.edges.append((pred, a))
        return Fragment(s, a)


def compile_regex(pattern):
    return Parser(pattern).parse()


def _closure(states):
    stack, seen = list(states), set(states)
    while stack:
        for nxt in stack.pop().eps:
            if nxt not in seen:
                seen.add(nxt)
                stack.append(nxt)
    return seen


def nfa_match(pattern, text):
    nfa = compile_regex(pattern)
    current = _closure([nfa.start])
    for ch in text:
        current = _closure([t for s in current for pred, t in s.edges if pred(ch)])
        if not current:
            return False
    return nfa.accept in current
