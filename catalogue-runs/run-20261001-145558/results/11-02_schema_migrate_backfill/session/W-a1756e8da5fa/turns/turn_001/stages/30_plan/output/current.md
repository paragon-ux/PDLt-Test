DESIGN a migration to split the users table and support multiple addresses per user
CREATE a forward migration SQL that adds an addresses table with columns (id INT PRIMARY KEY, user_id INT FOREIGN KEY REFERENCES users(id), street TEXT, city TEXT, state TEXT, zip TEXT, is_primary BOOL)
MODIFY the orders table to add a shipping_address_id INT FOREIGN KEY REFERENCES addresses(id)
GENERATE a rollback migration SQL that drops the shipping_address_id column from orders and drops the addresses table
WRITE a backfill script that inserts a default address for each existing user using placeholder data for street, city, state, zip, and sets is_primary to TRUE
UPDATE orders to reference the newly created address as shipping_address_id
GENERATE a validation query that confirms no orders reference missing addresses after migration
