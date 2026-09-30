ANALYZE the supplied query workload (Q1‑Q5) to extract columns used in WHERE clauses, JOIN conditions, ORDER BY, and GROUP BY clauses
IDENTIFY candidate indexes for each extracted column or column combination, considering B‑tree, partial, and expression index possibilities
GROUP candidate indexes across queries to find overlapping coverage and reduce redundancy
EVALUATE the benefit of each candidate index against the workload using heuristics such as selectivity, frequency, and estimated I/O reduction
SELECT a minimal set of indexes that maximizes overall query performance while respecting space constraints
FOR each selected index, CONSTRUCT the precise CREATE INDEX statement, including any partial predicates or expression definitions as required
MAP each constructed index to the specific queries (Q1‑Q5) it is intended to serve
ESTIMATE the storage overhead of each index relative to the base table size using typical index size formulas
