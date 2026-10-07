Create an index on every column:
CREATE INDEX ON events (user_id);
CREATE INDEX ON events (event_type);
CREATE INDEX ON events (created_at);
CREATE INDEX ON events (processed);
CREATE INDEX ON events (payload);
CREATE INDEX ON events (id);
Each index is about 50 MB.
