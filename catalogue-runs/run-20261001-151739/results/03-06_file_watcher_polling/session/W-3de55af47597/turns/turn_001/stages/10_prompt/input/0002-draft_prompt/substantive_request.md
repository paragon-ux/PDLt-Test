TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a cross‑platform file change detector in Python using only the os.stat API (no inotify, watchdog, or FSEvents). Provide a function watch(directory, callback, interval=1.0) that repeatedly polls the entire directory tree every interval seconds. Detect file creation, deletion, and modification by comparing stored modification times (mtime). For each detected change, invoke callback(event_type, filepath) where event_type indicates the type of change and filepath is the affected path. The watcher must also handle creation and deletion of subdirectories. Include a test that creates a temporary directory, starts the watcher, performs file operations (create, modify, delete), waits for the callbacks, and verifies that all expected events are reported.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- watch
- callback
- interval=1.0
- event_type
- filepath
- os.stat
