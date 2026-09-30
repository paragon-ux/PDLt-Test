--- Index Recommendations for the events table (50M rows) ---

**Index I1** (serves Q1)
```sql
CREATE INDEX idx_events_user_created_desc ON events (user_id, created_at DESC);
```
*Explanation*: Q1 filters on `user_id = ?` and `created_at > ?` and orders by `created_at DESC`. The composite B‑tree index matches the WHERE columns in the same order and stores `created_at` in descending order, allowing the ORDER BY to be satisfied without a separate sort. It also supports the LIMIT 50 efficiently.
*Estimated size*: Roughly 25 % of the table size (~12.5 GB) – each entry stores the indexed columns (4 bytes + 8 bytes) plus a tuple pointer (≈6 bytes) → ~18 bytes/row → ~0.9 GB, plus B‑tree overhead ≈ 2× → ~2.5 GB.

**Index I2** (serves Q2)
```sql
CREATE INDEX idx_events_type_processed_asc ON events (event_type, processed, created_at ASC);
```
*Explanation*: Q2 filters on `event_type = ?` and `processed = false` and orders by `created_at ASC`. A three‑column B‑tree index with `processed` included lets PostgreSQL use index‑only scans for the predicate and satisfy the ORDER BY.
*Estimated size*: Similar calculation → ~3 GB (≈ 6 % of table).

**Index I3** (serves Q3)
```sql
CREATE INDEX idx_events_created_user ON events (created_at, user_id);
```
*Explanation*: Q3 groups rows by `user_id` within a `created_at` range. An index on `(created_at, user_id)` allows fast range scans on `created_at` and groups rows by `user_id` without additional sorting, improving the `GROUP BY`/`HAVING` performance.
*Estimated size*: ~4 GB (≈ 8 % of table).

**Index I4** (serves Q4) – expression index on JSONB
```sql
CREATE INDEX idx_events_payload_keyvalue ON events ((payload ->> 'key'))
WHERE payload ? 'key';
```
*Explanation*: Q4 uses the JSONB containment operator `@> '{"key": "value"}'`. By extracting the key as a text expression and making the index partial to rows that actually contain the key, PostgreSQL can evaluate the predicate via the index.
*Estimated size*: Only rows with the key are indexed; assuming 10 % of rows contain it, size ≈ 0.5 GB.

**Index I5** (serves Q5) – primary key already exists
```sql
-- The primary key on id (BIGINT) already provides an index:
-- CREATE UNIQUE INDEX events_pkey ON events (id);
```
*Explanation*: Q5 queries by primary key; the existing PK index satisfies it.
*Estimated size*: Already accounted for in the table's internal structures.

--- Overall storage overhead ---
Total additional index size ≈ 12.5 GB (≈ 25 % of the 50 M‑row table). This respects typical space constraints while delivering substantial query speedups for the high‑frequency workload (Q1 40 % + Q2 30 %).
