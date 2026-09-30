DESIGN overall sharding architecture for the social media application
IDENTIFY candidate shard keys for each table: users, posts, likes, follows
ANALYZE typical query patterns for each table to determine single‑shard versus scatter‑gather access
SELECT a shard key for users based on query locality and balanced distribution
SELECT a shard key for posts that maximizes single‑shard reads for feed and post retrieval
SELECT a shard key for likes that aligns with the post shard key to reduce cross‑shard joins
SELECT a shard key for follows that supports efficient follower/following lookups
JUSTIFY each shard key by mapping common queries to their shard locality outcomes
IDENTIFY trade‑offs for each shard key, including data distribution uniformity, hotspot potential, cross‑shard join cost, and operational complexity
DOCUMENT the sharding strategy, shard key recommendations, justifications, and trade‑off analysis
