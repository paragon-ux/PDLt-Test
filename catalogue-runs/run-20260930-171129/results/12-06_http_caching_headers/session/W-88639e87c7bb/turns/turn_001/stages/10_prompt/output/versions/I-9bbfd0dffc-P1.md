DESIGN a cache-control header strategy for a CDN-backed REST API covering five resource types: static assets that change only on deploy, user profile data that changes at most once per day, real-time data that must never be stale, public catalog data identical for all users, and authenticated responses that vary per user.
SPECIFY the exact Cache-Control, Vary, ETag, and Surrogate-Control header values for each resource type.
EXPLAIN the rationale for each set of header values.
PROVIDE a Python middleware function that INSPECTS the response type and SETS the appropriate headers.
INCLUDE the operative task entities exactly as listed: Cache-Control, Vary, ETag, Surrogate-Control, Python, middleware.
