-- Revised query for better performance
-- Using inner join for orders after filtering cancelled status in a subquery to preserve LEFT JOIN semantics where needed
WITH filtered_orders AS (
    SELECT *
    FROM orders
    WHERE status <> 'cancelled'
)
SELECT u.name,
       u.email,
       COUNT(o.id)         AS order_count,
       SUM(o.total)        AS total_spent
FROM   users u
       LEFT JOIN filtered_orders o ON o.user_id = u.id
WHERE  u.created_at >= '2025-01-01'
  AND  u.status = 'active'
GROUP  BY u.id, u.name, u.email
HAVING SUM(o.total) > 1000
ORDER  BY total_spent DESC
LIMIT  50;

-- Indexing strategy
-- 1. On users(created_at, status) to satisfy the WHERE clause and enable index-only scan for the user filter.
CREATE INDEX idx_users_created_status ON users (created_at, status);
-- 2. On orders(user_id, status, total) to support the join, the status filter inside the CTE, and the HAVING aggregation.
CREATE INDEX idx_orders_user_status_total ON orders (user_id, status, total);
-- 3. Optionally, covering index on orders(id) if not already primary key.

-- Expected plan
-- The optimizer can use an index scan on idx_users_created_status to locate active users created after the date, then an index scan on idx_orders_user_status_total for matching orders, avoiding a sequential scan on both large tables.

-- Interaction of LEFT JOIN with o.status filter
-- By moving the o.status <> 'cancelled' condition into the CTE (or into the ON clause), we preserve rows from users that have no orders, while still excluding cancelled orders from the aggregation. This prevents the LEFT JOIN from being turned into an inner join unintentionally.
