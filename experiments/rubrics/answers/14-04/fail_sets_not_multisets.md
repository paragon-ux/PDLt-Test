Merge: if A and B are sorted, merge(A,B) is sorted, since we always take the smaller head. Also set(merge(A,B)) = set(A) ∪ set(B) because every element taken comes from A or B.

Termination: the list gets shorter each call.

By induction, merge sort returns a sorted list whose set of elements equals the input's set, so it is a permutation.
