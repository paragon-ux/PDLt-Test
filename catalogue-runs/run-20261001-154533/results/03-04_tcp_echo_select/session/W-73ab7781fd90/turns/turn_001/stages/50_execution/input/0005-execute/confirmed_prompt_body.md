IMPLEMENT a TCP echo server in Python using only the select module, PROHIBIT use of asyncio or threading.
LISTEN on a configurable port.
ACCEPT multiple concurrent client connections, supporting up to 64 simultaneous connections.
FOR each connected client:
    RECEIVE each line preserving newline characters.
    ECHO the line back to the client.
HANDLE client disconnection by removing the client socket from the select monitoring set and closing the socket.
IF the active connection count exceeds 64:
    REJECT new connections with an appropriate message.
PROVIDE a test that STARTS the server, CONCURRENTLY CONNECTS three clients, SENDS distinct messages from each client, VERIFIES that each client receives echoed responses matching the sent messages, DISCONNECTS the clients, and VERIFIES that resources are cleaned up.
