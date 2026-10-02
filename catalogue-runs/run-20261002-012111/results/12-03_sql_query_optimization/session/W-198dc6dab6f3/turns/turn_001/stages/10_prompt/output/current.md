REWRITE the SQL query that selects u.name, u.email, COUNT(o.id) as order_count, SUM(o.total) as total_spent from users u LEFT JOIN orders o ON o.user_id = u.id, with filters u.created_at >= 2025-01-01, u.status = active, o.status != cancelled, grouping by u.id, u.name, u.email, having SUM(o.total) > 1000, ordering by total_spent descending, limiting to 50 rows, to improve performance.
IDENTIFY appropriate indexes for the users and orders tables.
DETERMINE whether the query plan likely uses a sequential scan or an index scan.
EXPLAIN how the LEFT JOIN interacts with the WHERE clause on o.status.
PROVIDE the corrected query together with CREATE INDEX statements.
