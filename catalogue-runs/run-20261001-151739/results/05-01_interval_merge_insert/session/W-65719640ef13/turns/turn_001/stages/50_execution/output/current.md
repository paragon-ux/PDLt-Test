import unittest
from typing import List

def merge_intervals(intervals: List[List[int]], new_interval: List[int]) -> List[List[int]]:
    """Insert `new_interval` into a sorted list of non‑overlapping `intervals` and merge any overlaps.
    The algorithm runs in O(n) time.
    """
    result = []
    i = 0
    n = len(intervals)
    # Add all intervals that end before the new interval starts
    while i < n and intervals[i][1] < new_interval[0]:
        result.append(intervals[i])
        i += 1
    # Merge overlapping intervals
    start, end = new_interval
    while i < n and intervals[i][0] <= end:
        start = min(start, intervals[i][0])
        end = max(end, intervals[i][1])
        i += 1
    result.append([start, end])
    # Append the remaining intervals
    while i < n:
        result.append(intervals[i])
        i += 1
    return result

class TestMergeIntervals(unittest.TestCase):
    def test_insert_beginning(self):
        intervals = [[5, 7], [10, 12]]
        new_interval = [1, 3]
        expected = [[1, 3], [5, 7], [10, 12]]
        self.assertEqual(merge_intervals(intervals, new_interval), expected)

    def test_insert_end(self):
        intervals = [[1, 3], [5, 7]]
        new_interval = [8, 10]
        expected = [[1, 3], [5, 7], [8, 10]]
        self.assertEqual(merge_intervals(intervals, new_interval), expected)

    def test_insert_middle(self):
        intervals = [[1, 3], [6, 9], [12, 15]]
        new_interval = [4, 5]
        expected = [[1, 3], [4, 5], [6, 9], [12, 15]]
        self.assertEqual(merge_intervals(intervals, new_interval), expected)

    def test_merge_all(self):
        intervals = [[1, 3], [4, 6], [7, 9]]
        new_interval = [2, 8]
        expected = [[1, 9]]
        self.assertEqual(merge_intervals(intervals, new_interval), expected)

    def test_no_overlap(self):
        intervals = [[1, 2], [5, 6]]
        new_interval = [3, 4]
        expected = [[1, 2], [3, 4], [5, 6]]
        self.assertEqual(merge_intervals(intervals, new_interval), expected)

    def test_empty_initial(self):
        intervals = []
        new_interval = [2, 5]
        expected = [[2, 5]]
        self.assertEqual(merge_intervals(intervals, new_interval), expected)

    def test_example_case(self):
        intervals = [[1,3], [6,9], [12,15], [18,20]]
        new_interval = [5,13]
        expected = [[1,3], [5,15], [18,20]]
        self.assertEqual(merge_intervals(intervals, new_interval), expected)

if __name__ == "__main__":
    unittest.main()
