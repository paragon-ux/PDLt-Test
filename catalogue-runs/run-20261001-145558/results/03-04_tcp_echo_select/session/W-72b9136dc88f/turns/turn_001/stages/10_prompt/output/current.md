READ the TCP echo server specifications from the request
IMPLEMENT a Python server using only the SELECT module
CONFIGURE the server to listen on a user-specified port
ALLOW up to 64 simultaneous client connections
REJECT connections beyond the limit with an appropriate message to the client
ACCEPT multiple concurrent client connections
FOR each connected client, READ each line of input preserving newline characters
ECHO back each received line to the same client
DETECT client disconnections and gracefully remove the client from the SELECT set and close its socket
INCLUDE a test suite that:
    START the server
    CONNECT three clients concurrently to the server
    SEND distinct messages from each client
    VERIFY that each client receives the correct echoed messages
    DISCONNECT the clients
    VERIFY that the server cleans up the client connections properly
