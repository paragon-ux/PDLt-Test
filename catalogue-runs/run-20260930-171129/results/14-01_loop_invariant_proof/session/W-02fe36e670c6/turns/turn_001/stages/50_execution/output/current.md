The loop invariant for the while‑loop in `array_sum` is:

    At the start of each iteration, `total` equals the sum of the first `i` elements of `arr` (i.e., total == sum(arr[0:i])) and 0 ≤ i ≤ len(arr).

**Proof of initialization**
- Before the loop starts we have `total = 0` and `i = 0`.
- The sum of the first 0 elements of `arr` is also 0, so the invariant holds: `total == sum(arr[0:0])` and `0 ≤ 0 ≤ len(arr)`.

**Proof of maintenance**
Assume the invariant holds at the beginning of an iteration where `i < len(arr)`:
- By the invariant, `total == sum(arr[0:i])`.
- The body executes `total = total + arr[i]` and then `i = i + 1`.
- After these statements, `total == sum(arr[0:i])` now includes the element `arr[i‑1]`, and `i` has been incremented by one.
- Hence the invariant is restored for the next iteration.

**Proof of termination**
- The loop terminates when `i >= len(arr)`. At that point, by the invariant, `total == sum(arr[0:i])` and `i == len(arr)`.
- Therefore `total == sum(arr[0:len(arr)])`, which is exactly the sum of the entire array, and the function returns the correct result.

**Modified function with assertions**
```python
def array_sum(arr):
    total = 0
    i = 0
    # Invariant: total == sum(arr[0:i]) and 0 <= i <= len(arr)
    while i < len(arr):
        # Assert invariant holds at the start of each iteration
        assert total == sum(arr[0:i]), f"Invariant violation: total={total}, i={i}, expected={sum(arr[0:i])}"
        assert 0 <= i <= len(arr), f"Index out of bounds: i={i}, len(arr)={len(arr)}"
        total = total + arr[i]
        i = i + 1
    # Final invariant check after loop (optional)
    assert total == sum(arr), "Final invariant violation"
    return total
```
