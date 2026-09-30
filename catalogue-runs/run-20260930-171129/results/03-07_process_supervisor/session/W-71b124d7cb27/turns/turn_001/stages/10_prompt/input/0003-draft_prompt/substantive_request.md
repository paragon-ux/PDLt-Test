TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a Python process supervisor that manages named child processes. Provide a register(name, cmd) function to store a process name and its command line. Provide start_all() to launch all registered processes. The supervisor must monitor each child; if a child exits with a non-zero exit code, restart it using exponential backoff delays of 1 second, 2 seconds, 4 seconds, up to a maximum of 30 seconds. If the same child crashes 5 times within a 60‑second window, mark the process as failed and cease restarting it. Provide stop_all() to gracefully terminate all children by sending SIGTERM and, if a child does not exit within 5 seconds, send SIGKILL. Include a test script that simulates a child process that crashes three times before succeeding, and verify that the supervisor restarts the child with the appropriate backoff timings.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- register
- start_all
- stop_all
- SIGTERM
- SIGKILL
- exponential backoff
- 5 times

OPERATOR CORRECTION (host-side mechanical check): the following task entities are missing from the prompt body and MUST appear verbatim, character-for-character: start_all; stop_all
