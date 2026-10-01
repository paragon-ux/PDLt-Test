def find_median_sorted_arrays(nums1, nums2):
    # Ensure nums1 is the smaller array for binary search efficiency
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    m, n = len(nums1), len(nums2)
    total = m + n
    half = (total + 1) // 2

    lo, hi = 0, m
    while lo <= hi:
        i = (lo + hi) // 2  # Partition nums1
        j = half - i        # Partition nums2

        # Edge values handling
        nums1_left = nums1[i - 1] if i > 0 else float('-inf')
        nums1_right = nums1[i] if i < m else float('inf')
        nums2_left = nums2[j - 1] if j > 0 else float('-inf')
        nums2_right = nums2[j] if j < n else float('inf')

        if nums1_left <= nums2_right and nums2_left <= nums1_right:
            # Correct partition found
            if total % 2:
                return max(nums1_left, nums2_left) * 1.0
            else:
                return (max(nums1_left, nums2_left) + min(nums1_right, nums2_right)) / 2.0
        elif nums1_left > nums2_right:
            # Move partition i to left
            hi = i - 1
        else:
            # Move partition i to right
            lo = i + 1

# Test cases
if __name__ == "__main__":
    test_cases = [
        ([1, 3], [2], 2.0),
        ([1, 2], [3, 4], 2.5),
        ([], [1], 1.0),
        ([1, 3, 5, 7, 9], [2, 4, 6, 8, 10], 5.5),
    ]
    for a, b, expected in test_cases:
        result = find_median_sorted_arrays(a, b)
        print(f"nums1={a}, nums2={b} => median={result} (expected {expected})")
        assert abs(result - expected) < 1e-9, f"Failed for {a}, {b}"
