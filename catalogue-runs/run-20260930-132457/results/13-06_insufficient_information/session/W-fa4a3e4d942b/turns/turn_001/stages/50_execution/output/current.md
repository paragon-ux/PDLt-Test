# Actionable Recommendations for Query Performance

1. **Read the current SELECT statement**
   - Examine the existing query that uses `SELECT *` and note the table(s) involved.

2. **Identify required columns**
   - Determine which columns are actually needed for the result set (e.g., columns used by the application, reports, or downstream joins).  Replace `SELECT *` with an explicit column list.

3. **Rewrite the query**
   - Change the query to `SELECT col1, col2, … FROM table …` using only the identified columns.

4. **Evaluate existing indexes**
   - Review indexes on the table.  Ensure there is an index that covers the columns used in `WHERE` predicates and any join keys.  If the query filters on columns not indexed, consider adding a composite index that includes those columns (and, if possible, the needed SELECT columns for a covering index).

5. **Suggest query restructuring**
   - Add appropriate `WHERE` clauses to filter rows early.
   - Use explicit `JOIN` syntax with `ON` conditions rather than implicit joins.
   - If only a subset of rows is needed, apply `LIMIT` (or pagination) to reduce result size.
   - Consider rewriting sub‑queries or using `EXISTS/NOT EXISTS` instead of `IN` where beneficial.

6. **Guide execution‑plan optimization**
   - Run `EXPLAIN ANALYZE` on the rewritten query to verify the plan uses index seeks/scans instead of full table scans.
   - Make sure statistics are up‑to‑date (`ANALYZE` or `UPDATE STATISTICS`).
   - Avoid functions on indexed columns in `WHERE` clauses, as they can prevent index usage.

7. **Provide concise actionable list**
   - Replace `SELECT *` with explicit column list.
   - Add/adjust indexes to cover filter predicates and selected columns.
   - Refine `WHERE` clauses to filter early.
   - Use proper JOIN syntax and limit result sets.
   - Keep statistics current and verify plan with `EXPLAIN`.

These steps should significantly reduce I/O, improve cache utilization, and enable the optimizer to choose more efficient execution plans.
