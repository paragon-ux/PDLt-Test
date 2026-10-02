INITIALIZE HTTP client with base URL https://jsonplaceholder.typicode.com
DEFINE LIST_POSTS operation
    SEND GET request to /posts
    RECEIVE response
    PARSE JSON
DEFINE CREATE_POST operation
    SEND POST request to /posts with JSON payload
    RECEIVE response
    PARSE JSON
DEFINE DELETE_POST operation
    SEND DELETE request to /posts/{id}
    RECEIVE response
    PARSE JSON
EXPOSE interface for invoking LIST_POSTS, CREATE_POST, DELETE_POST
HANDLE error responses appropriately
