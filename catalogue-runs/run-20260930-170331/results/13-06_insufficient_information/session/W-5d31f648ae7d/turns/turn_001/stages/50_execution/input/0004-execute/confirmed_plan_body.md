ANALYZE the provided query pattern to determine required result columns
IDENTIFY the minimal set of columns needed for the intended result
REWRITE the query to SELECT only those necessary columns instead of SELECT *
EXAMINE the tables involved to determine appropriate indexing opportunities
CREATE or RECOMMEND indexes on columns used in WHERE clauses, JOIN conditions, and ORDER BY clauses
VERIFY that query syntax follows best practices for proper clause ordering and use of explicit JOINs
EVALUATE the revised query for performance improvements using EXPLAIN or similar profiling tools
