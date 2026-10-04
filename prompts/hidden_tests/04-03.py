"""Hidden tests for 04-03: Thompson's construction and NFA simulation.

From the prompt: concatenation, |, *, +, ?, character classes ([a-z]), dot and
grouping, matched by simulating the NFA over a set of states. The prompt's
examples ("a(b|c)*d" accepts "abcd" and rejects "aed") read as whole-string
matching, which is what an NFA accepting a string means. Expected answers come
from Python's re.fullmatch on the same supported subset.

The entry point is open. The adapter accepts:
- a two-argument matcher (pattern, text), in either order;
- a one-argument builder whose result has a match-like method or is callable;
- a builder plus a two-argument simulator (simulate(nfa, text));
- a class built from the pattern with a match-like method.
The adapter that gets the prompt's examples right is used for every case.
"""
TEST_SECONDS = 40
_MATCHERS = ("match", "matches", "regex_match", "full_match", "fullmatch", "nfa_match", "thompson_match",
             "match_regex", "accepts", "simulate", "run", "search", "is_match")
_BUILDERS = ("compile", "build_nfa", "regex_to_nfa", "thompson", "compile_regex", "build", "to_nfa", "construct_nfa",
             "thompson_construction", "parse", "compile_pattern")
_METHODS = ("match", "matches", "fullmatch", "full_match", "accepts", "accept", "simulate", "run", "test", "is_match")


def _examples_ok(m):
    try:
        return bool(m("a(b|c)*d", "abcd")) and not m("a(b|c)*d", "aed") and \
            bool(m("[0-9]+", "123")) and not m("[0-9]+", "abc")
    except Exception:  # noqa: BLE001 - an adapter that errors is not this deliverable's interface
        return False


def _object_matcher(obj):
    for name in _METHODS:
        method = getattr(obj, name, None)
        if callable(method):
            return method
    return obj if callable(obj) else None


def _adapters():
    funcs2 = functions_named(*_MATCHERS, params=2)
    funcs1 = functions_named(*_BUILDERS, params=1)
    for f in funcs2:
        yield f.__name__, (lambda f: lambda p, t: f(p, t))(f)
        yield f.__name__ + "(text, pattern)", (lambda f: lambda p, t: f(t, p))(f)
    for b in funcs1:
        yield b.__name__ + "().match", (lambda b: lambda p, t: _object_matcher(b(p))(t))(b)
        for f in funcs2:
            yield f"{f.__name__}({b.__name__}(p), t)", (lambda b, f: lambda p, t: f(b(p), t))(b, f)
    for cls in classes_with():
        if any(callable(getattr(cls, m, None)) for m in _METHODS):
            yield cls.__name__ + "(p).match", (lambda c: lambda p, t: _object_matcher(c(p))(t))(cls)


def CANDIDATES():
    """The first adapter that gets the prompt's examples right, else the first adapter."""
    adapters = list(_adapters())
    for name, m in adapters:
        if _examples_ok(m):
            m.__name__ = name
            return [m]
    found = []
    for name, m in adapters[:3]:
        m.__name__ = name
        found.append(m)
    return found


def _check(m, pattern, text):
    import re

    expected = re.fullmatch(pattern, text) is not None
    got = m(pattern, text)
    assert bool(got) is expected, f"{pattern!r} on {text!r}: got {got!r}, expected {expected}"


def test_prompt_examples(m):
    for text in ("ad", "abcd", "abcbcd"):
        _check(m, "a(b|c)*d", text)
    _check(m, "a(b|c)*d", "aed")
    _check(m, "[0-9]+", "123")
    _check(m, "[0-9]+", "abc")


def test_each_operator(m):
    cases = {
        "ab": ["ab", "a", "abc", ""], "a|b": ["a", "b", "ab", ""], "a*": ["", "a", "aaaa", "ab"],
        "a+": ["", "a", "aaa", "b"], "ab?c": ["ac", "abc", "abbc"], "[a-c]x": ["ax", "cx", "dx", "x"],
        "a.c": ["abc", "a.c", "azc", "ac", "abbc"], "(ab)+": ["ab", "abab", "aba", ""],
        "(a|b)*abb": ["abb", "aababb", "ab", "babba"], "x(y|z)?w": ["xw", "xyw", "xzw", "xyzw"],
        "[0-9][a-z]*": ["7", "7abc", "abc", "77"], "(a*)*b": ["b", "aaab", "aaa"], "((a|b)c)+": ["ac", "acbc", "abc"],
    }
    for pattern, texts in cases.items():
        for text in texts:
            _check(m, pattern, text)


def test_random_patterns_against_re(m):
    import random

    rng = random.Random(7)

    def atom(depth):
        r = rng.random()
        if depth > 0 and r < 0.25:
            return "(" + regex(depth - 1) + ")"
        if r < 0.35:
            return "."
        if r < 0.5:
            return rng.choice(["[a-b]", "[b-c]", "[a-c]"])
        return rng.choice("abc")

    def factor(depth):
        return atom(depth) + (rng.choice(["*", "+", "?"]) if rng.random() < 0.35 else "")

    def concat(depth):
        return "".join(factor(depth) for _ in range(rng.randint(1, 3)))

    def regex(depth):
        return "|".join(concat(depth) for _ in range(rng.randint(1, 2)))

    for _ in range(40):
        pattern = regex(2)
        for _ in range(8):
            _check(m, pattern, "".join(rng.choice("abc") for _ in range(rng.randint(0, 6))))


def test_long_input_does_not_backtrack(m):
    # Exponential for a backtracking matcher, linear for an NFA state-set simulation.
    _check(m, "(a|a)*b", "a" * 26)
    _check(m, "(a*)*b", "a" * 26)


TESTS = [test_prompt_examples, test_each_operator, test_random_patterns_against_re, test_long_input_does_not_backtrack]
