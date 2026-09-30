Design a cache-control header strategy for a CDN-backed REST API with the following resource types:
1. Static assets (JS, CSS, images) that change only on deploy.
2. User profile data that changes rarely (once per day at most).
3. Real-time data (stock prices, live scores) that must never be stale.
4. Public catalog data that is the same for all users.
5. Authenticated responses that vary by user.

For each resource type, specify the exact Cache-Control, Vary, ETag, and Surrogate-Control headers. Explain why each directive is chosen. Implement a Python middleware function that sets the correct headers based on the response type.
