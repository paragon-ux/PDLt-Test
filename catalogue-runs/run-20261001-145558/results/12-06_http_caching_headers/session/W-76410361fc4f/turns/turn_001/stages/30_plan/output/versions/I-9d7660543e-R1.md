READ the task description
IDENTIFY resource types: static assets, user profile data, real-time data, public catalog data, authenticated responses
DEFINE header specifications for each resource type (Cache-Control, Vary, ETag, Surrogate-Control)
COMPOSE a Python middleware skeleton that inspects the response type
SELECT appropriate header set based on response category
SET the headers on the outgoing response
RETURN the response to the client
