REGISTER a process name with its command line
START_ALL to launch every registered process
MONITOR each child process
IF a child exits with a non-zero exit code THEN restart it using exponential backoff delays of 1 second, 2 seconds, 4 seconds, up to a maximum of 30 seconds
IF the same child crashes 5 times within a 60‑second window THEN mark the process as failed and cease restarting it
STOP_ALL to gracefully terminate all children by sending SIGTERM
IF a child does not exit within 5 seconds after SIGTERM THEN send SIGKILL
INCLUDE a test script that simulates a child process that crashes three times before succeeding and VERIFY that the supervisor restarts the child with the appropriate backoff timings
