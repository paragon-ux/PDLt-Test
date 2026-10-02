import subprocess
import threading
import time
import signal
from collections import defaultdict

class ChildProcess:
    def __init__(self, name, cmd):
        self.name = name
        self.cmd = cmd
        self.process = None
        self.restart_delay = 1  # initial backoff in seconds
        self.failures = []  # timestamps of recent failures
        self.failed = False
        self.lock = threading.Lock()

    def start(self):
        with self.lock:
            if self.failed:
                return
            self.process = subprocess.Popen(self.cmd, preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_IGN))
            threading.Thread(target=self._monitor, daemon=True).start()

    def _monitor(self):
        ret = self.process.wait()
        if ret == 0:
            return  # normal exit, do not restart
        self._handle_crash()

    def _handle_crash(self):
        now = time.time()
        self.failures = [t for t in self.failures if now - t < 60]
        self.failures.append(now)
        if len(self.failures) >= 5:
            self.failed = True
            return
        # exponential backoff up to 30s
        delay = self.restart_delay
        self.restart_delay = min(self.restart_delay * 2, 30)
        time.sleep(delay)
        self.start()

    def terminate(self):
        with self.lock:
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                self.process = None

class Supervisor:
    def __init__(self):
        self.children = {}
        self.lock = threading.Lock()

    def register(self, name, cmd):
        with self.lock:
            if name in self.children:
                raise ValueError(f"Process {name} already registered")
            self.children[name] = ChildProcess(name, cmd)

    def start_all(self):
        with self.lock:
            for child in self.children.values():
                child.start()

    def stop_all(self):
        with self.lock:
            for child in self.children.values():
                child.terminate()

# Example test harness
if __name__ == "__main__":
    import os
    # Create a temporary script that fails 3 times then succeeds
    script_path = "temp_child.py"
    with open(script_path, "w") as f:
        f.write("""
import sys, os
state_file = 'state.txt'
if os.path.exists(state_file):
    with open(state_file) as sf:
        count = int(sf.read())
else:
    count = 0
if count < 3:
    count += 1
    with open(state_file, 'w') as sf:
        sf.write(str(count))
    sys.exit(1)
else:
    sys.exit(0)
""")
    sup = Supervisor()
    sup.register('test_child', ['python', script_path])
    sup.start_all()
    # Let it run for a while to observe restarts
    time.sleep(20)
    sup.stop_all()
    os.remove(script_path)
    if os.path.exists('state.txt'):
        os.remove('state.txt')
