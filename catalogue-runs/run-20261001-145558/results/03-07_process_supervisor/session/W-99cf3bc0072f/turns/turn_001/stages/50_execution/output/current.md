import subprocess
import threading
import signal
import time
from collections import defaultdict

class ProcessInfo:
    def __init__(self, name, cmd):
        self.name = name
        self.cmd = cmd
        self.process = None
        self.restart_attempts = []  # timestamps of restart attempts
        self.failed = False
        self.backoff = 1  # current backoff seconds
        self.lock = threading.Lock()

class Supervisor:
    def __init__(self):
        self.registry = {}
        self.running = {}
        self.monitor_thread = None
        self.stop_event = threading.Event()

    def register(self, name, cmd):
        """Register a named process with its command line (list of args)."""
        if name in self.registry:
            raise ValueError(f"Process {name} already registered")
        self.registry[name] = ProcessInfo(name, cmd)

    def _launch(self, info: ProcessInfo):
        proc = subprocess.Popen(info.cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        info.process = proc
        info.backoff = 1
        info.failed = False
        return proc

    def start_all(self):
        """Launch all registered processes."""
        for info in self.registry.values():
            self._launch(info)
        self.monitor_thread = threading.Thread(target=self._monitor, daemon=True)
        self.monitor_thread.start()

    def _monitor(self):
        while not self.stop_event.is_set():
            for info in list(self.registry.values()):
                if info.failed:
                    continue
                proc = info.process
                if proc is None:
                    continue
                ret = proc.poll()
                if ret is not None and ret != 0:
                    now = time.time()
                    # record attempt
                    info.restart_attempts.append(now)
                    # prune attempts older than 60 seconds
                    info.restart_attempts = [t for t in info.restart_attempts if now - t <= 60]
                    if len(info.restart_attempts) >= 5:
                        info.failed = True
                        continue
                    # exponential backoff
                    time.sleep(info.backoff)
                    info.backoff = min(info.backoff * 2, 30)
                    # restart
                    self._launch(info)
                elif ret == 0:
                    # normal exit, do not restart
                    info.process = None
            time.sleep(0.1)

    def stop_all(self):
        """Gracefully terminate all children (SIGTERM then SIGKILL after 5 seconds)."""
        self.stop_event.set()
        for info in self.registry.values():
            proc = info.process
            if proc and proc.poll() is None:
                proc.send_signal(signal.SIGTERM)
        # wait up to 5 seconds
        deadline = time.time() + 5
        while time.time() < deadline:
            if all(info.process.poll() is not None for info in self.registry.values() if info.process):
                break
            time.sleep(0.1)
        # kill remaining
        for info in self.registry.values():
            proc = info.process
            if proc and proc.poll() is None:
                proc.kill()
        # join monitor thread
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)

# ------- Test -------
if __name__ == "__main__":
    import os
    # Create a temporary child script that crashes 3 times then succeeds
    child_path = "child_script.py"
    with open(child_path, "w") as f:
        f.write("""
import os, sys, time
counter_file = 'counter.txt'
if not os.path.exists(counter_file):
    count = 0
else:
    with open(counter_file) as cf:
        count = int(cf.read())
count += 1
with open(counter_file, 'w') as cf:
    cf.write(str(count))
if count <= 3:
    sys.exit(1)  # crash
print('Child succeeded on attempt', count)
""")
    sup = Supervisor()
    sup.register('child', ['python', child_path])
    sup.start_all()
    # Let it run enough time for retries
    time.sleep(20)
    sup.stop_all()
    # Clean up
    if os.path.exists(child_path):
        os.remove(child_path)
    if os.path.exists('counter.txt'):
        os.remove('counter.txt')
    print('Test completed')
