TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Design and implement a database schema migration that splits the existing users table to support multiple addresses per user. The migration must create a new addresses table with fields (id INT PK, user_id INT FK->users, street TEXT, city TEXT, state TEXT, zip TEXT, is_primary BOOL), add a shipping_address_id INT FK->addresses column to orders, and preserve existing users and orders data. Provide (1) the forward migration SQL to create the addresses table, add the new column, and adjust constraints; (2) the rollback migration SQL to revert these changes; (3) a backfill script that creates a default address for each existing user using placeholder data; and (4) a validation query that confirms no orders reference missing addresses after migration.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- users
- orders
- addresses
- id
- INT
- PK
- TEXT
- user_id
- FK->users
- shipping_address_id
- FK->addresses
- is_primary
- BOOL
- forward migration SQL
- rollback migration SQL
- backfill script
- placeholder data
- validation query

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: PK; FK->users; FK->addresses; forward migration SQL; rollback migration SQL
