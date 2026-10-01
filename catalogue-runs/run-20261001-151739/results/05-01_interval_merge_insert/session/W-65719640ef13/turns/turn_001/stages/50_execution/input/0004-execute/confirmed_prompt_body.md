WRITE a function named merge_intervals that ACCEPTS a sorted list of non-overlapping intervals called intervals and a new interval called new_interval.
INSERT new_interval into intervals and MERGE any overlapping intervals to produce a resulting sorted list.
ENSURE the implementation runs in O(n) time.
OUTPUT the resulting sorted list.
WRITE unit tests covering the following scenarios:
- INSERTION at the beginning of intervals.
- INSERTION at the end of intervals.
- INSERTION in the middle of intervals.
- A new interval that MERGES all existing intervals.
- A new interval that OVERLAPS none of the existing intervals.
- An empty initial intervals list.
USE the example input intervals = [[1,3], [6,9], [12,15], [18,20]] and new_interval = [5,13]; EXPECT output [[1,3], [5,15], [18,20]].
