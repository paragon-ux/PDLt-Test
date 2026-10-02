IMPLEMENT a TCP echo server in Python using ONLY the select module.
PROHIBIT the use of asyncio.
PROHIBIT the use of threading.
CONFIGURE the listening port as a parameter.
LISTEN on the configured port.
SUPPORT up to 64 simultaneous connections.
REJECT any connections beyond 64 with an appropriate message.
ACCEPT multiple concurrent clients.
FOR each client, ECHO back every line received, preserving newlines.
HANDLE client disconnection gracefully by removing the client from the select set and closing its socket.
PROVIDE a test that:
  START the server.
  CONNECT three clients concurrently.
  FOR each client, SEND a distinct message.
  VERIFY that each client receives the correct echoed messages, preserving newlines.
  DISCONNECT the clients.
  CONFIRM that the server cleans up resources correctly.
