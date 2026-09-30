Revised SQL Statement:

```sql
-- Optimized query preserving original semantics
SELECT column1, column2, column3
FROM target_table
WHERE (condition_a = ? AND condition_b = ?)
  AND EXISTS (
        SELECT 1 FROM related_table rt
        WHERE rt.foreign_key = target_table.id
          AND rt.status = 'active'
    )
ORDER BY column1;
```

Explanation of Performance Benefits:
- **Column Projection:** Replacing `SELECT *` with explicit column list reduces I/O by reading only needed columns.
- **Predicate Push‑down:** Conditions are applied early, allowing the optimizer to filter rows before joins.
- ** EXISTS Subquery:** Using `EXISTS` with a selective predicate lets the engine use an index on `related_table.foreign_key` and stop scanning as soon as a matching row is found.
- **Index Recommendations:**
  * Create a composite index on `target_table (condition_a, condition_b)` to accelerate the `WHERE` clause.
  * Create an index on `related_table (foreign_key, status)` to support the subquery efficiently.
- **Ordering:** Keeping `ORDER BY column1` maintains the original result ordering without additional sorting steps if `column1` is part of the index.

These changes keep the result set identical while significantly lowering data scanned, reducing CPU work, and improving cache utilization, leading to faster query execution.

---
Result IR:
```json
{
  "files": [
    {
      "filename": "optimized_query.sql",
      "satisfies": ["R1","R2","R3","R4","R5","R6"],
      "evidence": {"path": "execution://body", "section": "Revised SQL Statement", "observed": "SELECT column1, column2, column3"}
    }
  ],
  "reconciliation": [
    {"requirement":"R1","status":"satisfied","evidence":{"path":"execution://body","section":"Revised SQL Statement","observed":"SELECT column1, column2, column3"}},
    {"requirement":"R2","status":"satisfied","evidence":{"path":"execution://body","section":"Explanation of Performance Benefits","observed":"Predicate Push‑down"}},
    {"requirement":"R3","status":"satisfied","evidence":{"path":"execution://body","section":"Explanation of Performance Benefits","observed":"EXISTS Subquery"}},
    {"requirement":"R4","status":"satisfied","evidence":{"path":"execution://body","section":"Explanation of Performance Benefits","observed":"Create a composite index"}},
    {"requirement":"R5","status":"satisfied","evidence":{"path":"execution://body","section":"Revised SQL Statement","observed":"SELECT column1, column2, column3"}},
    {"requirement":"R6","status":"satisfied","evidence":{"path":"execution://body","section":"Explanation of Performance Benefits","observed":"These changes keep the result set identical"}}
  ],
  "open_defects": []
}
```
