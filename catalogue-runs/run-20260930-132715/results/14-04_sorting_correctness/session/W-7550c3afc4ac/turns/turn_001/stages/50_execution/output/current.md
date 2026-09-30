PROVIDE a formal proof that merge sort terminates on all finite input lists using length as a well‑founded measure.
PROVE that the output list of merge sort is sorted in non‑decreasing order.
PROVE that the output list of merge sort is a permutation of the input list.
USE structural induction on list length for the above proofs.
SEPARATELY, PROVE that the merge subroutine, which merges two sorted lists, produces a list that is sorted in non‑decreasing order and is a permutation of the concatenation of the two input lists.
INCLUDE all required conclusions, definitions, and evidence as specified, without performing the proofs themselves.

---
**R1 – Termination of Merge Sort**
We prove by strong induction on the length \(n\) of the input list \(L\).
*Base cases:*
- \(n=0\): The algorithm returns the empty list immediately – terminates.
- \(n=1\): The algorithm returns the singleton list – terminates.
*Inductive step:* Assume for all lists of length \(k\le n\) the algorithm terminates. For a list of length \(n+1\), the algorithm splits \(L\) into two sublists \(L_1\) and \(L_2\) of lengths \(⌊(n+1)/2⌋\) and \(⌈(n+1)/2⌉\), each ≤ n. By the induction hypothesis, recursive calls on \(L_1\) and \(L_2\) terminate. The subsequent call to the merge routine is a finite loop/recursion on the total length \(n+1\) and therefore terminates. Hence merge sort terminates for length \(n+1\).
Thus, by induction, merge sort terminates for all finite lists.

**R2 – Sortedness of Merge Sort Output**
Induction on list length as above.
*Base cases:* Empty and singleton lists are trivially sorted.
*Inductive step:* By IH, recursive sorts on \(L_1\) and \(L_2\) produce sorted lists \(S_1\) and \(S_2\). By the separately proved correctness of the merge routine (R4), merging \(S_1\) and \(S_2\) yields a sorted list. Hence the result of merge sort on \(L\) is sorted.

**R3 – Permutation Property of Merge Sort Output**
Induction on length.
*Base cases:* Empty and singleton lists contain exactly the same elements as themselves.
*Inductive step:* The split operation partitions \(L\) into \(L_1\) and \(L_2\) without loss or duplication, so \(L\) is a permutation of the concatenation \(L_1\!+\!L_2\). By IH, the recursive sorts produce permutations \(S_1\) of \(L_1\) and \(S_2\) of \(L_2\). The merge routine (R4) returns a permutation of \(S_1\!+\!S_2\). Consequently the final output is a permutation of \(L_1\!+\!L_2\), and hence of \(L\).

---
**R4 – Correctness of Merge Subroutine**
We prove by strong induction on the total length \(m\) of the two input sorted lists \(A\) and \(B\).
*Base case:* \(m=0\) (both lists empty). Merge returns the empty list, which is sorted and a permutation of the concatenation.
*Inductive step:* Assume correctness for all total lengths ≤ k. For total length \(k+1\), consider the heads of \(A\) and \(B\). Without loss of generality, let \(head(A) \le head(B)\). The algorithm prepends \(head(A)\) to the result of merging \(tail(A)\) with \(B\). The tails have total length \(k\), so by IH the recursive call returns a sorted list that is a permutation of \(tail(A)\!+\!B\). Adding \(head(A)\) at the front preserves sortedness (since it is ≤ the first element of the recursive result) and yields a permutation of \(A\!+\!B\). The symmetric case when \(head(B) < head(A)\) is analogous. Hence merge produces a sorted list that is a permutation of the concatenation of its inputs.

---
**R5 – Overall Conclusion**
Combining R1–R4, we have shown:
1. Merge sort terminates on all finite input lists.
2. Its output is sorted in non‑decreasing order.
3. Its output is a permutation of the input list.
4. The merge subroutine itself satisfies sortedness and permutation properties.
These results fulfill all requirements of the task.
