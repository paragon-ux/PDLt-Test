RECOMMEND a shard key for each of the tables: users, posts, likes, follows.
JUSTIFY each recommendation by analyzing impact on the following common queries: Get a user's timeline, Get all likes on a specific post, Get a user's follower count, Full-text search across posts.
IDENTIFY trade‑offs such as locality versus cross‑shard joins, load balancing, hotspot risk, and data skew.
INCLUDE the following task entities verbatim: users; posts; likes; follows; id; username; region; created_at; author_id; content; post_id; user_id; follower_id; following_id; Get a user's timeline; Get all likes on a specific post; Get a user's follower count; shard key; 100M rows; 5B rows; 50B rows; 2B rows.
