DESIGN a cache-control header strategy for a CDN-backed REST API covering five resource types:
    - static assets (JS, CSS, images) that change only on deploy
    - user profile data that changes rarely (at most once per day)
    - real-time data (stock prices, live scores) that must never be stale
    - public catalog data that is the same for all users
    - authenticated responses that vary by user
FOR EACH resource type:
    SPECIFY the exact Cache-Control header value
    SPECIFY the exact Vary header value
    SPECIFY the exact ETag header value
    SPECIFY the exact Surrogate-Control header value
    EXPLAIN the rationale for each header directive
IMPLEMENT a Python middleware function that sets the appropriate headers based on the response type
