PRODUCE forward migration SQL that:
  CREATE a new table addresses with columns id INT PK, user_id INT FK->users, street TEXT, city TEXT, state TEXT, zip TEXT, is_primary BOOL
  ALTER the orders table to ADD COLUMN shipping_address_id INT FK->addresses
  KEEP the existing users table with columns id INT PK, name TEXT, email TEXT, created_at TIMESTAMP
  KEEP the existing orders table with columns id INT PK, user_id INT FK->users, total DECIMAL, status TEXT, created_at TIMESTAMP
PRODUCE rollback migration SQL that:
  DROP column shipping_address_id from the orders table
  DROP the addresses table
PRODUCE backfill script that:
  INSERT a default address for each existing user into the addresses table using placeholder data for street, city, state, zip, and set is_primary TRUE
  UPDATE each order to set shipping_address_id to the newly inserted address for its user_id
PRODUCE validation query that:
  CHECK that every order's shipping_address_id references an existing address in the addresses table
  ENSURE no missing address references are found after migration
