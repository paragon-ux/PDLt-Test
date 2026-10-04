"""Hidden tests for 05-06: the median of two sorted arrays (binary search over partitions).

The function takes (nums1, nums2), with the prompt's four examples plus random
cases checked against a merged sort.
"""
TEST_SECONDS = 20


def CANDIDATES():
    return functions_named("find_median_sorted_arrays", "findMedianSortedArrays", "median_of_two_sorted",
                           "find_median", "median", "median_two_sorted", "median_sorted_arrays", params=2)


def _expected(a, b):
    merged = sorted(a + b)
    n = len(merged)
    return float(merged[n // 2]) if n % 2 else (merged[n // 2 - 1] + merged[n // 2]) / 2


def test_prompt_examples(f):
    assert approx(f([1, 3], [2]), 2.0)
    assert approx(f([1, 2], [3, 4]), 2.5)
    assert approx(f([], [1]), 1.0)
    assert approx(f([1, 3, 5, 7, 9], [2, 4, 6, 8, 10]), 5.5)


def test_one_side_empty_and_disjoint_ranges(f):
    assert approx(f([5, 6, 7], []), 6.0)
    assert approx(f([1, 2, 3], [10, 11, 12, 13]), 10.0)
    assert approx(f([10, 11], [1, 2, 3]), 3.0)


def test_random(f):
    import random

    rng = random.Random(6)
    for _ in range(300):
        a = sorted(rng.randint(-50, 50) for _ in range(rng.randint(0, 20)))
        b = sorted(rng.randint(-50, 50) for _ in range(rng.randint(0 if a else 1, 20)))
        assert approx(f(list(a), list(b)), _expected(a, b)), (a, b)


TESTS = [test_prompt_examples, test_one_side_empty_and_disjoint_ranges, test_random]
