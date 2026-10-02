# Interval insertion and merging implementation with test suite

def insert_and_merge(intervals, new_interval):
    """Insert new_interval into a sorted list of non‑overlapping intervals and merge overlaps.

    Args:
        intervals (list[list[int]]): Sorted list of [start, end] intervals, non‑overlapping.
        new_interval (list[int]): Interval to insert.
    Returns:
        list[list[int]]: New sorted list with intervals merged as needed.
    """
    result = []
    i = 0
    n = len(intervals)
    added = False
    start, end = new_interval
    while i < n:
        cur_start, cur_end = intervals[i]
        if cur_end < start:
            result.append([cur_start, cur_end])
            i += 1
        elif cur_start > end:
            if not added:
                result.append([start, end])
                added = True
            result.append([cur_start, cur_end])
            i += 1
        else:
            # Overlap – merge
            start = min(start, cur_start)
            end = max(end, cur_end)
            i += 1
    if not added:
        result.append([start, end])
    return result

# Test suite
import unittest

class TestInsertAndMerge(unittest.TestCase):
    def test_insert_beginning(self):
        intervals = [[5, 7], [10, 12]]
        new = [1, 3]
        expected = [[1, 3], [5, 7], [10, 12]]
        self.assertEqual(insert_and_merge(intervals, new), expected)

    def test_insert_end(self):
        intervals = [[1, 3], [5, 7]]
        new = [8, 10]
        expected = [[1, 3], [5, 7], [8, 10]]
        self.assertEqual(insert_and_merge(intervals, new), expected)

    def test_insert_middle(self):
        intervals = [[1, 3], [7, 9]]
        new = [4, 6]
        expected = [[1, 3], [4, 6], [7, 9]]
        self.assertEqual(insert_and_merge(intervals, new), expected)

    def test_merge_all(self):
        intervals = [[1, 2], [3, 5], [6, 8]]
        new = [0, 10]
        expected = [[0, 10]]
        self.assertEqual(insert_and_merge(intervals, new), expected)

    def test_overlap_none(self):
        intervals = [[1, 2], [5, 6]]
        new = [3, 4]
        expected = [[1, 2], [3, 4], [5, 6]]
        self.assertEqual(insert_and_merge(intervals, new), expected)

    def test_empty_initial(self):
        intervals = []
        new = [2, 5]
        expected = [[2, 5]]
        self.assertEqual(insert_and_merge(intervals, new), expected)

if __name__ == "__main__":
    unittest.main()
