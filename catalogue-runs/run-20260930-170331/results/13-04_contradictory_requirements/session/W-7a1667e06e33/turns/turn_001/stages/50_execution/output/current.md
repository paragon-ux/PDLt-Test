It is mathematically impossible to satisfy all the requested constraints simultaneously. A comparison‑based sorting algorithm has a lower bound of Ω(n log n) time in the worst case; therefore a linear‑time (O(n)) worst‑case bound cannot be achieved without abandoning the comparison‑based model. Consequently, no algorithm can be both:
1. Comparison‑based,
2. Have O(n) worst‑case time,
3. Be stable, and
4. Sort in‑place using O(1) extra space.
Any attempt to meet the O(n) worst‑case requirement must either use non‑comparison techniques (e.g., counting/radix sort) or relax the stability/in‑place constraints. The combination of all four constraints is contradictory.

Hence, the task as stated has no feasible solution.
