TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Refactor the provided Python class UserManager into at least three cohesive classes, each with a single responsibility, while preserving all existing behavior. The original class handles user persistence via the db_path file, stores user records in the users dictionary, manages active sessions in the sessions dictionary, and queues emails in the email_queue list. It provides methods create_user, login, logout, get_user, send_emails, deactivate_user, list_active_users, and cleanup_sessions (default max_age 3600 seconds). Refactoring must retain the same validation checks that raise errors with messages "User exists", "Invalid email", and "Password too short", use the same hashing approach with hashlib.sha256 and a salt derived from the username, and maintain session creation using uuid.uuid4() and timestamps. Additionally, include unit tests that verify all original functionalities continue to work after the refactoring.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- UserManager
- db_path
- users
- sessions
- email_queue
- create_user
- username
- email
- User exists
- Invalid email
- Password too short
- salt
- active
- login
- hashlib.sha256
- uuid
- time
- logout
- get_user
- send_emails
- deactivate_user
- list_active_users
- cleanup_sessions
- max_age
- 3600
