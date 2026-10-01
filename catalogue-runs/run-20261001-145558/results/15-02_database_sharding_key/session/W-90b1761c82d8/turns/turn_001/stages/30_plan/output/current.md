SELECT shard key for users table that supports timeline and region lookups
JUSTIFY the chosen key based on typical query patterns for user timeline and region‑based queries
SELECT shard key for posts table that enables efficient retrieval of a user timeline and full‑text search
JUSTIFY the chosen key based on query patterns for timeline ordering and text search
SELECT shard key for likes table that supports fetching likes for a given post and counting likes per post
JUSTIFY the chosen key based on typical read‑heavy queries for likes retrieval and aggregation
SELECT shard key for follows table that facilitates retrieving a follower's list and counting followers for a user
JUSTIFY the chosen key based on follow‑list and follower‑count queries
ANALYZE which queries become single‑shard versus scatter‑gather under each proposed key
DISCUSS tradeoffs of the chosen shard keys, including load balancing, hotspot risk, and cross‑shard join implications
PROVIDE the recommended shard keys together with their justifications and the analysis results
