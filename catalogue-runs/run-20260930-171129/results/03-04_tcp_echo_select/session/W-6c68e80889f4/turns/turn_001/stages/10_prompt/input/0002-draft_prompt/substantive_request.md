TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a TCP echo server in Python using only the select module (no asyncio, no threading). The server must listen on a configurable port, accept multiple concurrent clients, and echo back every line received from each client while preserving newlines. It must handle client disconnection gracefully by removing the client from the select set and closing the socket. The server must support up to 64 simultaneous connections and reject additional connections with an appropriate message. Include a test that spawns the server, connects three clients concurrently, sends different messages from each, verifies that each client receives the correct echoed messages, then disconnects the clients and verifies that the server cleans up resources.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- select
- socket
- listen
- accept
- send
- TCP
- port
- 64
