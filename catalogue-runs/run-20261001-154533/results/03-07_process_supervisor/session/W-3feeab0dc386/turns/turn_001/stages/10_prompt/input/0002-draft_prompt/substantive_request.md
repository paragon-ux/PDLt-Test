TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Develop a Python process supervisor that can register a named process with a command line via the function register(name, cmd); start all registered processes using start_all(); continuously monitor child processes and, upon non-zero exit, restart the child using exponential backoff intervals of 1 second, then 2 seconds, then 4 seconds, up to a maximum of 30 seconds; if a child process crashes five times within a rolling 60‑second window, mark the process as failed and cease further restarts; provide a stop_all() function that gracefully terminates all children by sending SIGTERM and, if necessary after a five‑second timeout, SIGKILL; include a test script that deliberately crashes three times before succeeding to verify correct restart behavior with backoff.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- register
- start_all
- stop_all
- exponential backoff
- SIGTERM
- SIGKILL
