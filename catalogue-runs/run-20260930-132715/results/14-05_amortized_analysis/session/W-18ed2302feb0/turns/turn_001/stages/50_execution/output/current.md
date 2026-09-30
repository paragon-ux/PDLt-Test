Amortized analysis using the accounting (banker’s) method

**Dynamic array model**
- Initial capacity = 1.
- Each push that does not trigger a resize costs 1 unit.
- When a push would exceed the current capacity `C`, the array is resized to capacity `2C`. The resize copies all `C` existing elements (cost `C`) and then stores the new element (the push cost 1).

**Banker’s credit assignment**
Assign an amortized cost `a` to every push operation and deposit part of it as credit on each element that is already in the array. The credit on an element will be used later to pay for the copy of that element when a resize occurs.

Let the credit deposited on each element after a push be `c`. When the array of size `n` (and capacity `C`) is about to be resized, the total credit stored on the `n` existing elements equals `n·c`. This credit must cover the copy cost `n` of the resize.

Hence we need `n·c ≥ n` for every possible `n`. The smallest `c` satisfying this for all `n≥1` is `c = 1`.

Therefore we deposit **1 credit unit on each element at the moment it is inserted**. The amortized cost per push is then:

```
amortized_cost = actual_push_cost (1) + deposited credit (1) = 2 units.
```

**Verification of the credit invariant**
We prove by induction that the credit balance never becomes negative.

*Base case*: Before any operation the array is empty, capacity 1, and credit balance = 0.

*Inductive step*: Assume after `k` pushes the balance is non‑negative. Consider the `(k+1)`‑st push.
- If the push does **not** cause a resize, the actual cost is 1 and we add 1 credit (deposit) → net balance change = 0, staying non‑negative.
- If the push **does** cause a resize, let the current capacity be `C`. The actual cost is `1` (push) + `C` (copying `C` elements). We have `C` elements each carrying 1 credit from previous pushes, giving exactly `C` credit to pay the copy cost. Additionally we deposit 1 credit for the new element. Net balance change = `+1` (new deposit) – `0` (copies fully paid) = `+1`, again non‑negative.
Thus the invariant holds for any sequence length.

**Result**
- The amortized cost per push is **2 units**, which is `O(1)`.
- The credit invariant guarantees the prepaid balance never drops below zero.

---

Result IR follows the required schema.
