# Correct with a different interface: PollingWatcher(path, on_change, interval)
# with start()/stop() running its own thread, Enum event types, paths relative
# to the watched directory, and files only (directories are not reported).
import enum
import os
import threading


class Change(enum.Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


class PollingWatcher:
    def __init__(self, path, on_change, interval=1.0):
        self.path, self.on_change, self.interval = path, on_change, interval
        self._stop = threading.Event()
        self._seen = self._scan()

    def _scan(self):
        out = {}
        for root, _dirs, files in os.walk(self.path):
            for f in files:
                full = os.path.join(root, f)
                try:
                    out[os.path.relpath(full, self.path)] = os.stat(full).st_mtime
                except OSError:
                    pass
        return out

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def stop(self):
        self._stop.set()

    def _run(self):
        while not self._stop.wait(self.interval):
            now = self._scan()
            for rel in sorted(now.keys() - self._seen.keys()):
                self.on_change(Change.ADDED, rel)
            for rel in sorted(self._seen.keys() - now.keys()):
                self.on_change(Change.REMOVED, rel)
            for rel in sorted(now.keys() & self._seen.keys()):
                if now[rel] != self._seen[rel]:
                    self.on_change(Change.CHANGED, rel)
            self._seen = now
