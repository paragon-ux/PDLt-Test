TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Design a sharding strategy for a social media application with tables: users (id, username, region, created_at), posts (id, author_id, content, created_at), likes (id, post_id, user_id, created_at), follows (follower_id, following_id, created_at). Recommend a shard key for each table, justify choices by analyzing which common queries become single‑shard versus scatter‑gather, and identify trade‑offs.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- users
- posts
- likes
- follows
