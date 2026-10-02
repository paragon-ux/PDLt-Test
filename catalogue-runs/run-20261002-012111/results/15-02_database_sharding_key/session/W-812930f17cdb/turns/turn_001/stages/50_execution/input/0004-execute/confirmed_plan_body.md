IDENTIFY candidate shard key fields for each table: users, posts, likes, follows
CONSIDER data volume for each table (users: 100M rows, posts: 5B rows, likes: 50B rows, follows: 2B rows)
ANALYZE impact of each candidate shard key on each common query: Get a user's timeline, Get all likes on a specific post, Get a user's follower count, Full‑text search across posts
EVALUATE trade‑offs for each candidate, including locality versus cross‑shard joins, load balancing, hotspot risk, and data skew
SELECT optimal shard key for each table based on analysis
DOCUMENT recommendation for each table with justification referencing the analysis
