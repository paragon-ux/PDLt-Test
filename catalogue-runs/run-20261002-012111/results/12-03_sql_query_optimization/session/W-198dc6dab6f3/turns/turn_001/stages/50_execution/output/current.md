-- Indexes to improve performance
CREATE INDEX idx_users_created_at_status ON users (created_at, status);
CREATE INDEX idx_users_id ON users (id);
CREATE INDEX idx_orders_user_id_status_total ON orders (user_id, status, total);

-- Rewritten query using the indexes and moving the orders.status filter into the JOIN condition to preserve the LEFT JOIN semantics
SELECT u.name,
       u.email,
       COUNT(o.id) AS order_count,
       SUM(o.total) AS total_spent
FROM users u
LEFT JOIN orders o
       ON o.user_id = u.id
      AND o.status <> 'cancelled'  -- filter applied in the join condition
WHERE u.created_at >= '2025-01-01'
  AND u.status = 'active'
GROUP BY u.id, u.name, u.email
HAVING SUM(o.total) > 1000
ORDER BY total_spent DESC
LIMIT 50;
