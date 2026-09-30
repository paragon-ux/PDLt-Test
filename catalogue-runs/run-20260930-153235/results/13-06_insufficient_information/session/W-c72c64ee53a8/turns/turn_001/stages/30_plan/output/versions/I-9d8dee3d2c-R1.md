ANALYZE the provided SQL SELECT query for performance characteristics
IDENTIFY potential bottlenecks in the query structure, including SELECT *, missing column lists, absent indexes, inefficient joins, and lack of query hints
GENERATE a concise list of recommendations to maximize performance, covering:
- SELECT specific columns instead of SELECT *
- ADD appropriate indexes on columns used in WHERE, JOIN, ORDER BY, and GROUP BY clauses
- REWRITE joins to use optimal join types and ordering
- APPLY suitable query hints or optimizer directives for the target database engine
- SUGGEST additional restructuring such as partitioning or query refactoring if applicable
