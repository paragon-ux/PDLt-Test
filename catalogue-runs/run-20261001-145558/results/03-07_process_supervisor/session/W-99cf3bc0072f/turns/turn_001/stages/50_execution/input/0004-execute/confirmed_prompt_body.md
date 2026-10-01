READ the request to implement a process supervisor in Python.
DEFINE function register(name, cmd) to register a named process with its command line.
DEFINE function start_all() to launch all registered processes.
DEFINE function stop_all() to gracefully terminate all children (SIGTERM, then SIGKILL after 5 seconds timeout).
MONITOR child processes for exit status.
IF a child exits with a non‑zero code THEN RESTART the child using exponential backoff starting at 1 second, doubling each attempt up to a maximum of 30 seconds.
IF a child crashes 5 times within 60 seconds THEN MARK the child as failed and STOP further restarts.
INCLUDE a test that runs a child script which crashes 3 times then succeeds, VERIFYING that the supervisor restarts it correctly with the specified backoff behavior.
