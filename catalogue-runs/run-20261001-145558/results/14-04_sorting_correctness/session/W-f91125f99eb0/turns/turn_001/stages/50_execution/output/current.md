Proof Specification for Merge Sort Correctness

**Goal**: Provide a detailed specification of the proofs required to demonstrate the correctness of merge sort, without carrying out the proofs themselves.

**Structure**:

1. **Termination Proof**
   - **Base Cases**: Show that merge sort terminates for the empty list and a single‑element list (no recursive calls).
   - **Inductive Step**: Assume termination for all lists of length ≤ n. For a list of length n+1, the algorithm splits the list into two sub‑lists of strictly smaller length, recursively sorts each, and then merges them. By the induction hypothesis each recursive call terminates, and the merge subroutine also terminates (proved separately). Hence the whole algorithm terminates.
   - **Measure**: Use the length of the input list as a well‑founded measure that strictly decreases on each recursive call.

2. **Sortedness Proof**
   - **Base Cases**: The empty list and any single‑element list are trivially sorted.
   - **Inductive Step**: Assume that recursively sorting the two halves yields sorted lists. Then apply the correctness of the merge subroutine (see below) to conclude that the concatenation of the two sorted halves after merging is also sorted.
   - **Reference to Induction Hypothesis**: Explicitly cite the hypothesis that the recursive calls return sorted lists.

3. **Permutation Proof**
   - **Base Cases**: The empty list and single‑element list are permutations of themselves.
   - **Inductive Step**: Assume the recursive calls produce permutations of their respective sub‑lists. Show that merging two permutations of the two halves yields a permutation of the concatenation of the halves, which is itself a permutation of the original list. This relies on the merge subroutine preserving the multiset of elements.

4. **Merge Subroutine Proof** (separate sub‑proof)
   - **Goal**: Prove that merging two sorted lists `L1` and `L2` produces a sorted list `M` that is a permutation of `L1 ++ L2`.
   - **Base Cases**: When either `L1` or `L2` is empty, the result is the other list, which is sorted and a permutation of the concatenation.
   - **Inductive Step**: Assume the property holds for the tails of the lists. Compare the heads of `L1` and `L2`; the smaller head is placed first, and the merge proceeds recursively on the remaining elements. Use the induction hypothesis to argue that the recursive call yields a sorted list that is a permutation of the remaining concatenation, and thus the whole result satisfies both properties.

5. **Documentation Requirements**
   - Clearly state each base case and inductive step.
   - Explicitly reference the induction hypothesis where it is used.
   - Indicate the well‑founded measure (list length) for termination.
   - Separate the merge subroutine proof from the overall merge sort proof.
   - Do not execute any proofs; this document merely specifies the proof obligations.

**Note**: No actual proof steps are performed. The specification above must be carried out by the prover.
