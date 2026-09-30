GENERATE forward migration SQL including CREATE TABLE addresses and ALTER TABLE orders with foreign key constraints
GENERATE rollback migration SQL that drops shipping_address_id from orders and drops addresses table
WRITE backfill script that inserts a default address for each existing user and updates orders to reference the new address
CREATE validation query that checks for orders with shipping_address_id referencing non‑existent addresses
EMIT all generated SQL statements, the backfill script, and the validation query as separate output sections
