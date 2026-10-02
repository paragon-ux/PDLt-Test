PARSE the supplied SQL query
ANALYZE the relevant database schema and indexes
IDENTIFY performance bottlenecks and suboptimal constructs in the query
REWRITE the query to replace SELECT * with an explicit column list and improve predicate placement
OPTIMIZE join ordering and apply predicate pushdown where beneficial
CONSIDER adding or modifying indexes to support the rewritten query
EVALUATE the execution plan using EXPLAIN or an equivalent profiling tool
SELECT the version of the query with the lowest estimated cost
OUTPUT the optimized query
