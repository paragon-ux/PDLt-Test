ANALYZE the existing UserManager class to enumerate its responsibilities.
IDENTIFY separate responsibilities for user persistence, session handling, and email queue management.
DEFINE three cohesive classes, each with a single responsibility corresponding to the identified responsibilities.
REFRACTOR the user persistence code into the first new class.
REFRACTOR the session handling code into the second new class.
REFRACTOR the email queue code into the third new class.
UPDATE all references to use the new classes while preserving original behavior.
CREATE unit tests for each new class that verify functional equivalence to the original UserManager behavior.
CREATE integration tests that verify user creation, login, logout, retrieval, deactivation, listing active users, session cleanup, and email sending.
RUN the complete test suite to validate that all functionalities operate correctly after refactoring.
