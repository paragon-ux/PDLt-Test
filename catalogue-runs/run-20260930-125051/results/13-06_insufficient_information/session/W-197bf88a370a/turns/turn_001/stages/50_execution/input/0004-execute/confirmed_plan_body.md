ANALYZE the target database schema and data distribution
IDENTIFY columns used for filtering, joining, ordering, and aggregation in the intended query
EVALUATE existing indexes and determine if additional indexes are needed for high‑selectivity predicates
REWRITE the SELECT statement to retrieve only required columns instead of using *
APPLY query rewrite techniques such as predicate push‑down, join reordering, and subquery flattening
UTILIZE EXPLAIN (ANALYZE) to profile the execution plan and locate costly operations
OPTIMIZE the execution plan by adding or adjusting indexes, adjusting statistics, and configuring query hints if supported
VALIDATE performance improvements by benchmarking the original and optimized queries under realistic workloads
