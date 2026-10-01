PARSE the sorted list of intervals and the new interval
LOCATE the insertion index to maintain sorted order
INSERT the new interval at the located position
SCAN the list sequentially to MERGE any overlapping intervals, ensuring O(n) time complexity
RETURN the merged list of intervals
DESIGN a unit test where the new interval is inserted at the beginning of a non-empty list
DESIGN a unit test where the new interval is inserted at the end of a non-empty list
DESIGN a unit test where the new interval is inserted in the middle of a non-empty list
DESIGN a unit test where the new interval merges all existing intervals into a single interval
DESIGN a unit test where the new interval overlaps none of the existing intervals
DESIGN a unit test where the initial list of intervals is empty
