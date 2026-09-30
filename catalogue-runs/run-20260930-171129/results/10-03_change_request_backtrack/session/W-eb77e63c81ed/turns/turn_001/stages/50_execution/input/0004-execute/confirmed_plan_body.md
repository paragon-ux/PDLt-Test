DEFINE base URL as https://jsonplaceholder.typicode.com
CREATE HTTP client configured for JSON communication
IMPLEMENT function LIST_POSTS that SENDS a GET request to /posts and RETURNS the response data
IMPLEMENT function CREATE_POST that ACCEPTS post data, SENDS a POST request to /posts with the payload, and RETURNS the created resource response
IMPLEMENT function DELETE_POST that ACCEPTS a post identifier, SENDS a DELETE request to /posts/{id}, and RETURNS the status of the deletion
PACKAGE the client with the three functions for external use
