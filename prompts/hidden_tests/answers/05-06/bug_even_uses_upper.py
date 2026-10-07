# Wrong: for an even total it returns the upper middle element, not the average.
def find_median_sorted_arrays(nums1, nums2):
    merged = sorted(nums1 + nums2)
    return float(merged[len(merged) // 2])
