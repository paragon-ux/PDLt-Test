```python
def binary_search(arr, target):
    lo, hi = 0, len(arr) - 1  # use inclusive hi index
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

# Test suite demonstrating the bug and the fix
if __name__ == "__main__":
    arr = [1, 3, 5, 7, 9, 11, 13]
    targets = [1, 7, 13, 4, 0, 14]
    print("Original buggy binary_search results:")
    def buggy_binary_search(arr, target):
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                lo = mid
            else:
                hi = mid
        return -1
    for t in targets:
        result = buggy_binary_search(arr, t)
        print(f"target {t}: index {result}")
    print("\nCorrected binary_search results:")
    for t in targets:
        result = binary_search(arr, t)
        print(f"target {t}: index {result}")
```
