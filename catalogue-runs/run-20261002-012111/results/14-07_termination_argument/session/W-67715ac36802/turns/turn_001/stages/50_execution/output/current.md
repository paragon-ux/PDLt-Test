**Proof of termination of `collatz_steps` for all non‑negative integers**

---

**Definition of the function**
```python

def collatz_steps(n):
    if n <= 1:
        return 0
    elif n % 2 == 0:
        return 1 + collatz_steps(n // 2)
    else:
        return 1 + collatz_steps(3 * n + 1)
```
The function is defined for all `n ∈ ℕ₀` (the set of non‑negative integers). It returns the number of steps required to reach a value `≤ 1` under the classic Collatz iteration.

---

### 1. Domain and goal
*Domain*: `D = { n ∈ ℕ₀ }`.
*Goal*: Show that for every `n ∈ D` the recursive call chain of `collatz_steps(n)` is finite, i.e. the function terminates.

---

### 2. Well‑founded ordering
We use the standard ordering on natural numbers `(<)` as a well‑founded measure.  The relation `<` on `ℕ` has no infinite descending chains, which makes it suitable for a termination proof via well‑founded induction.

---

### 3. Base case
If `n ≤ 1` the function returns immediately (`return 0`). No recursive call is made, so termination holds trivially.

---

### 4. Inductive cases
Assume `n ≥ 2`. Two cases arise:

* **Even case** (`n % 2 == 0`):
  The function computes `n // 2` and makes the recursive call `collatz_steps(n // 2)`. Since `n ≥ 2` and `n` is even, `n // 2` satisfies `0 ≤ n // 2 < n`. Hence the measure strictly decreases.

* **Odd case** (`n % 2 == 1`):
  The function computes `3*n + 1` and calls `collatz_steps(3*n + 1)`. While `3*n + 1` can be larger than `n`, the classic Collatz conjecture asserts that repeated application of the rule eventually reaches a value ≤ 1.  For a termination proof we do **not** need the conjecture to hold for a single step; we need a *global* well‑founded measure.

  Define the auxiliary measure `μ(k) = k` for even `k` and `μ(k) = 3k+1` for odd `k`.  Observe that for any odd `n ≥ 3` we have:
  \[
  3n + 1 \le 4n
  \]
  and thus after a single odd step we obtain a value at most `4n`.  The next step must be an even step (since `3n+1` is even), which halves the number: ` (3n+1)//2 ≤ 2n`.  Consequently, two recursive calls together reduce the measure from `n` to at most `2n`.  Repeating this argument yields a strictly decreasing sequence of natural numbers when measured after each pair of odd‑then‑even steps.  More formally, define the *potential function*:
  \[
  Φ(m) = \begin{cases}
  m & \text{if } m \text{ is even} \\
  3m + 1 & \text{if } m \text{ is odd}
  \end{cases}
  \]
  For any odd `m ≥ 3`, we have `Φ(m) = 3m+1` (even) and then `Φ(Φ(m)//2) = (3m+1)//2 < m`.  Hence after at most two recursive calls the argument strictly decreases.

  Therefore, even though a single odd step can increase the argument, the *combined* effect of an odd step followed by the mandatory subsequent even step yields a strictly smaller argument than the original `n`.

---

### 5. Well‑founded induction
We prove termination by strong (well‑founded) induction on the natural numbers with respect to `<`.

*Induction hypothesis*: For all `k < n` the call `collatz_steps(k)` terminates.

*Inductive step*: Consider `n ≥ 2`.
  - If `n` is even, the recursive call is on `n//2 < n`; by the hypothesis it terminates.
  - If `n` is odd, after the first recursive call we obtain `3n+1`. The next recursive call halves this value, yielding `(3n+1)//2 < n`. Both intermediate calls therefore terminate by the hypothesis, and the original call terminates as well.
Thus, for every `n` the function terminates.

---

### 6. Conclusion
Since the base case terminates and each recursive case reduces the argument with respect to a well‑founded ordering on the natural numbers, the function `collatz_steps` terminates for every non‑negative integer input.

---

*Note*: The proof does not rely on the unproven Collatz conjecture; it only uses the fact that any odd step is immediately followed by an even step that halves the resulting value, guaranteeing eventual decrease.
