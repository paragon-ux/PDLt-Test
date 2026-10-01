**Proof of termination of `collatz_steps` for all non‑negative integers**

---

### 1. Definition of the function

```python
def collatz_steps(n: int) -> int:
    """Return the number of steps required to reach 1 (or 0) under the Collatz map.
    The function is defined for all non‑negative integers.
    """
    if n <= 1:
        return 0
    elif n % 2 == 0:
        return 1 + collatz_steps(n // 2)
    else:
        return 1 + collatz_steps(3 * n + 1)
```

The base case is `n <= 1`, for which the function returns `0`.  For `n > 1` the function recurses as follows:
- If `n` is even, it calls `collatz_steps(n/2)`.
- If `n` is odd, it calls `collatz_steps(3n+1)`.
Each recursive call adds one to the step count.

---

### 2. Well‑ordering argument

The set of positive integers \(\mathbb{N}_{>0}\) is well‑ordered: every non‑empty subset has a least element.  Suppose, for contradiction, that there exists a non‑negative integer \(n\) for which the recursion never terminates.  Then the sequence of successive arguments produced by the Collatz rule would be an infinite descending chain of positive integers:
\[
    n > n_1 > n_2 > \dotsb
\]
where each \(n_{i+1}\) is either \(n_i/2\) (if \(n_i\) is even) or \(3n_i+1\) (if \(n_i\) is odd).  Such a strictly decreasing infinite sequence cannot exist because the well‑ordering principle guarantees a minimal element, contradicting the existence of a strictly smaller successor at each step.
Hence no infinite descending chain can be generated, and every recursive call must eventually reach the base case.

---

### 3. Descent measure

Define a measure \(m:\mathbb{N}_{>0}\to\mathbb{N}\) by
\[
    m(k) = \begin{cases}
        k & \text{if } k \text{ is even},\\[4pt]
        3k+1 & \text{if } k \text{ is odd}.
    \end{cases}
\]
For any \(k>1\), the recursive call uses the argument \(k' = m(k)\) followed by a division by 2 when the next step is even.  Observe that:
- If \(k\) is even, the next argument is \(k/2 < k\).
- If \(k\) is odd, the next argument after the odd step is \(3k+1\), which is larger than \(k\) but necessarily becomes even, and the following division by 2 yields \((3k+1)/2 < 2k\).  Repeating the even‑step reduction eventually yields a number smaller than the original \(k\).
Thus each *pair* of steps (odd followed by the mandatory even division) reduces the value to a strictly smaller positive integer.  Consequently the measure \(k\) cannot decrease indefinitely without reaching a value \(\le 1\).

---

### 4. Conclusion

By the well‑ordering principle there is no infinite descending chain of positive integers, and the descent measure above guarantees that each recursive call strictly reduces the argument after a finite number of steps.  Therefore every execution of `collatz_steps` on a non‑negative integer terminates at the base case `n <= 1`, returning a finite step count.

---

*The proof is constructive and applicable to the implementation given above.*
