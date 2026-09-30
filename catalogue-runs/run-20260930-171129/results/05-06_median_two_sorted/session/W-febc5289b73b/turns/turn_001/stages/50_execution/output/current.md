import math

def find_median(nums1, nums2):
    """Return the median of two sorted arrays using O(log(min(m,n))) binary search partition."""
    # Ensure nums1 is the shorter array
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    m, n = len(nums1), len(nums2)
    low, high = 0, m
    while low <= high:
        partitionA = (low + high) // 2
        partitionB = (m + n + 1) // 2 - partitionA

        maxLeftA = -math.inf if partitionA == 0 else nums1[partitionA - 1]
        minRightA = math.inf if partitionA == m else nums1[partitionA]
        maxLeftB = -math.inf if partitionB == 0 else nums2[partitionB - 1]
        minRightB = math.inf if partitionB == n else nums2[partitionB]

        if maxLeftA <= minRightB and maxLeftB <= minRightA:
            if (m + n) % 2 == 1:
                return max(maxLeftA, maxLeftB)
            else:
                return (max(maxLeftA, maxLeftB) + min(minRightA, minRightB)) / 2.0
        elif maxLeftA > minRightB:
            high = partitionA - 1
        else:
            low = partitionA + 1
    raise ValueError("Input arrays are not sorted or are invalid.")

# Test cases
if __name__ == "__main__":
    test_cases = [
        ([1, 3], [2], 2.0),
        ([1, 2], [3, 4], 2.5),
        ([], [1], 1.0),
        ([1, 3, 5, 7, 9], [2, 4, 6, 8, 10], 5.5),
    ]
    for a, b, expected in test_cases:
        result = find_median(a, b)
        print(f"nums1={a}, nums2={b} => median={result} (expected {expected})")
