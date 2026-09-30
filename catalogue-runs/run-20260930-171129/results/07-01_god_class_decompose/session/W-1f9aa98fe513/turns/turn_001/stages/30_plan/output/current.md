DECOMPOSE the UserManager class into at least three cohesive classes each with a single responsibility while preserving all existing behavior
IDENTIFY distinct responsibilities among user storage, session management, email queuing, user creation, authentication, deactivation, listing active users, and session cleanup
GROUP related responsibilities into separate classes (e.g., UserRepository, SessionService, EmailQueue)
EXTRACT methods and fields related to each responsibility from UserManager into the appropriate new class
UPDATE each new class to encapsulate its behavior and expose a clear public interface
REFactor UserManager to coordinate the new classes, delegating calls to them
ENSURE that all original public methods of UserManager still invoke the appropriate delegated functionality
WRITE unit tests that cover the original behaviors (user storage, session management, email queuing, user creation, authentication, deactivation, listing active users, session cleanup) using the refactored design
RUN the test suite to verify that all tests pass and behavior is unchanged
