TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Provide a formal correctness proof of the merge sort algorithm, including: (1) a proof that merge sort terminates on all finite input lists using the length of the input as a well‑founded measure; (2) a proof that the returned list is in non‑decreasing order; (3) a proof that the returned list is a permutation of the input list. Use structural induction on the list length. Additionally, provide a separate proof for the merge subroutine showing that merging two sorted lists yields a sorted list that is a permutation of the concatenation of the two input lists.
APPROACH/RISK NOTES:
Apply structural induction on list length for the overall merge sort correctness proof, and treat the merge subroutine proof as a separate inductive argument. Present base case and inductive step clearly, without executing the algorithm or providing concrete examples.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- merge sort
- merge
