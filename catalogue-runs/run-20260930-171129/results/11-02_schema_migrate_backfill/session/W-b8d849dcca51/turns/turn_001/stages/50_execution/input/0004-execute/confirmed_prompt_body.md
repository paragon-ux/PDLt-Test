CREATE a new table called addresses with columns id, user_id, street, city, state, zip, is_primary;
ALTER the orders table to add a column shipping_address_id that references addresses(id) as a foreign key;
KEEP the existing users table unchanged;
PROVIDE forward migration SQL that creates the addresses table, adds the shipping_address_id column to orders, and sets up necessary indexes and constraints;
PROVIDE rollback migration SQL that drops the shipping_address_id column from orders and drops the addresses table;
WRITE a backfill script that inserts a default address record for each existing user using placeholder values for street, city, state, zip, and sets is_primary true, then updates orders to reference the newly created address as shipping_address_id where applicable;
GENERATE a validation query that checks that every orders.shipping_address_id references an existing addresses.id and reports any orders with missing references.
