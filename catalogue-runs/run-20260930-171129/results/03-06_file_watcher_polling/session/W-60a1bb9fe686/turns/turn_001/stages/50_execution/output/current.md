import os
import time
import threading
from typing import Callable, Dict, Tuple

EventCallback = Callable[[str, str], None]

def _snapshot(directory: str) -> Dict[str, Tuple[float, bool]]:
    """Return a mapping from path to (mtime, is_dir)."""
    snapshot = {}
    for root, dirs, files in os.walk(directory):
        for name in dirs:
            path = os.path.join(root, name)
            try:
                stat = os.stat(path)
                snapshot[path] = (stat.st_mtime, True)
            except FileNotFoundError:
                continue
        for name in files:
            path = os.path.join(root, name)
            try:
                stat = os.stat(path)
                snapshot[path] = (stat.st_mtime, False)
            except FileNotFoundError:
                continue
    return snapshot

def watch(directory: str, callback: EventCallback, interval: float = 1.0) -> threading.Thread:
    """Poll *directory* every *interval* seconds and invoke *callback* for changes.

    The *callback* receives two arguments: ``event_type`` (one of
    ``"created"``, ``"deleted"``, ``"modified"``) and the absolute ``filepath``.
    The function returns a ``threading.Thread`` that runs the watcher; callers
    should ``join()`` the thread to stop it (the thread stops when ``stop`` is
    set on the returned object).
    """
    stop_event = threading.Event()
    def _run():
        previous = _snapshot(directory)
        while not stop_event.is_set():
            time.sleep(interval)
            current = _snapshot(directory)
            # Detect created and modified
            for path, (mtime, is_dir) in current.items():
                if path not in previous:
                    callback('created', path)
                else:
                    prev_mtime, _ = previous[path]
                    if mtime != prev_mtime:
                        callback('modified', path)
            # Detect deletions
            for path in previous:
                if path not in current:
                    callback('deleted', path)
            previous = current
    thread = threading.Thread(target=_run, daemon=True)
    thread.stop = stop_event  # attach stop handle
    thread.start()
    return thread

# ---- Test ----
if __name__ == "__main__":
    import tempfile
    import shutil
    events = []
    def collector(event_type, path):
        events.append((event_type, os.path.relpath(path, tmpdir)))
    with tempfile.TemporaryDirectory() as tmpdir:
        watcher = watch(tmpdir, collector, interval=0.2)
        # create a file
        f_path = os.path.join(tmpdir, "file.txt")
        with open(f_path, "w") as f:
            f.write("hello")
        time.sleep(0.5)
        # modify the file
        with open(f_path, "a") as f:
            f.write(" world")
        time.sleep(0.5)
        # create a subdirectory and file inside it
        sub_dir = os.path.join(tmpdir, "sub")
        os.mkdir(sub_dir)
        sub_file = os.path.join(sub_dir, "inner.txt")
        with open(sub_file, "w") as f:
            f.write("inner")
        time.sleep(0.5)
        # delete a file
        os.remove(f_path)
        time.sleep(0.5)
        # delete subdirectory
        shutil.rmtree(sub_dir)
        time.sleep(0.5)
        # stop watcher
        watcher.stop.set()
        watcher.join()
    # Simple verification
    expected = {
        ('created', 'file.txt'),
        ('modified', 'file.txt'),
        ('created', os.path.join('sub')),  # directory creation reported as created
        ('created', os.path.join('sub', 'inner.txt')),
        ('deleted', 'file.txt'),
        ('deleted', os.path.join('sub', 'inner.txt')),
        ('deleted', os.path.join('sub')),
    }
    observed = set(events)
    missing = expected - observed
    extra = observed - expected
    print("Missing events:", missing)
    print("Extra events:", extra)
    assert not missing, "Not all events were detected"
    print("All events detected successfully.")
