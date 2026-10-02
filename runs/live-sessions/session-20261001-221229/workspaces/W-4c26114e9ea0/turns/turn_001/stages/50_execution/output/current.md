-- Optimized query and indexing strategy

/*
Explanation:
- The original query filters on users.created_at and users.status, and joins orders with a condition on o.status != 'cancelled'.
- To avoid a sequential scan on the large `users` table, create a composite index covering the filter columns and the joined column.
- For the `orders` table, an index on (user_id, status) allows the LEFT JOIN to efficiently locate matching orders while applying the `status != 'cancelled'` condition.
- The HAVING clause filters aggregated totals, which cannot be indexed directly, but the preceding indexes reduce the row set dramatically.
- The rewritten query moves the `o.status != 'cancelled'` condition into the JOIN ON clause, preserving semantics of the LEFT JOIN while allowing the optimizer to use the index on orders.
*/

-- Create indexes
CREATE INDEX idx_users_created_status ON users (created_at, status);
CREATE INDEX idx_orders_user_status ON orders (user_id, status);

-- Rewritten query
SELECT u.name,
       u.email,
       COUNT(o.id) AS order_count,
       SUM(o.total) AS total_spent
FROM users u
LEFT JOIN orders o
       ON o.user_id = u.id
      AND o.status != 'cancelled'
WHERE u.created_at >= '2025-01-01'
  AND u.status = 'active'
GROUP BY u.id, u.name, u.email
HAVING SUM(o.total) > 1000
ORDER BY total_spent DESC
LIMIT 50;
