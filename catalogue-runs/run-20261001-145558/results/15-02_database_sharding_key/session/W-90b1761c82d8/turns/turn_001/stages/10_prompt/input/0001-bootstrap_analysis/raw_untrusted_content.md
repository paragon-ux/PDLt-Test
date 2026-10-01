You are designing a sharding strategy for a social media application with the following tables:
- users (100M rows): id, username, region, created_at
- posts (5B rows): id, author_id, content, created_at
- likes (50B rows): id, post_id, user_id, created_at
- follows (2B rows): follower_id, following_id, created_at

Common queries:
1. Get a user's timeline (posts from people they follow, ordered by time)
2. Get all likes on a specific post
3. Get a user's follower count
4. Full-text search across posts

Recommend a shard key for each table. Justify your choice by analyzing which queries become local (single-shard) vs. scatter-gather (cross-shard). Identify the tradeoffs.
