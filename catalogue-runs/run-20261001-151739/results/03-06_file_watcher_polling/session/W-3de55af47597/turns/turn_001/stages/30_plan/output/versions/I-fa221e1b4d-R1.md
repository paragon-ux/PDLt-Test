DEFINE watch function with parameters directory, callback, interval=1.0
INITIALIZE empty mapping previous_mtimes
REPEAT forever
    SCAN recursively all entries under directory
    USE os.stat to retrieve modification timestamps for each entry
    COLLECT current_mtimes for each entry
    COMPARE current_mtimes to previous_mtimes
    DETECT added entries and INVOKE callback("created", path)
    DETECT removed entries and INVOKE callback("deleted", path)
    DETECT modified entries and INVOKE callback("modified", path)
    UPDATE previous_mtimes with current_mtimes
    SLEEP interval seconds
END_REPEAT
DEFINE test routine
CREATE temporary directory
IMPLEMENT test callback to record events
START watch function on temporary directory with test callback
CREATE a test file in temporary directory
MODIFY the test file content
DELETE the test file
WAIT for detection interval
COLLECT recorded events from test callback
VERIFY that events include creation, modification, and deletion for the test file
STOP watch function
REMOVE temporary directory
