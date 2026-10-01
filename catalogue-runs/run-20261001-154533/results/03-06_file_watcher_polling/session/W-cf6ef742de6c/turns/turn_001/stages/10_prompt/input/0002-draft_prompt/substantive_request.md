TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a cross-platform file change detector in Python using only os.stat. Provide a function watch(directory, callback, interval=1.0) that polls the directory tree every interval seconds, detects file creation, deletion, and modification via mtime comparison, and calls callback(event_type, filepath) for each change. The detector must handle subdirectory creation and deletion. Include a test that creates a temporary directory, starts the watcher, performs file operations (create, modify, delete), waits for callbacks, and verifies all events were detected.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- watch
- directory
- callback
- interval=1.0
- os.stat
- event_type
- filepath
