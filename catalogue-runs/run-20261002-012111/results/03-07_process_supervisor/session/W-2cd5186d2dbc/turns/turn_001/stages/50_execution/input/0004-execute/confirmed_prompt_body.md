REGISTER a child process using register(name, cmd).
CALL start_all() to launch all registered processes.
FOR EACH registered child:
    MONITOR the child process.
    IF the child exits with a non-zero status THEN
        RESTART the child using exponential backoff intervals of 1s, 2s, 4s, up to a maximum of 30s.
        INCREMENT the failure count for that child.
        IF the child has failed 5 times within 60 seconds THEN
            MARK the child as failed and cease further restarts.
        ENDIF
    ENDIF
END FOR
PROVIDE stop_all() to gracefully terminate all children by sending SIGTERM.
WAIT up to 5s for children to exit.
IF any child remains after 5s THEN
    SEND SIGKILL to force termination.
ENDIF
TEST the supervisor by creating a child script that crashes 3 times before succeeding, verifying the correct restart behavior with exponential backoff.
