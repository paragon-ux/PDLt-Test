READ the request to implement a cross‑platform file change detector in Python using only os.stat
DEFINE the function watch(directory, callback, interval=1.0)
POLL the directory tree every interval seconds
DETECT file creation, deletion, and modification by comparing mtimes obtained via os.stat
CALL callback(event_type, filepath) for each detected change
HANDLE subdirectory creation and deletion during polling
INCLUDE a test that creates a temporary directory, starts the watcher, performs file operations (create, modify, delete), waits for callbacks, and verifies that all events were detected
