import os
import time
import threading
from typing import Callable, Dict

def watch(directory: str, callback: Callable[[str, str], None], interval: float = 1.0) -> threading.Thread:
    """Watch *directory* recursively for file system changes.

    Parameters
    ----------
    directory: str
        Root directory to monitor.
    callback: Callable[[str, str], None]
        Function called with ``event_type`` ("created", "modified", "deleted")
        and the absolute *filepath* of the affected entry.
    interval: float, optional
        Seconds to wait between polls. Default is 1.0.

    Returns
    -------
    threading.Thread
        The background thread running the watcher. The thread is marked as daemon
        so it will not block interpreter shutdown.
    """
    stop_event = threading.Event()

    def _poll():
        prev_snapshot: Dict[str, float] = {}
        while not stop_event.is_set():
            current_snapshot: Dict[str, float] = {}
            # Walk the directory tree
            for root, dirs, files in os.walk(directory):
                for name in dirs + files:
                    path = os.path.join(root, name)
                    try:
                        stat = os.stat(path)
                        current_snapshot[path] = stat.st_mtime
                    except FileNotFoundError:
                        # Path vanished between os.walk and os.stat – ignore
                        continue
            # Detect creations and modifications
            for path, mtime in current_snapshot.items():
                if path not in prev_snapshot:
                    callback('created', path)
                elif prev_snapshot[path] != mtime:
                    callback('modified', path)
            # Detect deletions
            for path in set(prev_snapshot) - set(current_snapshot):
                callback('deleted', path)
            prev_snapshot = current_snapshot
            stop_event.wait(interval)

    thread = threading.Thread(target=_poll, daemon=True)
    thread.start()
    # Attach a stop method for graceful shutdown in tests
    thread.stop = stop_event.set  # type: ignore
    return thread

# ----------------- Test Suite -----------------#
import tempfile
import shutil
import unittest

class WatcherTest(unittest.TestCase):
    def setUp(self):
        self.events = []
        self.temp_dir = tempfile.mkdtemp()
        self.watcher = watch(self.temp_dir, self._record_event, interval=0.1)
        # Give the watcher a moment to initialise
        time.sleep(0.2)

    def tearDown(self):
        # Stop the background thread
        self.watcher.stop()
        self.watcher.join()
        shutil.rmtree(self.temp_dir)

    def _record_event(self, event_type: str, path: str):
        # Record events in a deterministic order
        self.events.append((event_type, os.path.relpath(path, self.temp_dir)))

    def test_create_modify_delete(self):
        # Create a file
        file_path = os.path.join(self.temp_dir, 'test.txt')
        with open(file_path, 'w') as f:
            f.write('hello')
        time.sleep(0.3)  # allow poll to detect

        # Modify the file
        with open(file_path, 'a') as f:
            f.write(' world')
        time.sleep(0.3)

        # Delete the file
        os.remove(file_path)
        time.sleep(0.3)

        # Verify events
        # The order may vary (creation can be seen before modification), so we sort
        expected = [('created', 'test.txt'), ('modified', 'test.txt'), ('deleted', 'test.txt')]
        self.assertCountEqual(self.events, expected)

if __name__ == '__main__':
    unittest.main()
