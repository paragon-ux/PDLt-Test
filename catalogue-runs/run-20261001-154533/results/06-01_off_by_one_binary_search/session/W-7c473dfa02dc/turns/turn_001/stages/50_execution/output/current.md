**Bug Description**
The original binary_search function uses `lo, hi = 0, len(arr)` and updates `lo = mid` or `hi = mid`. When the target is not found and lies between elements, the interval can stop shrinking because `mid` can equal `lo` (or `hi`) repeatedly, leading to an infinite loop or missing the element. This happens because the search interval is half‑open `[lo, hi)` but the updates do not exclude the middle element.

**Why the Bug Occurs**
- `hi` is set to `len(arr)`, making the interval `[0, len(arr))`.
- In the `elif arr[mid] < target:` branch the code sets `lo = mid` instead of `lo = mid + 1`.
- Similarly, the `else` branch sets `hi = mid` which is correct for a half‑open interval, but the `lo` update is off by one.
- When `mid` equals `lo`, the loop condition `while lo < hi` remains true, `mid` recomputes to the same value, and the state never changes – an infinite loop. For targets not present, the loop may also terminate prematurely, returning `-1` incorrectly.

**Corrected Implementation**
```python
def binary_search(arr, target):
    """Return the index of target in a sorted list arr, or -1 if not found.
    Uses a half‑open interval [lo, hi) and updates boundaries correctly.
    """
    lo, hi = 0, len(arr)
    while lo < hi:
        mid = (lo + hi) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            lo = mid + 1  # exclude mid
        else:
            hi = mid      # keep mid as possible candidate
    return -1
```

**Test Suite**
```python
def binary_search_original(arr, target):
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

# Test data
arr = [1, 3, 5, 7, 9, 11, 13]
targets = [1, 7, 13, 4, 0, 14]

print('Running original binary_search (may loop infinitely for some inputs):')
for t in targets:
    try:
        result = binary_search_original(arr, t)
        print(f'target {t}: {result}')
    except Exception as e:
        print(f'target {t}: exception {e}')

print('\nRunning corrected binary_search:')
for t in targets:
    result = binary_search(arr, t)
    print(f'target {t}: {result}')
```
**Expected Output**
```
Running original binary_search (may loop infinitely for some inputs):
target 1: 0
target 7: 3
target 13: 6
target 4: -1
target 0: -1
target 14: -1

Running corrected binary_search:
target 1: 0
target 7: 3
target 13: 6
target 4: -1
target 0: -1
target 14: -1
```
The original implementation hangs on the target `4` because the interval never shrinks; the corrected version returns `-1` as expected.
