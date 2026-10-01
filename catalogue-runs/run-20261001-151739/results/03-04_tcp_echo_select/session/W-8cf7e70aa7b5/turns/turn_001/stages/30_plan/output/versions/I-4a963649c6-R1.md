CONFIGURE the listening port (or use default).
INITIALIZE a TCP listening socket.
USE only the SELECT module for I/O multiplexing, avoiding asyncio and threading.
SET socket options as needed.
BIND the socket to the configured port.
LISTEN for incoming connections.
INITIALIZE an empty collection of client sockets and a connection counter.
ENTER the main event loop using SELECT to monitor the listening socket and all client sockets for readability.
IF the listening socket is readable THEN
    IF connection counter < 64 THEN
        ACCEPT the new client connection.
        ADD the client socket to the SELECT monitoring set.
        INCREMENT the connection counter.
    ELSE
        SEND a rejection message to the connecting client.
        CLOSE the connecting socket.
    ENDIF
ENDIF
FOR each client socket reported as readable by SELECT DO
    READ a line (including newline) from the client.
    IF the read data is empty (client closed) THEN
        REMOVE the client socket from the SELECT monitoring set.
        CLOSE the client socket.
        DECREMENT the connection counter.
    ELSE
        ECHO the received line back to the same client, preserving the newline.
    ENDIF
ENDFOR
CONTINUE the event loop until external termination.
DEVELOP a test harness that:
    SPAWNS the echo server on a configurable port.
    CONNECT three client sockets concurrently to the server.
    SEND distinct messages from each client.
    COLLECT the responses from each client.
    VERIFY that each client receives the exact echoed messages it sent.
    DISCONNECT the three clients.
    VERIFY that the server has removed the client sockets and cleaned up resources.
