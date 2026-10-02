**Amortized analysis (banker’s method)**

We model a dynamic array that starts with capacity 1 and doubles whenever a push would exceed the current capacity.  Each push that does **not** trigger a resize costs a single actual operation (cost = 1).  When a resize occurs, the actual cost consists of:
- copying all *n* existing elements (cost = n),
- writing the new element (cost = 1).
Thus the total actual cost of a push that causes a resize when the array size just before the push is *n* (and the capacity is *n*) is *n + 1*.

---
### Bank account scheme
Let us assign an **amortized cost** *c* to every push operation (including those that cause a resize).  The bank balance after each operation is the sum of the amortized costs charged so far minus the sum of the actual costs incurred so far.
We require that the bank balance never becomes negative.

Consider a sequence of pushes that cause a resize at array sizes 1, 2, 4, 8, …, 2^k.  Between two successive resizes there are exactly *2^i* non‑resize pushes (when the capacity is *2^i*).  The total actual cost of that block of pushes is:
- *2^i* pushes each costing 1 → cost *2^i*
- one resize push costing *2^i + 1* → cost *2^i + 1*
Overall cost for the block = *2·2^i + 1*.
If we charge an amortized cost *c* for each of the *2^i + 1* pushes in the block, the total amortized charge is *c·(2^i + 1)*.
We need
```
c·(2^i + 1)  ≥  2·2^i + 1   for every i ≥ 0.
```
Dividing by *2^i* gives
```
c·(1 + 1/2^i)  ≥  2 + 1/2^i.
```
The worst case (largest right‑hand side) occurs for *i = 0*, where *1/2^i = 1*.  Hence the inequality reduces to
```
c·2  ≥  3  →  c ≥ 3/2.
```
Therefore an amortized charge of **c = 3/2** (1.5) per push is sufficient to keep the bank balance non‑negative for the entire sequence.

---
### Proof of O(1) amortized cost
The derived amortized cost *c = 3/2* is a constant independent of the number of pushes.  Consequently the amortized cost per operation is **O(1)**.

---
### Bank balance never negative
With *c = 3/2*, after each block of pushes the net change in bank balance is:
```
Δ = c·(2^i + 1) – (2·2^i + 1) = (3/2)(2^i + 1) – (2·2^i + 1)
   = (3·2^{i-1} + 3/2) – (2·2^i + 1)
   = (3·2^{i-1} + 3/2) – (2·2^{i-1}·2 + 1)
   = (3·2^{i-1} + 3/2) – (4·2^{i-1} + 1)
   = -2^{i-1} + 1/2 ≥ 0   (since i ≥ 0).
```
Thus the balance never drops below zero at the end of any block, and because the balance only changes linearly within a block, it cannot become negative at intermediate points either.

---
### Exact amortized cost per operation
The minimal constant amortized charge that guarantees a non‑negative bank balance is **c = 3/2**.  Hence the exact amortized cost per push operation for this dynamic array (using the accounting method) is **1.5 units**.
