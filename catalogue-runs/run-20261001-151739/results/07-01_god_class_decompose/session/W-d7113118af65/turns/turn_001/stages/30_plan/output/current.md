READ the description of the original UserManager class and its components
IDENTIFY the listed methods: create_user, login, logout, get_user, send_emails, deactivate_user, list_active_users, cleanup_sessions
EXTRACT the validation messages "User exists", "Invalid email", "Password too short"
EXTRACT the email argument used by create_user
DESIGN at least three cohesive classes, each with a single responsibility, to host the refactored functionality
MAP each original method to the appropriate new class based based on its responsibility
INTEGRATE password hashing using hashlib.sha256 with a salt derived from the username within the authentication logic
INTEGRATE session creation using uuid.uuid4() with timestamps from time, and track active sessions in a session-management component
PRESERVE persistence using the db_path file within the repository component
PRESERVE email_queue handling within the email-dispatcher component
ENSURE validation checks raise errors with messages "User exists", "Invalid email", "Password too short"
ENSURE all original behavior is retained across the new class structure
WRITE unit tests that verify create_user, login, logout, get_user, send_emails, deactivate_user, list_active_users, and cleanup_sessions with a max_age of 3600 seconds
VALIDATE that the unit test suite passes against the refactored implementation
