Design and implement a database schema migration for the following change:

Current schema:
  users(id INT PK, name TEXT, email TEXT, created_at TIMESTAMP)
  orders(id INT PK, user_id INT FK->users, total DECIMAL, status TEXT, created_at TIMESTAMP)

Required change: Split the users table to support multiple addresses per user.
  users(id INT PK, name TEXT, email TEXT, created_at TIMESTAMP)
  addresses(id INT PK, user_id INT FK->users, street TEXT, city TEXT, state TEXT, zip TEXT, is_primary BOOL)
  orders(id INT PK, user_id INT FK->users, shipping_address_id INT FK->addresses, total DECIMAL, status TEXT, created_at TIMESTAMP)

Produce: (1) the forward migration SQL, (2) the rollback migration SQL, (3) a backfill script that creates a default address for existing users using placeholder data, and (4) a validation query that confirms no orders reference missing addresses after migration.
