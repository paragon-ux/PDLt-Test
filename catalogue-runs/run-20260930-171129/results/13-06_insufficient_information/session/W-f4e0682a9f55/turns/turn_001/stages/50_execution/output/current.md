-- Optimized query version
SELECT column1, column2, column3
FROM my_table
WHERE (filter_condition) -- Apply selective filters
-- Ensure appropriate indexes exist on filter_condition columns
-- Added explicit column list and filter predicates for better index usage
-- Consider covering index to avoid extra lookups
-- This formulation is intended to replace the original SELECT * FROM ???
