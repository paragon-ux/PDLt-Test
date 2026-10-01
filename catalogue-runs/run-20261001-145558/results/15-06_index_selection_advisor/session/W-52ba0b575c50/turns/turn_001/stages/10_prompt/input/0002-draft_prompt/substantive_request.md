TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Recommend an optimal index set for a PostgreSQL table 'events' with columns id BIGINT PK, user_id INT, event_type TEXT, payload JSONB, created_at TIMESTAMP, processed BOOLEAN and a workload of five queries (Q1‑Q5) with given frequencies. For each recommended index, provide the exact CREATE INDEX statement (including partial or expression indexes where appropriate), explain which queries it serves, and estimate the space overhead.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- events
- id
- user_id
- event_type
- payload
- created_at
- processed
- Q1
- Q5
