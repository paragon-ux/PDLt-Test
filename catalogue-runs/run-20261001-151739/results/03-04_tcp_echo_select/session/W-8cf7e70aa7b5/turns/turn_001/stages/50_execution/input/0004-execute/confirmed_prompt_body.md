IMPLEMENT a TCP echo server in Python that LISTENS on a configurable port.
ACCEPT multiple concurrent clients up to a maximum of 64 connections.
ECHO back each line received from each client, preserving newlines.
HANDLE client disconnections gracefully by REMOVING the client socket from the select set and CLOSING it.
REJECT any connection attempts exceeding 64 simultaneous connections with an appropriate message.
INCLUDE a test that SPAWNS the server, CONNECTS three clients concurrently, SEND distinct messages from each client, VERIFY that each client receives the correct echoed messages, then DISCONNECT the clients and VERIFY cleanup.
