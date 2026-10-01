PARSE the supplied list of integers L.
GENERATE all unordered pairs (a, b) from L where a < b.
COMPUTE c = a + b for each pair.
FILTER triples (a, b, c) where c ∈ L and c ≠ a and c ≠ b.
COLLECT the filtered triples as candidate triples.
SEARCH for a selection of 15 candidate triples that are pairwise disjoint and whose union equals L.
IF a valid selection is found THEN
    EMIT the selected 15 triples as the example partition.
ELSE
    EMIT a statement that no valid partition exists.
