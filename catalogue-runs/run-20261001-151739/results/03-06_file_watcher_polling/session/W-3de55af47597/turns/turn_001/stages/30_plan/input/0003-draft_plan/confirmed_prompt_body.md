IMPLEMENT a cross‑platform file change detector in Python using only the os.stat API, EXCLUDING any use of inotify, watchdog, or FSEvents.
DEFINE a function watch(directory, callback, interval=1.0) THAT repeatedly polls the entire directory tree EVERY interval seconds.
FOR each poll:
    COMPARE current modification times (mtime) of files and subdirectories WITH previously stored modification times USING os.stat TO DETECT file creation, deletion, and modification.
    FOR each detected change:
        INVOKE callback(event_type, filepath) WHERE event_type INDICATES the type of change AND filepath IS the affected path.
HANDLE creation and deletion of subdirectories as part of the detection process.
INCLUDE a test THAT creates a temporary directory, STARTS the watch function, PERFORMS file operations (create, modify, delete), WAITS for the callbacks, and VERIFIES that all expected events are reported.
