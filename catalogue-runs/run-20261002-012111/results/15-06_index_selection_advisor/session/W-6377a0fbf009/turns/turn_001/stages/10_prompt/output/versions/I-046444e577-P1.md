TASK ENTITIES: events, id, user_id, event_type, payload, created_at, processed, BIGINT, INT, TEXT, JSONB, TIMESTAMP, BOOLEAN, {\"key\": \"value\"}
TABLE DEFINITION: events (id BIGINT PK, user_id INT, event_type TEXT, payload JSONB, created_at TIMESTAMP, processed BOOLEAN)
QUERY WORKLOAD: Q1 (40%): SELECT * FROM events WHERE user_id = ? AND created_at > ? ORDER BY created_at DESC LIMIT 50
QUERY WORKLOAD: Q2 (30%): SELECT * FROM events WHERE event_type = ? AND processed = false ORDER BY created_at ASC LIMIT 100
QUERY WORKLOAD: Q3 (15%): SELECT user_id, COUNT(*) FROM events WHERE created_at BETWEEN ? AND ? GROUP BY user_id HAVING COUNT(*) > 10
QUERY WORKLOAD: Q4 (10%): SELECT * FROM events WHERE payload @> '{\"key\": \"value\"}'
QUERY WORKLOAD: Q5 (5%): SELECT * FROM events WHERE id = ?
RECOMMEND optimal set of PostgreSQL indexes for the table events based on the query workload
FOR EACH recommended index, PROVIDE the exact CREATE INDEX statement
FOR EACH recommended index, EXPLAIN which queries it serves
FOR EACH recommended index, ESTIMATE the space overhead
