"""Hidden tests for 04-01: a recursive-descent calculator.

From the prompt:
- +, -, *, /, unary minus, parentheses, integer and float literals;
- unary minus binds tighter than * and /, which bind tighter than + and -;
- binary operators are left-associative;
- the result is a number, not an AST;
- a malformed expression raises an error.

The entry point is open: a one-argument function (evaluate, calculate, parse,
...), or a class used as Class().method(expr) or Class(expr).method(). Each
candidate is an evaluator taking the expression text.
"""
TEST_SECONDS = 20
_NAMES = ("evaluate", "calculate", "calc", "parse", "eval_expr", "evaluate_expression", "compute", "evaluate_expr",
          "parse_and_evaluate", "parse_expression", "eval_expression", "run", "interpret")


def CANDIDATES():
    named = list(functions_named(*_NAMES))
    methods = [_method_adapter(cls, m) for cls in classes_with() for m in _NAMES if callable(getattr(cls, m, None))]
    others = [f for f in functions_named(*_NAMES, params=1) if f not in named]
    return named + methods + others


def _method_adapter(cls, method):
    def evaluate(text):
        try:
            obj = cls()
        except TypeError:
            return getattr(cls(text), method)()
        try:
            return getattr(obj, method)(text)
        except TypeError:
            return getattr(cls(text), method)()

    evaluate.__name__ = f"{cls.__name__}.{method}"
    return evaluate


def _value(f, text):
    result = f(text)
    assert isinstance(result, (int, float)) and not isinstance(result, bool), f"{text!r} gave {result!r}"
    return result


def test_prompt_examples(f):
    assert approx(_value(f, "3 + 4 * 2"), 11)
    assert approx(_value(f, "-(3 + 4) * 2"), -14)
    assert approx(_value(f, "10 / 3"), 10 / 3)


def test_precedence_and_associativity(f):
    cases = {
        "8 - 3 - 2": 3, "64 / 8 / 2": 4, "2 + 3 * 4 - 5": 9, "2 * 3 + 4 * 5": 26, "(2 + 3) * (4 - 1)": 15,
        "100 / 10 * 2": 20, "1 - 2 + 3": 2, "((((7))))": 7, "2*3+4": 10, "7 - -2": 9, "-3 * -2": 6,
        "-(-(4))": 4, "2 * -3": -6, "-2 + 5": 3, "10 / 4": 2.5, "1.5 * 2": 3.0, "0.25 + 0.5": 0.75,
        "3.0 / 2": 1.5, "12 - 4 / 2 * 3": 6,
    }
    for text, expected in cases.items():
        assert approx(_value(f, text), expected), (text, f(text), expected)


def test_random_expressions(f):
    import random

    rng = random.Random(41)

    def gen(depth):
        if depth == 0 or rng.random() < 0.3:
            return str(rng.randint(1, 9))
        kind = rng.random()
        if kind < 0.15:
            return "-(" + gen(depth - 1) + ")"
        if kind < 0.3:
            return "(" + gen(depth - 1) + ")"
        return gen(depth - 1) + " " + rng.choice("+-*") + " " + gen(depth - 1)

    for _ in range(60):
        text = gen(4)
        assert approx(_value(f, text), eval(text)), text


def test_malformed_expressions_raise(f):
    for text in ("(1 + 2", "1 + 2)", "1 +", "* 3", "", "2 3", "4 * / 2", "()"):
        try:
            result = f(text)
        except Exception:  # noqa: BLE001 - any raised error is the required report
            continue
        raise AssertionError(f"{text!r} returned {result!r} instead of raising")


TESTS = [test_prompt_examples, test_precedence_and_associativity, test_random_expressions,
         test_malformed_expressions_raise]
