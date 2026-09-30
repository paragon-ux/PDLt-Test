PARSE the supplied Node.js-style callback code
TRANSLATE each callback-based fetch into an async function in Python preserving logical flow and error handling
IMPLEMENT async fetch_user function that performs the user request and raises on error
IMPLEMENT async fetch_organization function that performs the organization request and raises on error
IMPLEMENT async fetch_permissions function that performs the permissions request and raises on error
COMPOSE async get_user_context function that concurrently invokes fetch_user, fetch_organization, and fetch_permissions, aggregates results, and propagates any raised errors
WRITE unit tests using asyncio test utilities
EXECUTE a success‑path test where all three fetch functions return expected data and verify the combined result
EXECUTE an error‑propagation test where fetch_user raises an exception and verify that get_user_context propagates the error
EXECUTE an error‑propagation test where fetch_organization raises an exception and verify propagation
EXECUTE an error‑propagation test where fetch_permissions raises an exception and verify propagation
