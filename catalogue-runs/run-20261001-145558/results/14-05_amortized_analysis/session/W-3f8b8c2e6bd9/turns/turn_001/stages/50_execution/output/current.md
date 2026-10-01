**Amortized analysis (accounting method)**

*Setup*
- Initial capacity `C = 1`, array size `n = 0`.
- A **push** that fits in the current capacity costs `1` (the actual write).  
- When a push would exceed capacity, the array is *resized*: the capacity is doubled (`C ← 2C`), all existing `n` elements are copied (`cost = n`), and the new element is written (`cost = 1`).

*Accounting method*
1. **Potential (bank balance)** – we keep a credit of `2` units for every element that is currently stored in the array.  
   Define the potential function
   \[ \Phi = 2\,n \]
   where `n` is the number of elements after the operation.  The initial potential is `0` because `n = 0`.
2. **Amortized cost** of an operation is `actual cost + ΔΦ`.

*Case 1 – ordinary push (no resize)*
- Actual cost = `1`.
- `n` increases by `1`, so `ΔΦ = 2`.
- Amortized cost = `1 + 2 = 3`.
- The extra `2` units are stored as credit for the newly inserted element.

*Case 2 – push that triggers a resize* (let the array contain `n` elements before the push, with capacity `C = n`).
- Actual cost = `n` (copy) `+ 1` (write new element) = `n+1`.
- After the resize the size becomes `n+1` and the capacity becomes `2C = 2n`.  The potential after the operation is `Φ' = 2·(n+1) = 2n+2`.
- Before the operation the potential was `Φ = 2·n = 2n`.
- Change in potential `ΔΦ = Φ' – Φ = (2n+2) – 2n = 2`.
- Amortized cost = `(n+1) + 2 = n+3`.
- The `n` copies are paid for by the `2` credits stored on each of the `n` existing elements (each contributed `2` credits when it was inserted).  The remaining `3` units are the amortized cost for this push.

*Conclusion*
- Every push, whether it causes a resize or not, has amortized cost **at most 3**.
- Therefore the amortized cost is `O(1)` per operation.
- Because the potential function is never negative (`Φ = 2n ≥ 0` for all `n`), the bank balance never becomes negative.
- The exact amortized cost per operation, derived from the accounting equations, is `3` units.

**Summary**
- Assigned amortized cost per push: **3**.
- Amortized cost bound: **O(1)**.
- Bank balance (potential) invariant: `Φ = 2·size ≥ 0`, never negative.
- The analysis follows the accounting method described in the confirmed plan.
