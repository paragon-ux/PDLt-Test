IDENTIFY the five resource type categories
FOR EACH resource type:
    DETERMINE Cache-Control header directive
    DETERMINE Vary header directive
    DETERMINE ETag header strategy
    DETERMINE Surrogate-Control header directive
    EXPLAIN rationale for each directive
COMPILE the header specifications into a reference document
DEVELOP a Python middleware function:
    RECEIVE request and response
    CLASSIFY response into one of the resource type categories
    LOOKUP header specification for the identified category
    APPLY Cache-Control, Vary, ETag, and Surrogate-Control headers to the response
    RETURN modified response
