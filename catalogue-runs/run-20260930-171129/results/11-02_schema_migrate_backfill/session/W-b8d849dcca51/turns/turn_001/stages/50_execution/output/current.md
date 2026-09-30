-- Forward Migration SQL
CREATE TABLE addresses (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id),
    street TEXT NOT NULL,
    city TEXT NOT NULL,
    state TEXT NOT NULL,
    zip TEXT NOT NULL,
    is_primary BOOLEAN NOT NULL DEFAULT TRUE
);

-- Create indexes for performance
CREATE INDEX idx_addresses_user_id ON addresses(user_id);

-- Alter orders to add shipping_address_id column
ALTER TABLE orders
    ADD COLUMN shipping_address_id INT,
    ADD CONSTRAINT fk_orders_shipping_address FOREIGN KEY (shipping_address_id) REFERENCES addresses(id);

-- Index on the new foreign key
CREATE INDEX idx_orders_shipping_address_id ON orders(shipping_address_id);

-- Rollback Migration SQL
-- Drop foreign key and column from orders
ALTER TABLE orders
    DROP CONSTRAINT IF EXISTS fk_orders_shipping_address,
    DROP COLUMN IF EXISTS shipping_address_id;

-- Drop addresses table (will cascade drop dependent constraints)
DROP TABLE IF EXISTS addresses;

-- Backfill Script (Python)
import psycopg2

PLACEHOLDER_STREET = '123 Placeholder St.'
PLACEHOLDER_CITY   = 'Placeholder City'
PLACEHOLDER_STATE  = 'PS'
PLACEHOLDER_ZIP    = '00000'

conn = psycopg2.connect("dbname=yourdb user=youruser password=yourpass host=yourhost")
conn.autocommit = False
cur = conn.cursor()
try:
    # Insert a default address for every user
    cur.execute("""
        INSERT INTO addresses (user_id, street, city, state, zip, is_primary)
        SELECT id, %s, %s, %s, %s, TRUE
        FROM users
        RETURNING id, user_id;
    """, (PLACEHOLDER_STREET, PLACEHOLDER_CITY, PLACEHOLDER_STATE, PLACEHOLDER_ZIP))
    address_rows = cur.fetchall()  # [(address_id, user_id), ...]

    # Map user_id -> address_id
    user_to_address = {user_id: addr_id for addr_id, user_id in address_rows}

    # Update orders to reference the newly created address where shipping_address_id is NULL
    for user_id, addr_id in user_to_address.items():
        cur.execute(
            "UPDATE orders SET shipping_address_id = %s WHERE user_id = %s AND shipping_address_id IS NULL",
            (addr_id, user_id)
        )
    conn.commit()
finally:
    cur.close()
    conn.close()

-- Validation Query
SELECT o.id AS order_id, o.shipping_address_id
FROM orders o
LEFT JOIN addresses a ON o.shipping_address_id = a.id
WHERE o.shipping_address_id IS NOT NULL AND a.id IS NULL;
