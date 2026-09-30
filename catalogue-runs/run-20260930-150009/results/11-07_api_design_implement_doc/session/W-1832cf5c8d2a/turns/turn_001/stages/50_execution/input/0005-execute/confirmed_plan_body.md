DEFINE data model for bookmark with fields url, title, tags, created_at
DESIGN RESTful endpoints: POST /bookmarks (create), GET /bookmarks/{id} (read), PUT /bookmarks/{id} (update), DELETE /bookmarks/{id} (delete), GET /bookmarks?tag={tag} (search by tag)
IMPLEMENT HTTP server using Python http.server module
IMPLEMENT request parsing and JSON handling using json and urllib modules
IMPLEMENT each endpoint logic to manage an in‑memory collection of bookmarks
GENERATE OpenAPI 3.0 specification in YAML describing all endpoints, request/response schemas, status codes, and example values
WRITE a self‑contained test script that starts the server, performs CREATE, READ, UPDATE, DELETE, and tag SEARCH operations via HTTP requests, and asserts the correctness of each response
