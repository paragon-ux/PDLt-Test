DESIGN a cache-control header strategy for a CDN-backed REST API covering the following resource types:
- STATIC ASSETS (JS, CSS, images) that change only on deploy
- USER PROFILE DATA that changes rarely (at most once per day)
- REAL-TIME DATA (stock prices, live scores) that must never be stale
- PUBLIC CATALOG DATA that is identical for all users
- AUTHENTICATED RESPONSES that vary by user
FOR EACH resource type SPECIFY the exact Cache-Control, Vary, ETag, and Surrogate-Control header values.
EXPLAIN the rationale for each directive.
IMPLEMENT a Python middleware function that sets the appropriate headers based on the response type.
