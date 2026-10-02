IMPLEMENT a cross-platform file change detector in Python using ONLY os.stat.
FORBID the use of inotify, watchdog, or FSEvents.
PROVIDE a function watch that takes a directory path, a callback function, and an OPTIONAL interval defaulting to interval=1.0 seconds.
POLL the entire directory tree at the given interval.
DETECT file creation, deletion, and modification by COMPARING modification times (mtime).
FOR EACH detected change, INVOKE the callback with event_type and filepath.
HANDLE creation and deletion of subdirectories.
INCLUDE an automated test that creates a temporary directory, STARTS the watcher, PERFORMS file operations (create, modify, delete), WAITS for callbacks, and VERIFIES that all expected events are reported.
