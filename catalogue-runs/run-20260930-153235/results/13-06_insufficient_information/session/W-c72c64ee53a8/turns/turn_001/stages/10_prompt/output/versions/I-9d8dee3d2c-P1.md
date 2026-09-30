ANALYZE the provided SQL SELECT query for performance characteristics
IDENTIFY potential bottlenecks in the query structure, including use of SELECT *, missing column lists, absent indexes, inefficient joins, and lack of query hints
RECOMMEND improvements to maximize performance, specifying:
- SELECT specific columns instead of SELECT *
- ADD appropriate indexes on columns used in WHERE, JOIN, ORDER BY, and GROUP BY clauses
- REWRITE joins to use optimal join types and ordering
- APPLY suitable query hints or optimizer directives for the target database engine
- SUGGEST any additional restructuring such as partitioning or query refactoring if applicable
PROVIDE the recommendations as a concise list without executing or testing the query
