DESIGN a sharding strategy for the social media application with the listed tables.
FOR the users table (users(id, username, region, created_at, ~100M rows)):
    SELECT a shard key that supports queries for user timeline and region‑based lookups.
    JUSTIFY the choice based on typical query patterns.
FOR the posts table (posts(id, author_id, content, created_at, ~5B rows)):
    SELECT a shard key that enables efficient retrieval of a user timeline and full‑text search.
    JUSTIFY the choice based on query patterns.
FOR the likes table (likes(id, post_id, user_id, created_at, ~50B rows)):
    SELECT a shard key that supports fetching likes for a given post and counting likes per post.
    JUSTIFY the choice based on query patterns.
FOR the follows table (follows(follower_id, following_id, created_at, ~2B rows)):
    SELECT a shard key that facilitates retrieving a follower's list and counting followers for a user.
    JUSTIFY the choice based on query patterns.
ANALYZE which of the above queries become single‑shard versus scatter‑gather under the proposed keys.
DISCUSS tradeoffs of the chosen shard keys, including load balancing, hotspot risk, and cross‑shard joins.
PROVIDE the recommended shard keys and the accompanying justification and analysis as outlined.
