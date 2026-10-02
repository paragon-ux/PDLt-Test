TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Write code that, given a sorted list of non-overlapping intervals and a new interval, inserts the new interval into the list, merges any overlapping intervals, and returns the resulting sorted list. Provide a test suite that covers insertion at the beginning, at the end, in the middle, a new interval that merges all existing intervals, a new interval that overlaps none, and the case where the initial list of intervals is empty.
APPROACH/RISK NOTES:
Use a linear-time algorithm (O(n)) that scans the intervals once, inserting the new interval at its correct position and merging overlapping intervals in a single pass.
