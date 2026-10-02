TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Recommend a shard key for each table—users (id, username, region, created_at, 100M rows), posts (id, author_id, content, created_at, 5B rows), likes (id, post_id, user_id, created_at, 50B rows), follows (follower_id, following_id, created_at, 2B rows). For each recommendation, justify it by analyzing the impact on the common queries: (1) Get a user's timeline (posts from people they follow, ordered by time), (2) Get all likes on a specific post, (3) Get a user's follower count, and (4) Full‑text search across posts. Identify trade‑offs such as locality versus cross‑shard joins, load balancing, hotspot risk, and data skew.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- users
- posts
- likes
- follows
- id
- username
- region
- created_at
- author_id
- content
- post_id
- user_id
- follower_id
- following_id
- Get a user's timeline
- Get all likes on a specific post
- Get a user's follower count
- shard key
- 100M rows
- 5B rows
- 50B rows
- 2B rows
