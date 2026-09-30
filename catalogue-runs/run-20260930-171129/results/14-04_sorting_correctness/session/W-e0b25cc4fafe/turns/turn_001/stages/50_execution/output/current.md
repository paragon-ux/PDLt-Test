Proof of Correctness of Merge Sort Using Structural Induction

**Theorem**: For any finite list *L* of elements from a totally ordered set, the Merge Sort algorithm terminates, returns a list that is sorted in non‑decreasing order, and returns a permutation of *L*.

The proof proceeds by structural induction on the length *n = |L|* of the input list.

---
### 1. Base Cases

*Case n = 0 (empty list)*
- The algorithm checks the length; since *n ≤ 1*, it returns the list unchanged. This clearly terminates.
- The returned list is empty, which is vacuously sorted.
- The empty list contains exactly the elements of the input (none), so it is a permutation of the input.

*Case n = 1 (singleton list)*
- The length check again triggers the “already sorted” branch, returning the list unchanged. Termination is immediate.
- A one‑element list is trivially sorted.
- The output list contains the same single element as the input, hence a permutation.

Thus termination, sortedness, and permutation hold for *n = 0,1*.

---
### 2. Inductive Hypothesis
Assume that for all lists of length *k* with *k < n* (where *n ≥ 2*), Merge Sort terminates, returns a sorted list, and that list is a permutation of the input.

---
### 3. Inductive Step for a List *L* of Length *n*
1. **Split** *L* into two sub‑lists *L₁* and *L₂* of lengths ⌊*n*/2⌋ and ⌈*n*/2⌉. Both lengths are **strictly less** than *n*.
2. **Recursive calls**
   - By the inductive hypothesis, `merge_sort(L₁)` terminates, yields a sorted list *S₁* that is a permutation of *L₁*.
   - Similarly, `merge_sort(L₂)` terminates, yields a sorted list *S₂* that is a permutation of *L₂*.
3. **Merge** the two sorted lists *S₁* and *S₂* using the `merge` sub‑routine.

We must now show that the merge step preserves the three properties.

---
### 4. Correctness of the Merge Sub‑routine
The `merge` routine repeatedly compares the heads of two sorted input lists and appends the smaller (or equal) head to the output list, advancing the pointer of the list from which the element was taken. The process stops when both input lists are exhausted.

**Termination**: Each iteration consumes one element from at least one input list. Because the inputs are finite, after exactly |S₁| + |S₂| iterations both become empty, and the routine stops.

**Sortedness**: At each step the smallest remaining head element among the two inputs is appended to the output. Hence the output list is built in non‑decreasing order; no later element can be smaller than an earlier one.

**Permutation**: Every element taken from the inputs is appended exactly once to the output, and no element is created or discarded. Consequently the output list contains precisely the multiset union of the two inputs, i.e., a permutation of *S₁ ∪ S₂*.

---
### 5. Completion of the Inductive Step
Applying the merge routine to *S₁* and *S₂* yields a list *M* such that:
- **Termination** follows from the termination of the recursive calls and the merge routine.
- **Sortedness**: Since *S₁* and *S₂* are sorted and merge preserves sortedness, *M* is sorted.
- **Permutation**: *M* is a permutation of *S₁ ∪ S₂*, which by the inductive hypothesis is a permutation of *L₁ ∪ L₂ = L*.

Thus all three properties hold for a list of length *n*.

---
### 6. Conclusion
By structural induction, Merge Sort terminates for every finite input list, returns a list that is sorted in non‑decreasing order, and returns a permutation of the original list. The proof of the merge sub‑routine guarantees that the composition of the recursive calls yields the claimed result.

---
*QED*
