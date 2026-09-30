READ the request to implement a cross‑platform file change detector in Python using only os.stat
DEFINE the function watch(directory, callback, interval=1.0)
POLL the directory tree at the specified interval
COMPARE current mtimes from os.stat with previously stored mtimes to DETECT file creation, deletion, and modification
UPDATE the stored state after each poll
CALL callback(event_type, filepath) for each detected change
HANDLE subdirectory creation and deletion by dynamically updating the monitored tree during polling
SETUP a temporary test directory
START the watcher on the temporary directory
PERFORM file operations within the test directory (create, modify, delete files and subdirectories)
WAIT for the watcher to invoke callbacks for each operation
VERIFY that the callback received the expected set of events for the test actions
