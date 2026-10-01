TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Find the median of two sorted arrays nums1 and nums2 in O(log(min(m, n))) time. Implement the binary search approach that partitions both arrays simultaneously. Provide the median for the test cases: nums1 = [1, 3], nums2 = [2] → median = 2.0; nums1 = [1, 2], nums2 = [3, 4] → median = 2.5; nums1 = [], nums2 = [1] → median = 1.0; nums1 = [1, 3, 5, 7, 9], nums2 = [2, 4, 6, 8, 10] → median = 5.5.
APPROACH/RISK NOTES:
Apply a binary search partition method that runs in O(log(min(m, n))) time, partitioning both arrays simultaneously to locate the correct split point for median calculation.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- nums1
- nums2
- median
- O(log(min(m, n)))
