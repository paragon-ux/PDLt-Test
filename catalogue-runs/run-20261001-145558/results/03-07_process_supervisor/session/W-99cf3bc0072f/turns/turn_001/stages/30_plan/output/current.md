READ the request to implement a process supervisor in Python
DEFINE function register(name, cmd) to add a named process and its command line to a registry
DEFINE function start_all() to iterate over the registry and launch each registered process as a child
DEFINE function stop_all() to send SIGTERM to all child processes, wait up to 5 seconds, then send SIGKILL to any remaining
MONITOR each child process for exit status
IF a child exits with a non‑zero code THEN schedule a restart using exponential backoff starting at 1 second, doubling each attempt up to a maximum of 30 seconds
TRACK restart attempts per child with timestamps
IF a child experiences 5 restart attempts within any 60‑second window THEN mark the child as failed and cease further restart attempts for that child
INCLUDE a test that launches a child script designed to crash three times then exit successfully
VERIFY that the supervisor restarts the child according to the specified backoff behavior and ultimately allows the child to succeed
