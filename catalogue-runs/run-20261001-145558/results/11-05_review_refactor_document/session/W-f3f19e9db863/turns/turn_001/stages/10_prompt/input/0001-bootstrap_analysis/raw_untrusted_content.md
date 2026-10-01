Review the following code for bugs and style issues, apply fixes, and update the docstrings to reflect the corrected behavior.

`python
def merge_sorted_lists(list1, list2):
    """Merge two sorted lists into one sorted list.
    Uses in-place modification for efficiency.
    Returns: the merged list
    """
    result = list1
    for item in list2:
        for i in range(len(result)):
            if item < result[i]:
                result.insert(i, item)
                break
        else:
            result.append(item)
    return result

def binary_search_recursive(arr, target, lo=0, hi=None):
    """Find target in sorted array using binary search.
    Returns: index of target, or -1 if not found.
    Time complexity: O(n log n)
    """
    if hi is None:
        hi = len(arr) - 1
    if lo > hi:
        return -1
    mid = (lo + hi) // 2
    if arr[mid] == target:
        return mid
    elif arr[mid] < target:
        return binary_search_recursive(arr, target, mid + 1, hi)
    else:
        return binary_search_recursive(arr, target, lo, mid)

def flatten(nested):
    """Flatten a nested list structure.
    Example: [[1, [2]], 3] -> [1, 2, 3]
    """
    flat = []
    for item in nested:
        if type(item) == list:
            flat.extend(flatten(item))
        else:
            flat.append(item)
    return flat
`

For each function: identify bugs, fix them, correct the docstrings (including the wrong time complexity claim), and write tests proving each bug existed and is now fixed.
