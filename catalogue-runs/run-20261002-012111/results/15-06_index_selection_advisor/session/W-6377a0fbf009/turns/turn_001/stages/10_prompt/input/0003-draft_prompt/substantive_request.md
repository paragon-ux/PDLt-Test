TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Recommend an optimal set of PostgreSQL indexes for the table events (id BIGINT PK, user_id INT, event_type TEXT, payload JSONB, created_at TIMESTAMP, processed BOOLEAN) based on the given query workload: Q1 (40%): SELECT * FROM events WHERE user_id = ? AND created_at > ? ORDER BY created_at DESC LIMIT 50; Q2 (30%): SELECT * FROM events WHERE event_type = ? AND processed = false ORDER BY created_at ASC LIMIT 100; Q3 (15%): SELECT user_id, COUNT(*) FROM events WHERE created_at BETWEEN ? AND ? GROUP BY user_id HAVING COUNT(*) > 10; Q4 (10%): SELECT * FROM events WHERE payload @> '{"key": "value"}'; Q5 (5%): SELECT * FROM events WHERE id = ?. For each recommended index, provide the exact CREATE INDEX statement (including partial or expression indexes if appropriate), explain which queries it serves, and estimate the space overhead.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- events
- id
- user_id
- event_type
- payload
- created_at
- processed
- BIGINT
- INT
- TEXT
- JSONB
- TIMESTAMP
- BOOLEAN
- {"key": "value"}
