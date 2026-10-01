READ the two sorted arrays nums1 and nums2
PARTITION the arrays using a binary search on the shorter array to find the correct split where left side elements are less than or equal to right side elements
COMPUTE the median from the maximum of the left partition and the minimum of the right partition, handling both even and odd combined lengths
OUTPUT the median as a floating‑point number
PROVIDE the following test cases with expected results:
  - nums1 = [1, 3], nums2 = [2] -> median = 2.0
  - nums1 = [1, 2], nums2 = [3, 4] -> median = 2.5
  - nums1 = [], nums2 = [1] -> median = 1.0
  - nums1 = [1, 3, 5, 7, 9], nums2 = [2, 4, 6, 8, 10] -> median = 5.5
