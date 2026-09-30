TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Design and implement a database schema migration that splits the existing users table to support multiple addresses per user. The migration must (1) create a new addresses table with columns id, user_id, street, city, state, zip, is_primary; (2) add a shipping_address_id foreign key to the orders table referencing addresses; (3) preserve existing users table structure; (4) provide forward migration SQL, rollback migration SQL, a backfill script that inserts a default address for each existing user using placeholder data, and a validation query that ensures no orders reference missing addresses after migration.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- users
- orders
- addresses
- id
- user_id
- shipping_address_id
- street
- city
- state
- zip
- is_primary
- forward migration SQL
- rollback migration SQL
- backfill script
- validation query
