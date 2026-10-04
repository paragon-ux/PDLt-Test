Notation: ms(L) is the multiset of L; sorted(L) means non-decreasing.

Merge lemma. If A and B are sorted, merge(A, B) is sorted and ms(merge(A,B)) = ms(A) + ms(B).
Proof by induction on |A| + |B|. If either is empty, merge returns the other: sorted, same multiset. Otherwise let a = head(A), b = head(B), and suppose a <= b (the other case is symmetric). merge returns a :: merge(tail A, B). By IH the recursive result R is sorted with ms(R) = ms(tail A) + ms(B). Every element of R is >= a: elements of tail A are >= a because A is sorted, and elements of B are >= b >= a because B is sorted. So a :: R is sorted, and its multiset is {a} + ms(tail A) + ms(B) = ms(A) + ms(B).

Termination. If n <= 1 merge sort returns at once. If n >= 2 the halves have lengths floor(n/2) and ceil(n/2), both at least 1 and at most n - 1. Length is a natural number, so by well-founded induction on length every call terminates (merge itself terminates since |A| + |B| decreases each step).

Sortedness and permutation, by strong induction on n. Base: n <= 1, the list is returned unchanged; it is sorted and a permutation of itself. Step: n >= 2, the input L splits into L1, L2 with ms(L1) + ms(L2) = ms(L). By IH S1 = msort(L1), S2 = msort(L2) are sorted with ms(Si) = ms(Li). By the merge lemma merge(S1, S2) is sorted with multiset ms(S1) + ms(S2) = ms(L). QED.
