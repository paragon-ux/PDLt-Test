To maximize performance of the query pattern `SELECT * FROM ???` apply the following concrete steps:

1. **Identify required columns** – Determine which columns are actually needed for the result set. Replace `SELECT *` with `SELECT col1, col2, …` listing only those columns.
2. **Add appropriate indexes** – For each table referenced, create indexes on columns used in:
   - `WHERE` predicates
   - `JOIN` conditions
   - `ORDER BY` clauses
   Example (PostgreSQL syntax):
   ```sql
   CREATE INDEX idx_table_column ON table_name (column_name);
   ```
3. **Rewrite joins** – Use explicit `JOIN` syntax instead of comma‑separated tables. Ensure join conditions are on indexed columns.
4. **Limit result set** – If only a subset of rows is needed, add a `WHERE` filter or `LIMIT` clause.
5. **Review query plan** – Run `EXPLAIN ANALYZE` (or the equivalent in your RDBMS) on the rewritten query to verify that index scans are used and that the cost is reduced.
6. **Avoid functions on indexed columns** – Do not wrap indexed columns in functions or expressions in `WHERE`/`JOIN` conditions, as this prevents index usage.
7. **Consider covering indexes** – If a query selects only a few columns and those columns are indexed together, the index can satisfy the query without needing to read the full table rows.

**Example transformation**
```sql
-- Original (inefficient)
SELECT * FROM orders o JOIN customers c ON o.customer_id = c.id WHERE o.status = 'pending';

-- Optimized version
SELECT o.order_id, o.order_date, c.name, c.email
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE o.status = 'pending';

-- Recommended indexes
CREATE INDEX idx_orders_status ON orders (status);
CREATE INDEX idx_orders_customer_id ON orders (customer_id);
CREATE INDEX idx_customers_id ON customers (id);
```

After applying these changes, re‑run `EXPLAIN ANALYZE` to confirm that the query uses index scans and that the estimated execution time is significantly lower.

---
Result IR:
```json
{
  "files": [
    {
      "filename": "optimization.md",
      "satisfies": ["R1"],
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "Apply the generic optimization strategies ... and rewrite the query to SELECT only those necessary columns instead of SELECT *"
      }
    }
  ],
  "reconciliation": [
    {
      "requirement": "R1",
      "status": "satisfied",
      "evidence": {
        "path": "execution://body",
        "section": null,
        "observed": "OPTIMIZE the database query for maximum performance"
      }
    }
  ],
  "open_defects": []
}
```
