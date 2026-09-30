-- Forward Migration
CREATE TABLE addresses (
    id INT PRIMARY KEY,
    user_id INT NOT NULL,
    street TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    is_primary BOOL,
    CONSTRAINT fk_addresses_user FOREIGN KEY (user_id) REFERENCES users(id)
);

ALTER TABLE orders ADD COLUMN shipping_address_id INT;
ALTER TABLE orders ADD CONSTRAINT fk_orders_shipping_address FOREIGN KEY (shipping_address_id) REFERENCES addresses(id);

-- Rollback Migration
ALTER TABLE orders DROP CONSTRAINT IF EXISTS fk_orders_shipping_address;
ALTER TABLE orders DROP COLUMN IF EXISTS shipping_address_id;
DROP TABLE IF EXISTS addresses;

-- Backfill Script (Python)
import psycopg2

conn = psycopg2.connect("dbname=yourdb user=youruser password=yourpass host=localhost")
cur = conn.cursor()

# Insert a default address for each user
cur.execute("""
INSERT INTO addresses (user_id, street, city, state, zip, is_primary)
SELECT id, '123 Placeholder St', 'Placeholder City', 'PC', '00000', TRUE
FROM users;
""")

# Update orders to reference the newly created address (assumes one address per user)
cur.execute("""
UPDATE orders o
SET shipping_address_id = a.id
FROM addresses a
WHERE o.user_id = a.user_id AND a.is_primary = TRUE;
""")

conn.commit()
cur.close()
conn.close()

-- Validation Query
SELECT COUNT(*) AS orphan_order_count
FROM orders o
LEFT JOIN addresses a ON o.shipping_address_id = a.id
WHERE o.shipping_address_id IS NOT NULL AND a.id IS NULL;
