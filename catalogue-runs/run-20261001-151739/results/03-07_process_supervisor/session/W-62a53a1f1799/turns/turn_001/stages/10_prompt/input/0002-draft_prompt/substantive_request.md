TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Create a Python process supervisor that can register named child processes via a function `register(name, cmd)`, launch them all with `start_all()`, monitor each child, and if a child exits with a non‑zero status, restart it using exponential backoff intervals of 1 second, 2 seconds, 4 seconds, up to a maximum of 30 seconds. If a child crashes five times within a 60‑second window, the supervisor should mark the process as failed and cease further restarts. Provide a `stop_all()` operation that gracefully terminates all children by sending SIGTERM and, if they do not exit within 5 seconds, sending SIGKILL. Include a test where a child script crashes three times before succeeding, verifying that the supervisor correctly restarts the process with the specified backoff behavior.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Python
- register(name, cmd)
- start_all()
- stop_all()
- exponential backoff
- SIGTERM
- SIGKILL
