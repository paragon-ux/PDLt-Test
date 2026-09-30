DEFINE a function that takes a sorted list of non‑overlapping intervals and a new interval
MERGE the new interval into the list while preserving order and non‑overlap in O(n) time
RETURN the resulting sorted list of intervals
CREATE a test suite containing distinct test cases for:
INSERTION at the beginning of the list
INSERTION at the end of the list
INSERTION in the middle of the list
A new interval that merges all existing intervals into a single interval
A new interval that overlaps none of the existing intervals
The case where the initial list is empty
FOR each test case, VERIFY that the function output is sorted and contains no overlapping intervals
