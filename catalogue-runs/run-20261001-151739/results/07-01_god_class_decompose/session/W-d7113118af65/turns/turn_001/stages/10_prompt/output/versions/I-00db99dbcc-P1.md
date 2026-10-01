READ the description of the original class UserManager and its components db_path, users, sessions, email_queue.
IDENTIFY the methods create_user, login, logout, get_user, send_emails, deactivate_user, list_active_users, cleanup_sessions and the validation messages "User exists", "Invalid email", "Password too short".
IDENTIFY the email argument used by create_user.
REFRACTOR the code into at least three cohesive classes, each with a single responsibility, preserving all behavior.
ENSURE the validation checks raise errors with messages "User exists", "Invalid email", "Password too short".
ENSURE password hashing uses hashlib.sha256 with a salt derived from the username (salt).
ENSURE session creation uses uuid.uuid4() with timestamps from time and tracks active sessions.
ENSURE persistence continues to use the db_path file.
ENSURE the email_queue handling is preserved.
INCLUDE unit tests that verify the functionality of create_user, login, logout, get_user, send_emails, deactivate_user, list_active_users, cleanup_sessions with max_age of 3600 seconds.
