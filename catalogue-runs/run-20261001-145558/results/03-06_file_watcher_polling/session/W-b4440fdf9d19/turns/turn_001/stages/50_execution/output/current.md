import os
import time
import threading
from typing import Callable

def _snapshot(root: str):
    """Return a dict mapping file paths to their modification times."""
    snapshot = {}
    for dirpath, dirnames, filenames in os.walk(root):
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                mtime = os.stat(path).st_mtime
                snapshot[path] = mtime
            except FileNotFoundError:
                # File might disappear between walk and stat
                continue
    return snapshot

def watch(watch_path: str, callback: Callable[[str, str], None], interval: float = 1.0):
    """Poll *watch_path* every *interval* seconds and invoke *callback* for changes.

    The *callback* receives two arguments: ``event_type`` (one of ``"create"``, ``"delete"``, ``"modify"``)
    and the absolute ``filepath`` where the event occurred.
    """
    previous = {}
    while True:
        current = _snapshot(watch_path)
        # Detect created files
        for path in current:
            if path not in previous:
                callback("create", path)
        # Detect deleted files
        for path in previous:
            if path not in current:
                callback("delete", path)
        # Detect modified files
        for path, mtime in current.items():
            if path in previous and previous[path] != mtime:
                callback("modify", path)
        previous = current
        time.sleep(interval)

# --- Test ----------------------------------------------------------
if __name__ == "__main__":
    import tempfile
    import shutil

    events = []
    def recorder(event_type, path):
        events.append((event_type, os.path.relpath(path, tmp_dir)))

    tmp_dir = tempfile.mkdtemp()
    try:
        watcher_thread = threading.Thread(target=watch, args=(tmp_dir, recorder, 0.5), daemon=True)
        watcher_thread.start()
        # Give the watcher a moment to start
        time.sleep(0.6)
        # Create a file
        file_path = os.path.join(tmp_dir, "test.txt")
        with open(file_path, "w") as f:
            f.write("hello")
        time.sleep(0.6)
        # Modify the file
        with open(file_path, "a") as f:
            f.write(" world")
        time.sleep(0.6)
        # Delete the file
        os.remove(file_path)
        time.sleep(0.6)
        # Verify events
        expected = [("create", "test.txt"), ("modify", "test.txt"), ("delete", "test.txt")]
        assert all(ev in events for ev in expected), f"Missing events: expected {expected}, got {events}"
        print("All events detected successfully.")
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)
