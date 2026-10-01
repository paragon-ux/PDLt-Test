PARSE the CONFIRMED_PROMPT_BODY to extract functional specifications
DEFINE a registry data structure for process entries with fields name and command
IMPLEMENT the register function to ADD a process entry to the registry
IMPLEMENT the start_all function to ITERATE over registered processes and LAUNCH each command
IMPLEMENT the stop_all function to ITERATE over running child processes, SEND SIGTERM, WAIT up to five seconds, IF process still alive THEN SEND SIGKILL
ESTABLISH a MONITOR loop that CONTINUOUSLY watches child processes
IF a child process exits with non-zero status THEN SCHEDULE a restart using exponential backoff intervals: 1 second, then 2 seconds, then 4 seconds, doubling each attempt up to a maximum of 30 seconds
TRACK restart count per process over a rolling 60‑second window
IF a process restarts five times within the 60‑second window THEN MARK the process as FAILED and CEASE further restarts
CREATE a test script that deliberately crashes three times before succeeding
UTILIZE the test script to VERIFY correct restart behavior with exponential backoff
