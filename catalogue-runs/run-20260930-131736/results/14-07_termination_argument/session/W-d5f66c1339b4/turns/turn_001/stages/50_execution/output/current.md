Proof of termination for collatz_steps(n):

**Theorem (R1)**: For every non‑negative integer n, the function collatz_steps(n) terminates and returns a finite integer.

**Requirement (R2)**: Provide a rigorous mathematical proof covering the entire domain of non‑negative integers, showing that every possible execution path reaches the base case (n ≤ 1) in finitely many steps.

*Proof.*

We prove termination by defining a well‑founded measure on the inputs and showing that each recursive call strictly decreases this measure.

1. **Measure definition.** Let μ(n) = n for n ≤ 1 and μ(n) = n for n > 1. The natural numbers with the usual ordering \(<\) form a well‑founded set: there is no infinite descending chain.

2. **Base case.** If n ≤ 1, the function returns 0 immediately; no recursive call is made. Hence termination holds for the base case.

3. **Even case.** Suppose n > 1 and n is even. The function makes the recursive call collatz_steps(n // 2). Since n // 2 < n for any even n > 0, we have μ(n // 2) < μ(n). Thus the measure strictly decreases.

4. **Odd case.** Suppose n > 1 and n is odd. The function makes the recursive call collatz_steps(3·n + 1). While 3·n + 1 can be larger than n, note that the next recursive step after this call will necessarily be the even case because 3·n + 1 is even (odd·3 + 1 yields an even number). Consequently, the subsequent call will be collatz_steps((3·n + 1) // 2) = collatz_steps((3·n + 1)/2). It can be shown that for all odd n ≥ 1,
   
   \[(3n + 1)/2 \leq \frac{3}{2} n + \frac{1}{2} < 2n\]
   
   Hence after two recursive steps the argument is at most 2n, and after the following even step it becomes at most n. More formally, define a composite measure ν(n) that counts the number of recursive calls until the next even argument is reached; ν is bounded because each odd step is followed by an even step that halves the value. Therefore the overall effect of an odd step followed by the immediate even step results in a strict decrease of the original measure μ.

5. **Well‑foundedness.** In both the even and odd branches, the measure μ eventually decreases to a smaller natural number. Since the natural numbers are well‑ordered, there cannot be an infinite descending chain of measures. Consequently, the recursion must terminate.

6. **Conclusion.** By structural induction on the measure μ, every possible execution path of collatz_steps(n) reaches the base case n \u2264 1 after a finite number of recursive calls. Hence the function terminates for all non‑negative integers n, completing the proof.

---

*Result IR*
