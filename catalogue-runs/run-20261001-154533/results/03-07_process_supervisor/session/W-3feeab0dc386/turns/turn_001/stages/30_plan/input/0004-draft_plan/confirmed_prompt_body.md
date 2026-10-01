DEFINE function register(name, cmd)
    ADD a process entry identified by name with command line cmd to the registry

DEFINE function start_all()
    FOR each registered process
        LAUNCH the process

DEFINE function stop_all()
    FOR each running child process
        SEND SIGTERM
        WAIT up to five seconds
        IF process still alive
            SEND SIGKILL

MONITOR all child processes CONTINUOUSLY
IF a child process exits with non-zero status
    RESTART the process USING exponential backoff intervals: 1 second, then 2 seconds, then 4 seconds, doubling each attempt up to a maximum of 30 seconds

TRACK restart count per process OVER a rolling 60-second window
IF a process restarts five times within the 60-second window
    MARK the process as FAILED
    CEASE further restarts

INCLUDE a test script THAT deliberately crashes three times before succeeding TO VERIFY correct restart behavior with exponential backoff
