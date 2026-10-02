-- Forward Migration SQL
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

ALTER TABLE orders
    ADD COLUMN shipping_address_id INT,
    ADD CONSTRAINT fk_orders_shipping_address FOREIGN KEY (shipping_address_id) REFERENCES addresses(id);

-- Rollback Migration SQL
ALTER TABLE orders DROP COLUMN shipping_address_id;
DROP TABLE addresses;

-- Backfill Script (Python)
```python
import sqlite3

# Connect to your database (adjust connection string as needed)
conn = sqlite3.connect('your_database.db')
cur = conn.cursor()

# Insert a default address for each existing user
cur.execute('SELECT id FROM users')
user_ids = [row[0] for row in cur.fetchall()]
for uid in user_ids:
    cur.execute('''
        INSERT INTO addresses (user_id, street, city, state, zip, is_primary)
        VALUES (?, '123 Placeholder St', 'Placeholder City', 'XX', '00000', 1)
    ''', (uid,))
    address_id = cur.lastrowid
    # Update orders for this user to reference the newly created address
    cur.execute('''
        UPDATE orders SET shipping_address_id = ? WHERE user_id = ?
    ''', (address_id, uid))

conn.commit()
conn.close()
```

-- Validation Query
SELECT o.id AS order_id, o.shipping_address_id
FROM orders o
LEFT JOIN addresses a ON o.shipping_address_id = a.id
WHERE o.shipping_address_id IS NOT NULL AND a.id IS NULL;
