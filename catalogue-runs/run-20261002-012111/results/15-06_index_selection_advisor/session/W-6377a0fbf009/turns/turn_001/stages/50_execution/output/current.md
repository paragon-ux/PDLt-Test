-- Index recommendations for the events table based on the given workload

-- 1. Supports Q1 (filter by user_id and created_at, order by created_at DESC)
CREATE INDEX idx_events_user_created_desc ON events (user_id, created_at DESC);

-- 2. Supports Q2 (filter by event_type and processed, order by created_at ASC). Including the primary key column can make index‑only scans possible.
CREATE INDEX idx_events_eventtype_processed ON events (event_type, processed) INCLUDE (id);

-- 3. Supports Q3 (range on created_at) and also benefits Q1 ordering. A simple btree on created_at covers the range and ordering requirements.
CREATE INDEX idx_events_created_at ON events (created_at);

-- 4. Supports Q4 (JSONB containment). Use a GIN index on the payload column.
CREATE INDEX idx_events_payload_gin ON events USING GIN (payload);

-- 5. Q5 is already covered by the primary key on id (id BIGINT PRIMARY KEY), so no additional index is needed.

-- Space overhead estimates (approximate, based on typical PostgreSQL index size factors):
-- * idx_events_user_created_desc: ~1.2 GB (covers two columns, ~2.5 % of table size)
-- * idx_events_eventtype_processed: ~800 MB (two columns with INCLUDE, ~1.5 % of table size)
-- * idx_events_created_at: ~600 MB (single column, ~1 % of table size)
-- * idx_events_payload_gin: ~1.5 GB (GIN index on JSONB, ~3 % of table size)
-- Total additional storage ≈ 4.1 GB, roughly 8 % of the 50 M‑row table size.
