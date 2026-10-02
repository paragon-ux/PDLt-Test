DETERMINE the schema modifications needed for the forward migration
GENERATE forward migration SQL to create the addresses table with columns id, user_id, street, city, state, zip, is_primary and appropriate primary and foreign key constraints
GENERATE forward migration SQL to alter the orders table by adding the shipping_address_id column with a foreign key constraint to addresses
GENERATE rollback migration SQL to drop the shipping_address_id column from the orders table
GENERATE rollback migration SQL to drop the addresses table
GENERATE backfill script to insert a default address for each existing user using placeholder values for street, city, state, zip and setting is_primary to TRUE
GENERATE backfill script to update each order to set shipping_address_id to the address inserted for its user_id
GENERATE validation query to verify that every order's shipping_address_id references an existing address and that no missing address references exist
OUTPUT the forward migration SQL, rollback migration SQL, backfill script, and validation query as separate artifacts
