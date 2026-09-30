CREATE a new table named addresses with columns id INT PK, user_id INT FK->users, street TEXT, city TEXT, state TEXT, zip TEXT, is_primary BOOL.
ADD a column shipping_address_id INT FK->addresses to the orders table.
GENERATE forward migration SQL that includes the CREATE TABLE statement for addresses, the ALTER TABLE statement for orders, and any necessary constraint definitions.
GENERATE rollback migration SQL that drops the shipping_address_id column from orders and drops the addresses table, restoring original schema.
WRITE a backfill script that inserts a default address record for each existing user using placeholder data for street, city, state, zip, and sets is_primary to TRUE, then updates each order to reference the newly created address via shipping_address_id.
CREATE a validation query that confirms no orders have a shipping_address_id value referencing a non‑existent address record after migration.
PROVIDE all generated SQL statements, the backfill script, and the validation query as separate output sections.
