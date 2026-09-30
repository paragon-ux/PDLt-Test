IMPLEMENT a function that, given a sorted list of non-overlapping intervals and a new interval, inserts the new interval into the list and merges any overlapping intervals, RETURNING the resulting sorted list. ENSURE the algorithm runs in O(n) time.
GENERATE tests that cover:
- INSERTION at the beginning of the list.
- INSERTION at the end of the list.
- INSERTION in the middle of the list.
- A new interval that MERGES all existing intervals into a single interval.
- A new interval that OVERLAPS none of the existing intervals.
- THE case where the initial list is empty.
ALL tests must verify that the returned list is sorted and contains non‑overlapping intervals.
