| Table | Shard key | Why |
|---|---|---|
| users (100M) | id | point lookups by user; co-locates with the user's posts |
| posts (5B) | author_id | a user's own posts and profile pages are single-shard |
| likes (50B) | post_id | "all likes on a post" is single-shard; likes are co-located with nothing else, but that query dominates |
| follows (2B) | follower_id, plus a copy keyed by following_id | "who do I follow" (timeline) and "who follows X" (counts, notifications) are both single-shard |

Queries:
1. **Timeline:** scatter-gather under author sharding (followed authors live on many shards). Mitigation: fan-out on write: when a user posts, push the post id into each follower's timeline (a timeline store keyed by follower); for accounts with millions of followers, pull their posts at read time and merge (hybrid).
2. **Likes on a post:** single-shard (post_id).
3. **Follower count:** single-shard using the following_id copy, or better a denormalized counter on the user row, updated on follow/unfollow.
4. **Full-text search:** not served by the shards: index posts into Elasticsearch/OpenSearch asynchronously.

Tradeoffs: celebrity users create hot shards (posts by author, likes on viral posts): split hot keys or add caching. Duplicated follows doubles writes and needs reconciliation. Fan-out on write amplifies writes and complicates deletes. Resharding needs consistent hashing or a directory service. Cross-shard operations (deleting a user's likes) are not transactional.
