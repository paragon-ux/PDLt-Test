PARSE the supplied list L of 45 distinct positive integers.
GENERATE all unordered pairs (a_i, b_i) from L.
FOR each pair compute the sum c = a_i + b_i.
FILTER triples (a_i, b_i, c) where c is a distinct element of L not equal to a_i or b_i.
BUILD a collection of candidate triples.
APPLY a constraint-satisfaction search to select 15 triples that are pairwise disjoint and together cover every element of L exactly once.
IF a complete disjoint triple set is found THEN EMIT that triple set as the example partition.
ELSE EMIT a statement that no such partition exists.
