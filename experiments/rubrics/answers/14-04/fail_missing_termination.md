Merge lemma: if A and B are sorted, merging them produces a sorted list, because the next element taken is the smaller head, which is <= everything left; and every element of A and B appears exactly once in the output, so the multisets agree. (Induction on |A|+|B|.)

Merge sort: by induction on n, the two recursive results are sorted permutations of the halves, so their merge is a sorted permutation of the input. The base case of one element is sorted.

Hence merge sort is correct.
