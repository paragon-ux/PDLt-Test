VALIDATE the listening port parameter is provided and is a positive integer.
CREATE a TCP listening socket bound to the configured port.
SET the listening socket to non‑blocking mode.
INITIALIZE a collection to track active client sockets and define MAX_CONNECTIONS = 64.
ADD the listening socket to the select read set.
WHILE true DO
    CALL select on the read set to obtain sockets ready for I/O.
    FOR each ready socket DO
        IF the ready socket is the listening socket THEN
            IF the current client count is less than MAX_CONNECTIONS THEN
                ACCEPT the incoming connection.
                SET the new client socket to non‑blocking mode.
                ADD the client socket to the select read set and to the tracking collection.
            ELSE
                SEND a rejection message to the connecting client.
                CLOSE the connecting socket.
            ENDIF
        ELSE
            RECEIVE data from the client socket.
            IF no data is received (client closed) THEN
                REMOVE the client socket from the select read set and the tracking collection.
                CLOSE the client socket.
            ELSE
                SEND the received data back to the same client, preserving newlines.
            ENDIF
        ENDIF
    ENDFOR
ENDWHILE
COMPOSE a Python script that implements the above behavior using only the select module.
COMPOSE a test script that:
    STARTS the server on a chosen port.
    ESTABLISHes three concurrent client connections.
    FOR each client, SENDs a distinct multi‑line message.
    RECEIVEs the echoed response.
    VERIFIES that the echo matches the sent message with original newlines.
    DISCONNECTs all clients.
    SHUTDOWNs the server and CONFIRMs that all sockets are closed.
