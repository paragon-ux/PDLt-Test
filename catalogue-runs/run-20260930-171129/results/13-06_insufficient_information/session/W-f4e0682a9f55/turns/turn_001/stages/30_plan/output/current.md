ANALYZE the supplied SQL query to identify selected columns, tables, joins, filters, and ordering clauses
EXTRACT the schema metadata for involved tables, including indexes, column statistics, and foreign key relationships
EVALUATE potential indexing strategies relevant to filter predicates and join conditions
CONSIDER query rewrite techniques such as predicate push‑down, join reordering, subquery flattening, or using EXISTS versus IN
GENERATE alternative query formulations incorporating identified optimizations
APPLY EXPLAIN (ANALYZE) to each alternative to collect execution plans and performance metrics
COMPARE the execution plans to determine cost reductions, I/O savings, and runtime improvements
SELECT the formulation with the best performance characteristics as the optimized query
