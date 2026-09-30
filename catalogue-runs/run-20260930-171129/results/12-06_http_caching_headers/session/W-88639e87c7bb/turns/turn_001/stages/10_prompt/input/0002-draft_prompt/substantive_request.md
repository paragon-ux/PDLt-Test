TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Design a cache-control header strategy for a CDN-backed REST API covering five resource types: (1) static assets that change only on deploy, (2) user profile data that changes at most once per day, (3) real-time data that must never be stale, (4) public catalog data identical for all users, and (5) authenticated responses that vary per user. For each type, specify the exact Cache-Control, Vary, ETag, and Surrogate-Control header values and explain the rationale. Additionally, provide a Python middleware function that inspects the response type and sets the appropriate headers.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Cache-Control
- Vary
- ETag
- Surrogate-Control
- Python
- middleware
