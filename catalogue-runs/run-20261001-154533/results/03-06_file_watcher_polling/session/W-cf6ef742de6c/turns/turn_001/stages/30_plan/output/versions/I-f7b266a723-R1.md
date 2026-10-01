DEFINE watch function with parameters directory, callback, interval=1.0
INITIALIZE empty mapping of paths to last modification times
LOOP forever
    SLEEP for interval seconds
    RECURSIVELY LIST all file and subdirectory paths under directory
    FOR each path
        RETRIEVE current modification time using os.stat
        IF path not in mapping
            ADD path with its modification time to mapping
            CALL callback('created', path)
        ELSE
            IF current modification time differs from stored time
                UPDATE mapping entry with current modification time
                CALL callback('modified', path)
            ENDIF
        ENDIF
    ENDFOR
    DETECT deleted paths as entries present in mapping but absent from current listing
    FOR each deleted path
        REMOVE path from mapping
        CALL callback('deleted', path)
    ENDFOR
ENDLOOP

DEFINE test procedure
    CREATE temporary directory
    START watch function on temporary directory in background
    PERFORM file creation within temporary directory
    PERFORM file modification within temporary directory
    PERFORM file deletion within temporary directory
    WAIT for callback invocations
    VERIFY that callbacks include created, modified, and deleted events with correct paths
