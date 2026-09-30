# interval_merge.py

def insert_interval(intervals, new_interval):
    """Insert ``new_interval`` into a sorted list of non‑overlapping ``intervals``
    and merge any overlaps. Returns a new list preserving sort order.
    Runs in O(n) time where n = len(intervals).
    """
    result = []
    i = 0
    n = len(intervals)
    # Add all intervals before the new interval
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
    # Append the rest
    while i < n:
        result.append(intervals[i])
        i += 1
    return result

# test_interval_merge.py
import unittest

class TestInsertInterval(unittest.TestCase):
    def test_insert_beginning(self):
        intervals = [[5,7], [10,12]]
        new = [1,3]
        expected = [[1,3], [5,7], [10,12]]
        self.assertEqual(insert_interval(intervals, new), expected)

    def test_insert_end(self):
        intervals = [[1,2], [4,5]]
        new = [6,8]
        expected = [[1,2], [4,5], [6,8]]
        self.assertEqual(insert_interval(intervals, new), expected)

    def test_insert_middle_no_merge(self):
        intervals = [[1,2], [5,6]]
        new = [3,4]
        expected = [[1,2], [3,4], [5,6]]
        self.assertEqual(insert_interval(intervals, new), expected)

    def test_merge_all(self):
        intervals = [[1,3], [4,6], [7,9]]
        new = [2,8]
        expected = [[1,9]]
        self.assertEqual(insert_interval(intervals, new), expected)

    def test_no_overlap(self):
        intervals = [[1,2], [5,6]]
        new = [3,4]
        expected = [[1,2], [3,4], [5,6]]
        self.assertEqual(insert_interval(intervals, new), expected)

    def test_empty_initial(self):
        intervals = []
        new = [2,5]
        expected = [[2,5]]
        self.assertEqual(insert_interval(intervals, new), expected)

    def test_sorted_and_non_overlapping(self):
        # Verify output is sorted and non‑overlapping for a random case
        intervals = [[1,3], [6,9], [12,15], [18,20]]
        new = [5,13]
        result = insert_interval(intervals, new)
        # Check sorted
        self.assertTrue(all(result[i][0] <= result[i][1] for i in range(len(result))))
        self.assertTrue(all(result[i][1] < result[i+1][0] for i in range(len(result)-1)))
        self.assertEqual(result, [[1,3], [5,15], [18,20]])

if __name__ == "__main__":
    unittest.main()
