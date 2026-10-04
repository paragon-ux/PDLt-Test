"""Hidden tests for 05-04: LCS by dynamic programming, with the subsequence reconstructed.

The function takes (s1, s2) and must return both the length and an actual LCS.
The result shape is open: a (length, string) or (string, length) pair, or a dict.
Any longest common subsequence passes, not one particular string.
"""
TEST_SECONDS = 20


def CANDIDATES():
    return functions_named("lcs", "longest_common_subsequence", "lcs_with_reconstruction", "compute_lcs",
                           "lcs_reconstruct", params=2)


def _unpack(result):
    if isinstance(result, dict):
        values = list(result.values())
    elif isinstance(result, (tuple, list)):
        values = list(result)
    else:
        raise AssertionError(f"unrecognised result: {type(result).__name__}")
    lengths = [v for v in values if isinstance(v, int) and not isinstance(v, bool)]
    strings = [v for v in values if isinstance(v, str)]
    assert len(lengths) == 1 and len(strings) == 1, values
    return lengths[0], strings[0]


def _is_subsequence(sub, s):
    it = iter(s)
    return all(ch in it for ch in sub)


def _length(a, b):
    prev = [0] * (len(b) + 1)
    for ch in a:
        cur = [0]
        for j, other in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if ch == other else max(prev[j], cur[j - 1]))
        prev = cur
    return prev[-1]


def _check(f, a, b):
    length, sub = _unpack(f(a, b))
    expected = _length(a, b)
    assert length == expected == len(sub), (length, sub, expected)
    assert _is_subsequence(sub, a) and _is_subsequence(sub, b), sub


def test_prompt_example(f):
    length, sub = _unpack(f("AGGTAB", "GXTXAYB"))
    assert length == 4 and sub == "GTAB"


def test_edge_cases(f):
    _check(f, "ABCDEF", "ABCDEF")
    _check(f, "", "ABC")
    _check(f, "ABC", "")
    _check(f, "ABC", "XYZ")


def test_random_strings(f):
    import random

    rng = random.Random(8)
    for _ in range(40):
        a = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 25)))
        b = "".join(rng.choice("ACGT") for _ in range(rng.randint(0, 25)))
        _check(f, a, b)


TESTS = [test_prompt_example, test_edge_cases, test_random_strings]
