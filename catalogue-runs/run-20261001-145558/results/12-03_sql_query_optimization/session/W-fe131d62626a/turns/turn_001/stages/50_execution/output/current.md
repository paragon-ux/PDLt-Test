-- Revised query for better performance
SELECT u.name,
       u.email,
       COUNT(o.id)        AS order_count,
       SUM(o.total)       AS total_spent
FROM   users u
LEFT JOIN orders o
       ON o.user_id = u.id
          AND o.status <> 'cancelled'   -- move condition into join to preserve LEFT semantics
WHERE  u.created_at >= DATE '2025-01-01'
  AND  u.status = 'active'
GROUP BY u.id, u.name, u.email
HAVING SUM(o.total) > 1000
ORDER BY total_spent DESC
LIMIT 50;

-- Indexing strategy
-- 1. Index on orders(user_id, status, total) to support join, filter, and aggregation
CREATE INDEX idx_orders_userid_status_total ON orders(user_id, status, total);

-- 2. Index on users(created_at, status, id) to support the WHERE clause and grouping
CREATE INDEX idx_users_createdat_status_id ON users(created_at, status, id);

-- 3. Optional covering index for the SELECT list (if the query project frequently needs name/email)
CREATE INDEX idx_users_id_name_email ON users(id, name, email);

-- Explanation:
-- * The join predicate `o.status <> 'cancelled'` is moved from the WHERE clause into the LEFT JOIN condition. This preserves rows from `users` even when there is no matching order, while still eliminating cancelled orders from the aggregation.
-- * The `orders` index starts with `user_id` (the join column) followed by `status` (the filter) and `total` (used in SUM and HAVING). This allows the planner to use an index‑only scan for the join and aggregation when possible.
-- * The `users` index begins with `created_at` (range filter) and `status` (equality filter), then includes `id` to aid the GROUP BY. Including `name` and `email` in a covering index can make the query an index‑only scan, avoiding a heap fetch.
-- * With these indexes the planner is likely to choose an Index Scan on both tables rather than a Sequential Scan, because the predicates are highly selective and the indexes cover the needed columns.
-- * The LEFT JOIN interacts with the WHERE clause by filtering `orders` rows inside the join condition; rows from `users` without any non‑cancelled orders still appear with NULLs for `o` columns, satisfying the LEFT semantics.
