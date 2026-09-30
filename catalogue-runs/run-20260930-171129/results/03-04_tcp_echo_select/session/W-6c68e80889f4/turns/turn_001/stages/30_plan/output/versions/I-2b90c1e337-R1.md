READ the requirement to implement a TCP echo server in Python using the select module
CONFIGURE the server to listen on a configurable port
SET the maximum number of simultaneous connections to 64
USE the socket library to create a TCP socket
CALL listen on the socket to accept incoming connections
USE select to monitor the listening socket and client sockets for readability
WHEN the listening socket is readable, ACCEPT a new client connection
IF the current number of connections is less than 64, ADD the new client socket to the select set
ELSE SEND an appropriate rejection message to the connecting client and CLOSE the connection
FOR each client socket that becomes readable, READ lines from the client preserving newlines
FOR each line received, SEND the line back to the same client (echo)
IF a client disconnects, REMOVE the client socket from the select set and CLOSE the socket
IMPLEMENT a test that spawns the server, CONNECT three clients concurrently, SEND different messages from each client, VERIFY each client receives the correctly echoed messages, DISCONNECT the clients, and VERIFY the server cleans up resources
