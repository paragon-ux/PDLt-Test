CONVERT the provided Node.js-style callback code into clean async/await Python preserving the exact logical flow and error handling.
IMPLEMENT async functions for fetching a user, fetching an organization, and fetching permissions.
COMPOSE these functions into an async get_user_context function that returns a combined result or propagates errors.
INCLUDE unit tests that verify the success path where all fetches succeed.
INCLUDE unit tests that verify error propagation for each failure scenario: user fetch error, organization fetch error, permissions fetch error.
USE asyncio test utilities for the unit tests.
