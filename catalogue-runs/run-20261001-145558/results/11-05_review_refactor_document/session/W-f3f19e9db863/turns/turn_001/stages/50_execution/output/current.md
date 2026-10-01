import unittest

def merge_sorted_lists(list1, list2):
    """Merge two sorted lists into one sorted list.
    Time complexity: O(n + m) where n and m are the lengths of the input lists.
    """
    i, j = 0, 0
    result = []
    while i < len(list1) and j < len(list2):
        if list1[i] <= list2[j]:
            result.append(list1[i])
            i += 1
        else:
            result.append(list2[j])
            j += 1
    result.extend(list1[i:])
    result.extend(list2[j:])
    return result

def binary_search_recursive(arr, target, lo=0, hi=None):
    """Find target in sorted array using binary search.
    Returns: index of target, or -1 if not found.
    Time complexity: O(log n)
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
    """Flatten a nested list structure.
    Example: [[1, [2]], 3] -> [1, 2, 3]
    Time complexity: O(N) where N is the total number of elements.
    """
    flat = []
    for item in nested:
        if isinstance(item, list):
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat

class TestBuggyBehavior(unittest.TestCase):
    def test_merge_sorted_lists_bug(self):
        # Original buggy behavior modifies the first list in-place and fails on empty first list
        list1 = []
        list2 = [1, 2, 3]
        merged = merge_sorted_lists(list1, list2)
        self.assertEqual(merged, [1, 2, 3])

    def test_binary_search_recursive_bug(self):
        # Original buggy version could recurse infinitely for target not present at edges
        arr = [1, 2, 3, 4, 5]
        self.assertEqual(binary_search_recursive(arr, 6), -1)

    def test_flatten_bug(self):
        # Original buggy version would treat non-list iterables incorrectly (not an issue here)
        nested = []
        self.assertEqual(flatten(nested), [])

class TestCorrectedBehavior(unittest.TestCase):
    def test_merge_sorted_lists(self):
        self.assertEqual(merge_sorted_lists([1,3,5], [2,4,6]), [1,2,3,4,5,6])
        self.assertEqual(merge_sorted_lists([], [1,2]), [1,2])
        self.assertEqual(merge_sorted_lists([1,2], []), [1,2])
        self.assertEqual(merge_sorted_lists([], []), [])

    def test_binary_search_recursive(self):
        arr = [1,2,3,4,5]
        for i, val in enumerate(arr):
            self.assertEqual(binary_search_recursive(arr, val), i)
        self.assertEqual(binary_search_recursive(arr, 0), -1)
        self.assertEqual(binary_search_recursive(arr, 6), -1)

    def test_flatten(self):
        self.assertEqual(flatten([1, [2, [3, 4], 5], 6]), [1,2,3,4,5,6])
        self.assertEqual(flatten([]), [])
        self.assertEqual(flatten([[[[]]]]), [])
        self.assertEqual(flatten([1,2,3]), [1,2,3])

if __name__ == "__main__":
    unittest.main()
