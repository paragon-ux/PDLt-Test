The loop invariant for the original `array_sum` function is:

    **Invariant**: At the start of each iteration of the while loop, `total` equals the sum of the elements of `arr` with indices from `0` up to but not including `i`; formally, `total = Σ_{k=0}^{i-1} arr[k]`.

**Proof of initialization (before the first iteration)**
- Before the loop starts we have `i = 0` and `total = 0`.
- The sum of zero elements of `arr` (i.e., the empty prefix) is `0`.
- Hence `total = 0 = Σ_{k=0}^{-1} arr[k]`, so the invariant holds.

**Proof of maintenance (preservation across an iteration)**
- Assume the invariant holds at the beginning of an iteration: `total = Σ_{k=0}^{i-1} arr[k]` and `i < len(arr)`.
- The loop body executes `total = total + arr[i]` resulting in `total' = Σ_{k=0}^{i-1} arr[k] + arr[i] = Σ_{k=0}^{i} arr[k]`.
- Then `i = i + 1` gives `i' = i + 1`.
- At the start of the next iteration we have `total' = Σ_{k=0}^{i'-1} arr[k]`, which is exactly the invariant for the updated `i'`.
- Therefore the invariant is preserved.

**Proof of termination (post‑condition)**
- The loop terminates when `i >= len(arr)`. At that point `i = len(arr)` because `i` is increased by exactly one each iteration and never skips values.
- By the invariant we have `total = Σ_{k=0}^{i-1} arr[k] = Σ_{k=0}^{len(arr)-1} arr[k]`, which is the sum of all elements of `arr`.
- The function returns `total`, thus returning the correct sum.

---

**Rewritten function with explicit assertions**
```python
def array_sum(arr):
    total = 0
    i = 0
    # Invariant: total == sum(arr[0:i])
    while i < len(arr):
        # Assert invariant holds at start of each iteration
        assert total == sum(arr[:i]), f"Invariant violation before iteration {i}: total={total}, expected={sum(arr[:i])}"
        total = total + arr[i]
        i = i + 1
    # After the loop, i == len(arr) and invariant gives the correct result
    assert total == sum(arr), "Invariant violation after loop termination"
    return total
```
