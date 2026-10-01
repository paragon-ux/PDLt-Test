TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a process supervisor in Python that manages child processes with restart-on-crash: register(name, cmd) to register a named process with its command line; start_all() to launch all registered processes; monitor children and restart any that exit with a non-zero code using exponential backoff (1s, 2s, 4s, max 30s); if a child crashes 5 times within 60 seconds, mark it as failed and stop restarting; stop_all() to gracefully terminate all children (SIGTERM, then SIGKILL after 5s timeout); include a test with a child script that crashes 3 times then succeeds, verifying the supervisor restarts it correctly with backoff.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- register
- start_all
- stop_all
- exponential backoff
