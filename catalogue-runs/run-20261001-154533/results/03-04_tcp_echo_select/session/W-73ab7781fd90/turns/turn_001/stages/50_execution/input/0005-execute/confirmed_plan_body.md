PARSE configuration for listening port
CREATE listening TCP socket bound to configured port
SET listening socket to non‑blocking mode
INITIALIZE monitored set with listening socket
WHILE true
    CALL select on monitored set to obtain readable sockets
    FOR each socket in readable set
        IF socket is listening socket
            IF current connection count < 64
                ACCEPT client connection
                SET client socket to non‑blocking mode
                ADD client socket to monitored set
                INCREMENT connection count
            ELSE
                SEND rejection message to client
                CLOSE client socket
            ENDIF
        ELSE
            RECEIVE line preserving newline from client socket
            IF received data is empty
                REMOVE client socket from monitored set
                CLOSE client socket
                DECREMENT connection count
            ELSE
                SEND received line back to client socket
            ENDIF
        ENDIF
    ENDFOR
ENDWHILE

START server process via subprocess invocation
WAIT until server signals readiness to accept connections
CREATE three concurrent client connections to server
FOR each client
    SEND distinct message terminated with newline
    RECEIVE echoed response from server
    VERIFY that echoed response matches the sent message
ENDFOR
CLOSE all client connections
WAIT for server to clean up client resources and reflect zero active connections
TERMINATE server process
