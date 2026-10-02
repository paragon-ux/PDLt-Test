PARSE the confirmed prompt for required deliverable
DEFINE a snapshot data structure mapping file paths to modification times
IMPLEMENT the function watch with parameters (directory_path, callback, interval=1.0)
    LOOP indefinitely with a sleep interval
        SCAN the entire directory tree under directory_path using os.walk
        FOR each file and directory, OBTAIN its modification time via os.stat
        COMPARE current snapshot to previous snapshot to DETECT creations, deletions, modifications
        FOR each detected creation, INVOKE callback with event_type "created" and filepath
        FOR each detected deletion, INVOKE callback with event_type "deleted" and filepath
        FOR each detected modification, INVOKE callback with event_type "modified" and filepath
        UPDATE the previous snapshot with the current snapshot
        SLEEP for interval seconds
IMPLEMENT cleanup and termination handling
DEVELOP an automated test suite
    CREATE a temporary directory
    DEFINE a callback function that records received events
    START the watch function in a concurrent context targeting the temporary directory
    PERFORM a series of file operations: create a file, modify it, delete it, and create/delete subdirectories
    WAIT sufficient time for the watcher to detect each operation
    STOP the watcher
    VERIFY that the recorded events correspond to the performed operations
