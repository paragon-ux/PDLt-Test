**Shard Key Recommendations**

| Table | Recommended Shard Key | Reasoning |
|-------|----------------------|----------|
| users | `id` (primary key) – optionally prefixed with `region` if data‑locality to a specific geographic region is needed | Queries: *Get a user's follower count* (needs only the user row) and *Get a user's timeline* (fetches follower list from `follows` then posts). Using `id` ensures uniform distribution across shards (100M rows) and avoids hotspots. Adding `region` can improve locality for region‑based services but may introduce imbalance if some regions dominate.
| posts | Composite key `author_id` (or `author_id + created_at` for time‑range sharding) | The timeline query fetches posts of users a person follows. Sharding by `author_id` keeps each user's posts on the same shard, allowing the timeline query to retrieve posts for many followees with a single scatter‑gather (one shard per author). Adding `created_at` helps balance write load over time and assists range scans for recent posts.
| likes | `post_id` (or `post_id + user_id` for finer granularity) | *Get all likes on a specific post* becomes a single‑shard query when sharding by `post_id`, eliminating cross‑shard joins for the 50B‑row table. Queries that need likes for a user’s own posts still require a scatter‑gather, but this is acceptable as the primary read pattern is per‑post.
| follows | Composite key `follower_id` (or `follower_id + following_id`) | *Get a user's follower count* and the list of followees required for the timeline query both become local reads when sharding by `follower_id`. This distributes the 2B rows evenly and prevents a single hot shard for very popular users.

**Impact Analysis on Common Queries**

1. **Get a user's timeline** – Requires joins between `follows` (by `follower_id`) and `posts` (by `author_id`). With the chosen keys, `follows` is local to the requesting user, and each author’s posts are on the shard keyed by `author_id`. The query becomes a scatter‑gather across the set of followed authors, but each shard returns only that author’s posts, keeping the amount of data transferred modest. Adding a cache layer can further reduce cross‑shard traffic.
2. **Get all likes on a specific post** – Sharding `likes` by `post_id` makes this a single‑shard lookup, enabling fast, low‑latency retrieval even at 50B rows.
3. **Get a user's follower count** – With `follows` sharded on `follower_id`, counting followers is a local operation on the shard that stores the requesting user’s follow rows.
4. **Full‑text search across posts** – Sharding by `author_id` does not help full‑text search, which will still require a scatter‑gather across all shards (or use an external search index). This is acceptable because search is read‑intensive and can be backed by a replicated search service.

**Trade‑offs**

- **Locality vs. Cross‑shard joins**: The chosen keys maximize locality for the most common read patterns (timeline, likes, follower count) while accepting cross‑shard reads for timeline aggregation across many authors.
- **Load balancing**: Primary keys (`id`, `author_id`, `post_id`, `follower_id`) provide near‑uniform distribution, mitigating hotspot risk. Adding secondary components (e.g., `region` or `created_at`) can fine‑tune balance but may introduce skew if the added field is unevenly distributed.
- **Hotspot risk**: Very popular users or viral posts could concentrate traffic on a subset of shards. Composite sharding (e.g., `author_id + created_at`) spreads writes over time buckets, reducing per‑shard write pressure.
- **Data skew**: Composite keys help avoid skew from uneven region or time distributions. Monitoring shard metrics and re‑balancing shards periodically will be required.
- **Cross‑shard joins**: The timeline query inevitably involves a scatter‑gather across the set of followed authors; this is acceptable given the query’s high latency tolerance and the ability to parallelize fetches.
- **Scalability**: All chosen keys scale horizontally; adding new shards requires moving ranges of the primary key space, which is straightforward for monotonic identifiers.

**Summary**: Use `id` (or `region+id`) for `users`, `author_id` (optionally with `created_at`) for `posts`, `post_id` for `likes`, and `follower_id` for `follows`. This configuration balances locality for the key queries, distributes load evenly, and limits hotspot and skew risks while accepting the necessary scatter‑gather for timeline assembly.
