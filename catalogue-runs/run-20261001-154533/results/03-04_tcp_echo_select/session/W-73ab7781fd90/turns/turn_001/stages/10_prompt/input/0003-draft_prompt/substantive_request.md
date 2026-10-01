TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a TCP echo server in Python using only the select module, explicitly prohibiting the use of asyncio or threading. The server must listen on a configurable port and accept multiple concurrent client connections. For each client, it must echo back every line received, preserving the newline characters. It must handle client disconnections gracefully by removing the client socket from the select monitoring set and closing the socket. The server must support up to 64 simultaneous connections; if the limit is exceeded, it should reject new connections with an appropriate message. Additionally, provide a test that starts the server, concurrently connects three clients, sends distinct messages from each client, verifies that the echoed responses match the sent messages, then disconnects the clients and verifies that resources are cleaned up.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- TCP
- echo server
- Python
- select module
- configurable port
- client disconnection
- test

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: client disconnection
