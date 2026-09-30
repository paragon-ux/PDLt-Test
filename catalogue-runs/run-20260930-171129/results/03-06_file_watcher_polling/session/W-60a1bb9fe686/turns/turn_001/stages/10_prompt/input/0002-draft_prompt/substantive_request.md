TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a cross-platform file change detector in Python using only os.stat (no inotify, no watchdog, no FSEvents). Provide a watch(directory, callback, interval=1.0) function that polls the directory tree every interval seconds, detects file creation, deletion, and modification via mtime comparison, calls callback(event_type, filepath) for each change, and handles subdirectory creation and deletion. Include a test that creates a temporary directory, starts the watcher, performs file operations (create, modify, delete), waits for callbacks, and verifies all events were detected.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- watch
- directory
- callback
- interval
- event_type
- filepath
- os.stat
