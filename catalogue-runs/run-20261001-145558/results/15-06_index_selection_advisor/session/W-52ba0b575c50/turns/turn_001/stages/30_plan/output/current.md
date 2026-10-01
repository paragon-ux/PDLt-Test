READ the schema of the events table with columns id, user_id, event_type, payload, created_at, processed.
READ the workload of queries Q1 through Q5 and their frequencies.
ANALYZE the predicates and ordering in Q1‑Q5 to identify candidate index columns, expressions, and partial conditions.
SELECT an optimal set of indexes that together serve the queries while minimizing overlap and cost.
FOR each recommended index:
  WRITE the exact CREATE INDEX statement, including any expression or partial specifications as needed.
  NOTE which of the queries Q1‑Q5 each index serves.
  ESTIMATE the space overhead of the index.
