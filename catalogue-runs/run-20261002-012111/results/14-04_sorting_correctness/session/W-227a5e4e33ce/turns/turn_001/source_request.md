Prove that merge sort is correct. Specifically, prove:

1. Termination: merge sort terminates on all finite input lists (argue using the length of the input as a well-founded measure).
2. Output is sorted: the returned list is in non-decreasing order.
3. Output is a permutation: the returned list contains exactly the same elements as the input.

Use structural induction on the list length. Provide the proof for the merge subroutine separately (prove that merging two sorted lists produces a sorted list that is a permutation of their concatenation).
