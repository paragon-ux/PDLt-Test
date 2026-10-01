IMPLEMENT a cross‑platform file change detector in Python using ONLY os.stat.
DEFINE a function watch that takes watch, callback, interval=1.0 and POLLS the directory tree every interval seconds.
DETECT file creation, deletion, and modification by COMPARING mtime values.
CALL callback with event_type and filepath for each detected change.
HANDLE subdirectory creation and deletion.
INCLUDE a test that CREATES a temporary directory, STARTS the watcher, PERFORMS file operations (create, modify, delete), WAITS for callbacks, and VERIFIES that all events were detected.
