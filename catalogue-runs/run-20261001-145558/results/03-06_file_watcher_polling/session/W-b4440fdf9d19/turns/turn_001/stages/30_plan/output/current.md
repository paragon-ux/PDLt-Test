DEFINE function watch with parameters watch_path, callback, interval=1.0
INITIALIZE previous_snapshot as empty mapping
LOOP indefinitely every interval seconds
    BUILD current_snapshot by recursively traversING watch_path and recording each file's path with its os.stat().st_mtime
    COMPARE current_snapshot to previous_snapshot to IDENTIFY created, deleted, and modified paths
    FOR each created path CALL callback with event_type "create" and the filepath
    FOR each deleted path CALL callback with event_type "delete" and the filepath
    FOR each path where mtime differs CALL callback with event_type "modify" and the filepath
    UPDATE previous_snapshot to current_snapshot
ENDLOOP
DEFINE test procedure
    CREATE temporary directory
    START watcher in a separate thread invoking a recorder callback
    PERFORM file creation inside temporary directory
    PERFORM file modification on the created file
    PERFORM file deletion of the file
    WAIT sufficient time for callbacks to be captured
    VERIFY that recorded events include create, modify, and delete for the file
ENDDEFINE
