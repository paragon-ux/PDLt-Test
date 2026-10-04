"""Hidden tests for 05-06: KMP search returning every match index.

The search may take (text, pattern) or (pattern, text): whichever order gives
the prompt example's answer is used for every case. A failure-function builder,
if the deliverable exposes one, must give the partial-match table
[0,0,1,2,0,1,2,3,4] for "ABABCABAB" (or the same table in the shifted "next"
convention, [-1,0,0,1,2,0,1,2,3]).
"""
TEST_SECONDS = 20


def CANDIDATES():
    return functions_named("kmp_search", "kmp", "search", "find_all", "kmp_find", "kmp_find_all", "find_occurrences",
                           "kmp_match", "kmp_find_all_occurrences", params=2)


def _naive(text, pattern):
    return [i for i in range(len(text) - len(pattern) + 1) if text[i:i + len(pattern)] == pattern]


def _order(f):
    text, pattern = "ABABDAABABCABABABABCABAB", "ABABCABAB"
    expected = _naive(text, pattern)
    try:
        if list(f(text, pattern)) == expected:
            return lambda t, p: list(f(t, p))
    except Exception:  # noqa: BLE001 - try the other order
        pass
    return lambda t, p: list(f(p, t))


def test_prompt_example(f):
    search = _order(f)
    assert search("ABABDAABABCABABABABCABAB", "ABABCABAB") == _naive("ABABDAABABCABABABABCABAB", "ABABCABAB")


def test_overlapping_and_edge_matches(f):
    search = _order(f)
    assert search("AAAAA", "AA") == [0, 1, 2, 3]
    assert search("ABCABCABC", "ABC") == [0, 3, 6]
    assert search("ABC", "D") == []
    assert search("ABC", "ABCD") == []


def test_random_against_naive(f):
    import random

    rng = random.Random(12)
    search = _order(f)
    for _ in range(150):
        text = "".join(rng.choice("AB") for _ in range(rng.randint(0, 60)))
        pattern = "".join(rng.choice("AB") for _ in range(rng.randint(1, 5)))
        assert search(text, pattern) == _naive(text, pattern), (text, pattern)


def test_failure_function_if_exposed(f):
    builders = functions_named("build_failure", "failure_function", "build_failure_function", "compute_lps",
                               "prefix_function", "build_lps", "lps", "compute_prefix_function",
                               "partial_match_table", "build_partial_match_table")
    if not builders:
        return
    table = [0, 0, 1, 2, 0, 1, 2, 3, 4]
    # The textbook "next" convention shifts the same table right with a leading -1.
    assert list(builders[0]("ABABCABAB")) in (table, [-1] + table[:-1])


TESTS = [test_prompt_example, test_overlapping_and_edge_matches, test_random_against_naive,
         test_failure_function_if_exposed]
