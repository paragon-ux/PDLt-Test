import os
import time
import threading
from typing import Callable, Dict

def _snapshot_directory(root: str) -> Dict[str, float]:
    """Return a mapping from file path to its modification time.
    Directories are also included to detect creation/deletion of subfolders.
    """
    snapshot = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # include directories
        for d in dirnames:
            path = os.path.join(dirpath, d)
            try:
                snapshot[path] = os.stat(path).st_mtime
            except FileNotFoundError:
                continue
        # include files
        for f in filenames:
            path = os.path.join(dirpath, f)
            try:
                snapshot[path] = os.stat(path).st_mtime
            except FileNotFoundError:
                continue
    return snapshot

def watch(directory_path: str, callback: Callable[[str, str], None], interval: float = 1.0):
    """Poll *directory_path* every *interval* seconds and invoke *callback* for changes.

    The callback receives two arguments: ``event_type`` (one of ``"created"``,
    ``"deleted"``, ``"modified"``) and the absolute ``filepath`` of the affected
    entry.
    """
    if not os.path.isdir(directory_path):
        raise ValueError(f"{directory_path!r} is not a directory")

    stop_event = threading.Event()
    thread = threading.Thread(target=_watch_worker, args=(directory_path, callback, interval, stop_event), daemon=True)
    thread.start()
    return stop_event

def _watch_worker(root: str, callback: Callable[[str, str], None], interval: float, stop_event: threading.Event):
    previous = _snapshot_directory(root)
    while not stop_event.is_set():
        time.sleep(interval)
        current = _snapshot_directory(root)
        # Detect created files/directories
        for path in current:
            if path not in previous:
                callback("created", path)
            else:
                # Detect modified files (directories' mtime may also change)
                if current[path] != previous[path]:
                    callback("modified", path)
        # Detect deleted files/directories
        for path in previous:
            if path not in current:
                callback("deleted", path)
        previous = current

# ------------------- Automated Test -------------------
if __name__ == "__main__":
    import tempfile
    import shutil

    # Record events received by the callback
    events = []
    def record(event_type: str, path: str):
        events.append((event_type, os.path.relpath(path, tmpdir)))

    # Create a temporary directory for the test
    tmpdir = tempfile.mkdtemp()
    try:
        stop = watch(tmpdir, record, interval=0.2)
        # Give the watcher a moment to start
        time.sleep(0.3)

        # 1. Create a file
        file_path = os.path.join(tmpdir, "test.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("hello")
        time.sleep(0.4)

        # 2. Modify the file
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(" world")
        time.sleep(0.4)

        # 3. Delete the file
        os.remove(file_path)
        time.sleep(0.4)

        # 4. Create a subdirectory
        sub_dir = os.path.join(tmpdir, "sub")
        os.mkdir(sub_dir)
        time.sleep(0.4)

        # 5. Delete the subdirectory
        os.rmdir(sub_dir)
        time.sleep(0.4)

        # Stop the watcher
        stop.set()
        time.sleep(0.2)  # ensure thread exits

        # Expected events (order may vary because of poll timing)
        expected = {
            "created": {"test.txt", "sub"},
            "modified": {"test.txt"},
            "deleted": {"test.txt", "sub"},
        }
        observed = {etype: set() for etype in expected}
        for etype, path in events:
            observed[etype].add(path)

        assert expected == observed, f"Mismatch: expected {expected}, got {observed}"
        print("All expected events were detected.")
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
