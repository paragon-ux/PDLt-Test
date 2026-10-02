def merge_sorted_lists(list1, list2):
    """Merge two sorted lists into a new sorted list.
    The function returns a *new* list containing all elements from ``list1`` and ``list2``
    in non‑decreasing order. It does **not** modify the input lists.
    """
    i, j = 0, 0
    merged = []
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            merged.append(list1[i])
            i += 1
        else:
            merged.append(list2[j])
            j += 1
    # Append any remaining elements
    merged.extend(list1[i:])
    merged.extend(list2[j:])
    return merged


def binary_search_recursive(arr, target, lo=0, hi=None):
    """Recursively perform binary search on a sorted list.
    Returns the index of ``target`` if found, otherwise ``-1``.
    Time complexity: O(log n).
    """
    if hi is None:
        hi = len(arr) - 1
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, hi)
    else:
        return binary_search_recursive(arr, target, lo, mid - 1)


def flatten(nested):
    """Recursively flatten a nested list of arbitrary depth.
    Example::
        flatten([[1, [2]], 3]) -> [1, 2, 3]
    """
    flat = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat


# Unit tests
import unittest

class TestFunctions(unittest.TestCase):
    # Tests for merge_sorted_lists
    def test_merge_sorted_lists_original_bug(self):
        # Original bug: in‑place modification caused duplicate insertions
        a = [1, 3, 5]
        b = [2, 4, 6]
        result = merge_sorted_lists(a, b)
        self.assertEqual(result, [1, 2, 3, 4, 5, 6])
        # Ensure original lists unchanged
        self.assertEqual(a, [1, 3, 5])
        self.assertEqual(b, [2, 4, 6])

    # Tests for binary_search_recursive
    def test_binary_search_recursive_original_bug(self):
        arr = [1, 2, 3, 4, 5]
        # Original time‑complexity claim was wrong; functionality is correct now
        self.assertEqual(binary_search_recursive(arr, 3), 2)
        self.assertEqual(binary_search_recursive(arr, 6), -1)

    # Tests for flatten
    def test_flatten_original_bug(self):
        nested = [[1, [2, [3]]], 4]
        self.assertEqual(flatten(nested), [1, 2, 3, 4])
        # Ensure non‑list elements are handled
        self.assertEqual(flatten([1, 2, 3]), [1, 2, 3])

if __name__ == "__main__":
    unittest.main()
