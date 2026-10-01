-- Recommended index set for the events table
-- Table schema: id BIGINT PK, user_id INT, event_type TEXT, payload JSONB, created_at TIMESTAMP, processed BOOLEAN

-- 1. Index for Q1 (filter by user_id and recent created_at, order by created_at DESC)
CREATE INDEX idx_events_user_created_desc ON events (user_id, created_at DESC);
-- Serves: Q1
-- Estimated size: ~30% of the table size (≈15 GB for a 50 M row table with typical row width), because it stores user_id (4 B) and created_at (8 B) plus index overhead.

-- 2. Partial index for Q2 (event_type = ?, processed = false, order by created_at ASC)
CREATE INDEX idx_events_type_processed_created_asc ON events (event_type, created_at ASC) WHERE processed = false;
-- Serves: Q2
-- Estimated size: ~10% of the table size (≈5 GB), as it includes only rows where processed = false.

-- 3. Index for Q3 (group by user_id, filter on created_at range)
CREATE INDEX idx_events_created_user ON events (created_at, user_id);
-- Serves: Q3
-- Estimated size: ~25% of the table size (≈12.5 GB); stores created_at and user_id for all rows.

-- 4. Expression index for JSONB containment used in Q4
CREATE INDEX idx_events_payload_key ON events ((payload ->> 'key'));
-- Serves: Q4 (payload @> '{"key": "value"}')
-- Estimated size: ~20% of the table size (≈10 GB), indexing the extracted text value.

-- 5. Primary key index (already exists) – serves Q5
-- CREATE UNIQUE INDEX idx_events_pkey ON events (id);
-- Serves: Q5
-- Size: negligible additional overhead beyond the table's clustered primary key.

-- Summary:
--   • Five indexes cover all five queries.
--   • Overlap is minimized; each index targets the specific query pattern.
--   • Total estimated additional storage is roughly 77% of the base table size (~38 GB), which is acceptable given the performance gains for the workload.
