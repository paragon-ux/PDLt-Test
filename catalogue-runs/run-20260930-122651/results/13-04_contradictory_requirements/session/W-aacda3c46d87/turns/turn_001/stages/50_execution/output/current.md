Explanation:

A comparison‑based sorting algorithm cannot simultaneously satisfy the four constraints of being comparison‑based, having O(n) worst‑case time complexity, being stable, and sorting in‑place with O(1) extra space.

**Information‑theoretic lower bound**
For any comparison‑based sorting algorithm, each comparison can be viewed as a binary decision that partitions the set of possible input permutations. To correctly sort n distinct elements, the algorithm must be able to distinguish among n! possible orderings. The decision tree therefore requires at least log₂(n!) ≈ n·log₂ n – O(n) comparisons in the worst case. This yields the lower bound Ω(n log n) on the number of comparisons, and consequently on the worst‑case time complexity of any comparison‑based sort.

**Conflict with O(n) worst‑case time**
Achieving O(n) worst‑case time would require the algorithm to perform only a linear number of comparisons, which contradicts the Ω(n log n) lower bound. No comparison‑based method can circumvent this bound, so the O(n) worst‑case requirement is impossible to fulfill alongside the comparison‑based requirement.

**In‑place O(1) extra space and stability constraints**
In‑place sorting with O(1) extra space severely restricts the algorithm’s ability to rearrange elements without auxiliary storage. When stability is also required, the algorithm must preserve the relative order of equal keys, which typically needs additional bookkeeping (e.g., extra pointers or buffers) to avoid overwriting equal elements during in‑place moves. Combining O(1) space with stability imposes further information‑theoretic constraints: the algorithm cannot arbitrarily reorder equal elements without extra memory to remember their original order. Consequently, any stable, in‑place, comparison‑based sort that respects the Ω(n log n) lower bound cannot achieve O(n) worst‑case time.

**Conclusion**
Because the Ω(n log n) lower bound for comparison‑based sorting rules out linear‑time worst‑case performance, and because stability together with strict O(1) extra‑space in‑place operation adds additional prohibitions, it is impossible for any comparison‑based sorting algorithm to meet all four constraints simultaneously. No such algorithm exists, and any claim to the contrary would violate fundamental theoretical limits.
