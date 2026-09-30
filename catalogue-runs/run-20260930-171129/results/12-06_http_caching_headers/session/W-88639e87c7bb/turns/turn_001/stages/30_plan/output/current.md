PARSE the confirmed prompt to identify each resource type and its caching requirements
DEFINE the header specifications (Cache-Control, Vary, ETag, Surrogate-Control) for each identified resource type
COMPOSE the rationale explanations linking each header choice to the corresponding resource characteristics
DEVELOP a Python middleware function that INSPECTS the response metadata or route identifier to DETERMINE the resource type
SET the appropriate headers on the HTTP response according to the pre‑defined specifications
RETURN the assembled header specifications, rationales, and middleware source code
