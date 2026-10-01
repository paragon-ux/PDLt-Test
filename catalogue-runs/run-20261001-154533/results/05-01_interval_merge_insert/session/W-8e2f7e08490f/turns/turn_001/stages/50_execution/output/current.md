import unittest

def insert_and_merge(intervals, new_interval):
    # Find position to insert to keep sorted order based on start
    i = 0
    while i < len(intervals) and intervals[i][0] < new_interval[0]:
        i += 1
    intervals = intervals[:i] + [new_interval] + intervals[i:]
    # Merge overlapping intervals
    merged = []
    for interval in intervals:
        if not merged or merged[-1][1] < interval[0]:
            merged.append(interval)
        else:
            merged[-1][1] = max(merged[-1][1], interval[1])
    return merged

class TestInsertAndMerge(unittest.TestCase):
    def test_insert_beginning(self):
        intervals = [[5,7], [10,12]]
        new_interval = [1,3]
        expected = [[1,3], [5,7], [10,12]]
        self.assertEqual(insert_and_merge(intervals, new_interval), expected)

    def test_insert_end(self):
        intervals = [[1,2], [3,5]]
        new_interval = [6,8]
        expected = [[1,2], [3,5], [6,8]]
        self.assertEqual(insert_and_merge(intervals, new_interval), expected)

    def test_insert_middle(self):
        intervals = [[1,2], [5,6]]
        new_interval = [3,4]
        expected = [[1,2], [3,4], [5,6]]
        self.assertEqual(insert_and_merge(intervals, new_interval), expected)

    def test_merge_all(self):
        intervals = [[1,2], [3,4], [5,6]]
        new_interval = [0,10]
        expected = [[0,10]]
        self.assertEqual(insert_and_merge(intervals, new_interval), expected)

    def test_no_overlap(self):
        intervals = [[1,2], [5,6]]
        new_interval = [3,4]
        expected = [[1,2], [3,4], [5,6]]
        self.assertEqual(insert_and_merge(intervals, new_interval), expected)

    def test_empty_initial(self):
        intervals = []
        new_interval = [2,5]
        expected = [[2,5]]
        self.assertEqual(insert_and_merge(intervals, new_interval), expected)

if __name__ == '__main__':
    unittest.main()
