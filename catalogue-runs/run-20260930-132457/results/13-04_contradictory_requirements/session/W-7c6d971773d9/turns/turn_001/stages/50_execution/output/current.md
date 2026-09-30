It is impossible to implement a comparison‑based sorting algorithm that simultaneously satisfies all of the following constraints:

1. **O(n) worst‑case time complexity** – Comparison‑based sorting algorithms have a proven lower bound of Ω(n log n) comparisons in the worst case. This bound applies to any algorithm that relies solely on pairwise element comparisons, regardless of stability or space usage.
2. **Stability** – While stability is achievable (e.g., mergesort), it does not relax the comparison lower bound.
3. **In‑place with O(1) extra space** – In‑place algorithms (e.g., heapsort) meet the space requirement but still require Ω(n log n) time.

Because requirement R1 ("IMPLEMENT a comparison‑based sorting algorithm ...") cannot be fulfilled under the theoretical limits of comparison‑based sorting, no algorithm can satisfy the combined constraints. Therefore, the task is infeasible.

*Conclusion*: The requirement set is contradictory; a comparison‑based sort cannot run in linear worst‑case time, even if stability and in‑place constraints are relaxed.

---
Result IR follows the required schema.
