TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Design and implement a database schema migration to split the users table and support multiple addresses per user. Create forward migration SQL that adds an addresses table with columns (id INT PK, user_id INT FK->users, street TEXT, city TEXT, state TEXT, zip TEXT, is_primary BOOL) and modifies orders table to add shipping_address_id INT FK->addresses. Produce rollback migration SQL to revert these changes. Provide a backfill script that creates a default address for each existing user using placeholder data. Generate a validation query that confirms no orders reference missing addresses after migration.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- users
- id
- orders
- user_id
- addresses
- street
- city
- state
- zip
- is_primary
- shipping_address_id
