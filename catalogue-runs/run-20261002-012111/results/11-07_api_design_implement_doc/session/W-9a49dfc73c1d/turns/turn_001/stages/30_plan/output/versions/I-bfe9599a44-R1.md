DESIGN the bookmark data model with fields url, title, tags, and created_at
DEFINE CRUD endpoint paths and HTTP methods for the bookmark resource
DEFINE a tag-based search endpoint using a query parameter to filter bookmarks by tag
SPECIFY request and response schemas, status codes, and example values for each endpoint
COMPOSE an OpenAPI 3.0 specification document in YAML or JSON that includes the defined endpoints and schemas
IMPLEMENT an HTTP server using Python http.server that dispatches requests to handlers for each endpoint
    PARSE request bodies as JSON using the json module
    EXTRACT query parameters using urllib.parse
    MANAGE bookmark records in an in-memory data store
    SERIALIZE response bodies as JSON with appropriate content-type headers
    RETURN correct HTTP status codes for each operation
DEVELOP a self-contained test harness that starts the server in a background thread or subprocess
    PERFORM HTTP requests using urllib.request to create a bookmark
    PERFORM HTTP requests using urllib.request to retrieve the created bookmark
    PERFORM HTTP requests using urllib.request to update the bookmark
    PERFORM HTTP requests using urllib.request to delete the bookmark
    PERFORM HTTP requests using urllib.request to search for bookmarks by tag
    ASSERT that each response status code and payload matches the expected values from the OpenAPI specification
SHUTDOWN the server after test execution completes
