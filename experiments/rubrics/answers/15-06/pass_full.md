```sql
-- Q1 (40%): equality on user_id, range + ORDER BY created_at DESC LIMIT 50
CREATE INDEX CONCURRENTLY idx_events_user_created ON events (user_id, created_at DESC);
-- Q2 (30%): only unprocessed rows; ordered by created_at
CREATE INDEX CONCURRENTLY idx_events_unprocessed ON events (event_type, created_at) WHERE processed = false;
-- Q3 (15%): time-range aggregation; covering user_id avoids heap fetches
CREATE INDEX CONCURRENTLY idx_events_created_user ON events (created_at) INCLUDE (user_id);
-- Q4 (10%): JSONB containment
CREATE INDEX CONCURRENTLY idx_events_payload ON events USING GIN (payload jsonb_path_ops);
-- Q5 (5%): primary key already serves id = ?
```
Space (50M rows): idx_events_user_created ≈ 50M × ~24 B per entry + overhead ≈ 1.5 GB. idx_events_unprocessed: the same per-row size times the unprocessed fraction (e.g. 1% → ~15 MB). idx_events_created_user ≈ 1.5 GB (a BRIN on created_at would be ~100 KB if rows are inserted in time order, at the cost of less precise scans). GIN on payload: often 20-50% of the JSONB column size, depending on key diversity.
