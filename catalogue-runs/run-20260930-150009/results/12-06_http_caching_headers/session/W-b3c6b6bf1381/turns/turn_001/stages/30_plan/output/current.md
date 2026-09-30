IDENTIFY the response type (STATIC ASSET, USER PROFILE, REAL-TIME DATA, PUBLIC CATALOG, AUTHENTICATED RESPONSE) based on request path or metadata
SELECT the appropriate Cache-Control directives for the identified type
SELECT the appropriate Vary header values for the identified type
SELECT the appropriate ETag generation strategy for the identified type
SELECT the appropriate Surrogate-Control directives for the identified type
COMPOSE the full set of headers (Cache-Control, Vary, ETag, Surrogate-Control) according to the selections
INSERT the composed headers into the HTTP response
RETURN the modified response to the client
IMPLEMENT a Python middleware function that:
ON each request, DETECT the response type
APPLY the header‑selection logic
SET the headers on the outgoing response
PASS control to the next component in the pipeline
