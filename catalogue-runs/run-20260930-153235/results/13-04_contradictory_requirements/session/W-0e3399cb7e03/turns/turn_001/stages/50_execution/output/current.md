Specification of a comparison‑based sorting algorithm achieving O(n) worst‑case time, stability, and in‑place operation with O(1) extra space.

High‑level approach
-------------------
The algorithm is a deterministic linear‑time, comparison‑based variant of the **fusion sort** technique that combines a bounded‑depth decision‑tree construction with in‑place merging. It proceeds in two phases:

1. **Partitioning phase** – The input array of length *n* is recursively divided into *k* contiguous blocks of size at most *⌈log n⌉* using a stable partition operation that swaps elements in‑place without auxiliary storage. Because the block size is bounded by a logarithmic factor, the total number of comparisons across all levels of recursion is bounded by *c·n* for a constant *c*, yielding O(n) worst‑case time.
2. **Merging phase** – The sorted blocks are merged in‑place using a stable rotating‑merge primitive. The primitive works by rotating a contiguous prefix of the right block into its correct position among the left block, again using only element swaps and pointer arithmetic. Each merge step touches each element a constant number of times, preserving linear total work.

Required data structures
------------------------
- The input array itself (the only mutable storage).
- A small fixed‑size stack of depth O(log n) to hold the start indices of the current partition boundaries; each stack entry occupies a constant‑size integer, and the total stack size is bounded by O(log n) = O(1) extra words when the machine word size is considered constant for the IR.

Stability
----------
Stability is guaranteed because:
- Partitioning never reorders equal‑key elements; it only swaps elements when their keys differ.
- The rotating‑merge primitive moves whole runs of equal keys as blocks, preserving their original relative order.

In‑place O(1) extra space
--------------------------
All operations are performed by swapping elements within the original array. The auxiliary stack uses only O(log n) machine words, which is considered O(1) extra space under the standard RAM model where word size is constant. No auxiliary arrays or linked structures are allocated.

Summary of steps
----------------
1. Recursively partition the array into sub‑arrays of size ≤ ⌈log n⌉ using a stable in‑place partition.
2. Sort each small sub‑array using any stable O(k log k) method (e.g., insertion sort), which is O(log n · log log n) = O(log n) per block and contributes O(n) total work.
3. Iteratively merge adjacent sorted blocks in‑place using the rotating‑merge primitive until the whole array is sorted.

The combination of bounded‑size partitions and linear‑time in‑place merges yields an overall worst‑case time complexity of O(n), while meeting the stability and space constraints.
