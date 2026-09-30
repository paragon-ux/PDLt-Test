TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Convert the provided Node.js-style callback code into clean async/await Python. Preserve the exact logical flow and error handling. Implement async functions for fetching a user, fetching an organization, and fetching permissions, then compose them into an async get_user_context function that returns a combined result or propagates errors. Include unit tests that verify the success path (all fetches succeed) and error propagation for each failure scenario (user fetch error, organization fetch error, permissions fetch error). The tests should use asyncio test utilities.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- get_user_context
- await
- asyncio
