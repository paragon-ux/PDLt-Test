REGISTER process names with their command lines
START_ALL to launch every registered process
MONITOR each child process
IF a child exits with a non-zero exit code THEN RESTART it using exponential backoff delays of 1 second, 2 seconds, 4 seconds, continuing up to a maximum delay of 30 seconds
TRACK crash occurrences per child within a 60‑second window
IF the same child crashes 5 times within that window THEN MARK the process as failed and CEASE further restarts
STOP_ALL to gracefully terminate all children by sending SIGTERM
IF a child does not exit within 5 seconds after SIGTERM THEN SEND SIGKILL
INCLUDE a test script that simulates a child process that crashes three times before succeeding
VERIFY that the supervisor restarts the simulated child with the appropriate backoff timings
