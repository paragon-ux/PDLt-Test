TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a cross-platform file change detector in Python using only os.stat (no inotify, no watchdog, no FSEvents):
1. watch(directory, callback, interval=1.0): Polls the directory tree every interval seconds.
2. Detects file creation, deletion, and modification (via mtime comparison).
3. Calls callback(event_type, filepath) for each change detected.
4. Handles subdirectory creation and deletion.
5. Include a test that creates a temp directory, starts the watcher, performs file operations (create, modify, delete), waits for callbacks, and verifies all events were detected.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- watch
- callback
- interval
- event_type
- filepath
