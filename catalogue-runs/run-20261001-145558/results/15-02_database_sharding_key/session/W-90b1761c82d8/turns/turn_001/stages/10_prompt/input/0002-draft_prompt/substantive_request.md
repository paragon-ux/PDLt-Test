TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Design a sharding strategy for a social media application with tables: users(id, username, region, created_at, ~100M rows), posts(id, author_id, content, created_at, ~5B rows), likes(id, post_id, user_id, created_at, ~50B rows), follows(follower_id, following_id, created_at, ~2B rows). Provide recommended shard keys for each table, justify based on query patterns: user timeline, likes on a post, follower count, full-text search across posts. Analyze which queries become single-shard versus scatter-gather and discuss tradeoffs.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- users
- id
- username
- region
- created_at
- posts
- author_id
- content
- likes
- post_id
- user_id
- follows
- follower_id
- following_id
