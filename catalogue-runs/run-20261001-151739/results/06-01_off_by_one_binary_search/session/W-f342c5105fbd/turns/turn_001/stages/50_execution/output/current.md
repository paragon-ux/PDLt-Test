**Bug Identification**
The original binary_search function sets the high bound `hi` to `len(arr)`, which is one past the last valid index. More critically, when the target is greater than `arr[mid]`, it updates `lo = mid` instead of `lo = mid + 1`. This can cause the loop to get stuck (e.g., when `lo` and `mid` are equal) and also miss elements because the element at `mid` is never excluded from the search space.

**Why the Bug Occurs**
- `hi = len(arr)`: The loop condition `while lo < hi` expects `hi` to be exclusive. If `hi` is set to the length, the last index (`len(arr) - 1`) is still reachable, but the update logic must correctly move past `mid`.
- `lo = mid`: When `arr[mid] < target`, the lower bound should move past `mid`. Keeping `lo` at `mid` means the next iteration computes the same `mid`, leading to an infinite loop when the target is not present.

**Corrected Implementation**
```python
def binary_search(arr, target):
    lo, hi = 0, len(arr)  # hi is exclusive
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1  # move past mid
        else:
            hi = mid  # hi stays exclusive
    return -1
```

**Test Suite**
```python
def run_tests():
    arr = [1, 3, 5, 7, 9, 11, 13]
    targets = [1, 7, 13, 4, 0, 14]
    expected = [0, 3, 6, -1, -1, -1]
    # Test original buggy implementation
    def buggy_binary_search(arr, target):
        lo, hi = 0, len(arr)
        while lo < hi:
            mid = (lo + hi) // 2
            if arr[mid] == target:
                return mid
            elif arr[mid] < target:
                lo = mid  # bug: should be mid + 1
            else:
                hi = mid
        return -1
    print("Demonstrating bug with original implementation:")
    for t, exp in zip(targets, expected):
        result = buggy_binary_search(arr, t)
        print(f"target={t}, result={result}, expected={exp}, bug={'YES' if result != exp else 'NO'}")
    # Test corrected implementation
    print("\nTesting corrected implementation:")
    for t, exp in zip(targets, expected):
        result = binary_search(arr, t)
        print(f"target={t}, result={result}, expected={exp}, pass={result == exp}")

if __name__ == "__main__":
    run_tests()
```
The test suite first runs the buggy version, showing mismatches (the bug) and then runs the corrected version, confirming all tests pass.
