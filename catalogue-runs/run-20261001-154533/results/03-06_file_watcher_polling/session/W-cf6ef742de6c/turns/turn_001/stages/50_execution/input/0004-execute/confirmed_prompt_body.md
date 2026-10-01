DEFINE a Python function named watch with parameters directory, callback, interval=1.0
    POLL the entire directory tree under directory every interval seconds
    FOR each file, RETRIEVE its modification time using os.stat
    COMPARE current modification times with previously recorded times to DETECT creation, modification, or deletion events
    FOR each detected event, CALL callback(event_type, filepath)
    HANDLE subdirectory creation and deletion similarly
PROVIDE a test that
    CREATE a temporary directory
    START the watch function on that directory
    PERFORM file creation, modification, and deletion operations within the directory
    WAIT for callbacks
    VERIFY that all expected event_type and filepath callbacks are received
