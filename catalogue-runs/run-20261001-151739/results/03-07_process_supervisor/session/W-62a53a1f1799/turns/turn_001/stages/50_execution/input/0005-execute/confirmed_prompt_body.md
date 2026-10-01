DEFINE a Python process supervisor.
REGISTER child processes using register(name, cmd).
LAUNCH all registered processes with start_all().
MONITOR each child process.
IF a child process exits with a non‑zero status THEN
    RESTART the child using exponential backoff intervals: 1 second, 2 seconds, 4 seconds, doubling each time up to a maximum of 30 seconds.
    IF the child crashes five times within a 60‑second window THEN
        MARK the process as failed and CEASE further restarts.
    ENDIF
ENDIF
PROVIDE a stop_all() operation that sends SIGTERM to all children, and IF a child does not exit within 5 seconds THEN send SIGKILL.
INCLUDE a test where a child script crashes three times before succeeding, verifying that the supervisor correctly restarts the process with the specified exponential backoff behavior.
