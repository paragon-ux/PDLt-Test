READ the schema of table events with columns id BIGINT PK, user_id INT, event_type TEXT, payload JSONB, created_at TIMESTAMP, processed BOOLEAN.
READ the workload of queries Q1 through Q5 with their frequencies.
RECOMMEND an optimal set of indexes for the events table.
FOR each recommended index:
  WRITE the exact CREATE INDEX statement, including any partial or expression specifications where appropriate.
  EXPLAIN which of the queries Q1‑Q5 each index serves.
  ESTIMATE the space overhead of the index.
INCLUDE the operative task entities exactly as listed: events, id, user_id, event_type, payload, created_at, processed, Q1, Q5.
