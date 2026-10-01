TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a TCP echo server in Python that listens on a configurable port, accepts multiple concurrent clients, echoes back each line received from each client preserving newlines, handles client disconnections gracefully by removing the socket from the select set and closing it, supports a maximum of 64 simultaneous connections and rejects extra connections with an appropriate message, and includes a test that spawns the server, connects three clients concurrently, sends distinct messages from each, verifies correct echoes, then disconnects clients and verifies cleanup.
APPROACH/RISK NOTES:
Use only the select module for I/O multiplexing; explicitly avoid asyncio and threading.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- TCP
- Python
- select
- socket
- 64
