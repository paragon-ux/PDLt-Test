import subprocess
import signal
import threading
import time
from collections import deque
from typing import Dict, List, Optional

class ProcessEntry:
    def __init__(self, name: str, cmd: List[str]):
        self.name = name
        self.cmd = cmd
        self.process: Optional[subprocess.Popen] = None
        self.restart_times: deque[float] = deque()
        self.failed = False
        self.backoff = 1  # seconds, start at 1

    def _record_restart(self):
        now = time.time()
        self.restart_times.append(now)
        # prune entries older than 60 seconds
        while self.restart_times and now - self.restart_times[0] > 60:
            self.restart_times.popleft()

    def should_give_up(self) -> bool:
        return len(self.restart_times) >= 5

    def reset_backoff(self):
        self.backoff = 1

    def increase_backoff(self):
        self.backoff = min(self.backoff * 2, 30)

class Supervisor:
    def __init__(self):
        self.registry: Dict[str, ProcessEntry] = {}
        self.lock = threading.Lock()
        self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self._stop_event = threading.Event()
        self.monitor_thread.start()

    def register(self, name: str, cmd: List[str]):
        with self.lock:
            if name in self.registry:
                raise ValueError(f"Process {name!r} already registered")
            self.registry[name] = ProcessEntry(name, cmd)

    def start_all(self):
        with self.lock:
            for entry in self.registry.values():
                if entry.process is None or entry.process.poll() is not None:
                    self._launch(entry)

    def stop_all(self):
        self._stop_event.set()
        with self.lock:
            for entry in self.registry.values():
                if entry.process and entry.process.poll() is None:
                    try:
                        entry.process.send_signal(signal.SIGTERM)
                    except Exception:
                        pass
                    try:
                        entry.process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        try:
                            entry.process.kill()
                        except Exception:
                            pass
        self.monitor_thread.join(timeout=1)

    def _launch(self, entry: ProcessEntry):
        try:
            entry.process = subprocess.Popen(entry.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            entry.reset_backoff()
        except Exception as e:
            print(f"Failed to launch {entry.name}: {e}")

    def _restart_with_backoff(self, entry: ProcessEntry):
        if entry.failed:
            return
        if entry.should_give_up():
            entry.failed = True
            print(f"Process {entry.name} marked as FAILED after excessive restarts.")
            return
        time.sleep(entry.backoff)
        entry._record_restart()
        entry.increase_backoff()
        self._launch(entry)
        print(f"Restarted {entry.name} with backoff {entry.backoff}s")

    def _monitor(self):
        while not self._stop_event.is_set():
            with self.lock:
                for entry in list(self.registry.values()):
                    if entry.process is None:
                        continue
                    ret = entry.process.poll()
                    if ret is not None and ret != 0:
                        # non‑zero exit, schedule restart
                        threading.Thread(target=self._restart_with_backoff, args=(entry,)).start()
            time.sleep(0.5)

# Test script
if __name__ == "__main__":
    sup = Supervisor()
    # The test child script crashes three times then exits with 0.
    # Create a temporary script file.
    import pathlib, sys, os
    script_path = pathlib.Path("test_child.py")
    script_path.write_text(
        "import sys, time\n"
        "count = int(os.getenv('CRASH_COUNT', '0'))\n"
        "if count < 3:\n"
        "    print('crashing', count)\n"
        "    sys.exit(1)\n"
        "else:\n"
        "    print('succeeded')\n"
        "    sys.exit(0)\n"
    )
    # Wrapper to increment environment variable on each launch
    def make_cmd():
        return [sys.executable, str(script_path)]
    sup.register('test', make_cmd())
    sup.start_all()
    # Let the supervisor run for a while to observe restarts.
    try:
        time.sleep(30)
    finally:
        sup.stop_all()
