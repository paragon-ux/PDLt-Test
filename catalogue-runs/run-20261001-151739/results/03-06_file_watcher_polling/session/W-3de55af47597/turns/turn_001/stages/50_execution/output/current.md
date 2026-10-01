import os
import time
import threading
from typing import Callable, Dict

EventCallback = Callable[[str, str], None]

def _scan_directory(root: str) -> Dict[str, float]:
    """Recursively walk *root* and return a mapping of path → mtime.
    Only regular files and directories are tracked; symbolic links are ignored.
    """
    mtimes: Dict[str, float] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        # Record directory itself
        try:
            mtimes[dirpath] = os.stat(dirpath).st_mtime
        except FileNotFoundError:
            continue
        for name in filenames:
            path = os.path.join(dirpath, name)
            try:
                mtimes[path] = os.stat(path).st_mtime
            except FileNotFoundError:
                continue
    return mtimes

def watch(directory: str, callback: EventCallback, interval: float = 1.0) -> Callable[[], None]:
    """Poll *directory* every *interval* seconds and invoke *callback* on changes.

    The callback receives two arguments: ``event_type`` (one of ``"created"``, ``"deleted"``, ``"modified"``)
    and the absolute ``filepath`` that changed.

    The function returns a *stop* callable that, when invoked, terminates the background thread.
    """
    stop_event = threading.Event()
    previous: Dict[str, float] = {}

    def _loop() -> None:
        nonlocal previous
        while not stop_event.is_set():
            current = _scan_directory(directory)
            # Detect created entries
            for path in current:
                if path not in previous:
                    callback("created", path)
            # Detect deleted entries
            for path in previous:
                if path not in current:
                    callback("deleted", path)
            # Detect modified entries
            for path, mtime in current.items():
                if path in previous and mtime != previous[path]:
                    callback("modified", path)
            previous = current
            # Sleep respecting stop request
            stop_event.wait(interval)

    thread = threading.Thread(target=_loop, daemon=True)
    thread.start()

    def stop() -> None:
        """Signal the watcher thread to stop and wait for its termination."""
        stop_event.set()
        thread.join()

    return stop

# ---------- Test Suite ----------
if __name__ == "__main__":
    import tempfile
    import shutil

    events = []

    def recorder(event_type: str, path: str) -> None:
        events.append((event_type, os.path.relpath(path, root_dir)))

    root_dir = tempfile.mkdtemp(prefix="watch_test_")
    try:
        stop_watcher = watch(root_dir, recorder, interval=0.2)
        # Give the watcher a moment to start
        time.sleep(0.3)

        test_file = os.path.join(root_dir, "test.txt")
        # Create file
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("initial")
        time.sleep(0.3)
        # Modify file
        with open(test_file, "a", encoding="utf-8") as f:
            f.write(" more")
        time.sleep(0.3)
        # Delete file
        os.remove(test_file)
        time.sleep(0.3)
        # Stop watcher
        stop_watcher()
        # Verify events
        expected = [
            ("created", "test.txt"),
            ("modified", "test.txt"),
            ("deleted", "test.txt"),
        ]
        # Simple verification (order may vary due to timing)
        missing = [e for e in expected if e not in events]
        extra = [e for e in events if e not in expected]
        if missing:
            raise AssertionError(f"Missing expected events: {missing}")
        if extra:
            raise AssertionError(f"Unexpected extra events: {extra}")
        print("All expected events detected.")
    finally:
        shutil.rmtree(root_dir, ignore_errors=True)
