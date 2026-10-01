REFactor the monolithic Python class into separate cohesive classes
CREATE a UserRepository class handling user creation, activation/deactivation, and retrieval of active users
CREATE a SessionManager class handling login, logout, session tracking, and cleanup of expired sessions
CREATE an EmailDispatcher class handling email queuing and sending
ENSURE each class encapsulates a single responsibility and exposes clear public methods
INTEGRATE the new classes so that existing workflows (user creation, login, logout, session expiration, email dispatch, deactivation, active‑user listing) invoke them appropriately
WRITE unit tests for UserRepository covering user creation, activation, deactivation, and listing active users
WRITE unit tests for SessionManager covering login, logout, and session expiration handling
WRITE unit tests for EmailDispatcher covering email queuing and sending
RUN all unit tests to verify behavior matches the original implementation
