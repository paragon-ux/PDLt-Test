TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a TCP echo server in Python using only the select module (no asyncio, no threading). The server must listen on a configurable port and accept multiple concurrent clients. It must echo back every line received from each client, preserving newlines. It must handle client disconnection gracefully by removing the client from the select set and closing its socket. The server must support up to 64 simultaneous connections, rejecting any additional connections with an appropriate message. Additionally, provide a test that starts the server, connects three clients concurrently, sends distinct messages from each client, verifies that each client receives the correct echoed messages, then disconnects the clients and confirms that the server cleans up resources correctly.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- select
- asyncio
- threading
- TCP
- 64

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: select; asyncio; threading
