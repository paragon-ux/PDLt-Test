def find_median_sorted_arrays(nums1, nums2):
    # Ensure nums1 is the smaller array
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    x, y = len(nums1), len(nums2)
    low, high = 0, x
    while low <= high:
        partition_x = (low + high) // 2
        partition_y = (x + y + 1) // 2 - partition_x
        max_left_x = float('-inf') if partition_x == 0 else nums1[partition_x - 1]
        min_right_x = float('inf') if partition_x == x else nums1[partition_x]
        max_left_y = float('-inf') if partition_y == 0 else nums2[partition_y - 1]
        min_right_y = float('inf') if partition_y == y else nums2[partition_y]
        if max_left_x <= min_right_y and max_left_y <= min_right_x:
            if (x + y) % 2 == 1:
                return float(max(max_left_x, max_left_y))
            else:
                return (max(max_left_x, max_left_y) + min(min_right_x, min_right_y)) / 2.0
        elif max_left_x > min_right_y:
            high = partition_x - 1
        else:
            low = partition_x + 1
    raise ValueError("Input arrays are not sorted correctly")

# Test cases
if __name__ == "__main__":
    test_cases = [
        ([1, 3], [2], 2.0),
        ([1, 2], [3, 4], 2.5),
        ([], [1], 1.0),
        ([1, 3, 5, 7, 9], [2, 4, 6, 8, 10], 5.5),
    ]
    for nums1, nums2, expected in test_cases:
        result = find_median_sorted_arrays(nums1, nums2)
        assert abs(result - expected) < 1e-9, f"Failed for {nums1}, {nums2}: got {result}, expected {expected}"
    print("All test cases passed.")
