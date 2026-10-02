TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Design a cache-control header strategy for a CDN-backed REST API covering five resource types: (1) static assets (JS, CSS, images) that change only on deploy; (2) user profile data that changes rarely (at most once per day); (3) real-time data (stock prices, live scores) that must never be stale; (4) public catalog data that is the same for all users; and (5) authenticated responses that vary by user. For each resource type, specify the exact Cache-Control, Vary, ETag, and Surrogate-Control header values and explain the rationale for each directive. Additionally, implement a Python middleware function that sets the appropriate headers based on the response type.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Cache-Control
- Vary
- ETag
- Surrogate-Control
