DEFINE a ProcessSupervisor component
REGISTER child processes via a register(name, cmd) operation
LAUNCH all registered child processes with start_all()
MONITOR each child process for termination status
IF a child process exits with a non‑zero status THEN
    RESTART the child using exponential backoff intervals: 1 second, 2 seconds, 4 seconds, doubling each time up to a maximum of 30 seconds
    TRACK restart attempts and timestamps
    IF the child crashes five times within a 60‑second window THEN
        MARK the child as failed
        CEASE further restarts for that child
    ENDIF
ENDIF
PROVIDE a stop_all() operation that sends SIGTERM to all children
WAIT up to 5 seconds for each child to exit
IF a child has not exited after 5 seconds THEN
    SEND SIGKILL to the child
ENDIF
DEVELOP a test case where a child script crashes three times before succeeding
EXECUTE the supervisor with the test child script
VERIFY that the supervisor restarts the child with the specified exponential backoff behavior
VERIFY that the child is not marked as failed because the crash count does not exceed the threshold
VERIFY that stop_all correctly terminates children using SIGTERM and SIGKILL as needed
