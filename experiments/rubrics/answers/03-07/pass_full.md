```python
import subprocess, sys, threading, time
from collections import deque

class Supervisor:
    def __init__(self, base=1.0, cap=30.0, window=60.0, max_crashes=5, sleep=time.sleep, now=time.monotonic):
        self.base, self.cap, self.window, self.max_crashes = base, cap, window, max_crashes
        self.sleep, self.now = sleep, now
        self.cmds, self.procs, self.crashes, self.state, self.delays = {}, {}, {}, {}, {}
        self._stop = threading.Event()

    def register(self, name, cmd):
        self.cmds[name] = cmd; self.crashes[name] = deque(); self.state[name] = "registered"; self.delays[name] = []

    def start_all(self):
        for name in self.cmds:
            threading.Thread(target=self._monitor, args=(name,), daemon=True).start()

    def _monitor(self, name):
        attempt = 0
        while not self._stop.is_set():
            proc = self.procs[name] = subprocess.Popen(self.cmds[name])
            self.state[name] = "running"
            code = proc.wait()
            if code == 0 or self._stop.is_set():
                self.state[name] = "exited"; return
            t = self.now(); q = self.crashes[name]; q.append(t)
            while q and t - q[0] > self.window: q.popleft()
            if len(q) >= self.max_crashes:
                self.state[name] = "failed"; return
            delay = min(self.cap, self.base * 2 ** attempt); attempt += 1
            self.delays[name].append(delay)
            self.state[name] = "backoff"; self.sleep(delay)

    def stop_all(self):
        self._stop.set()
        for p in self.procs.values():
            if p.poll() is None:
                p.terminate()                  # SIGTERM
                try: p.wait(timeout=5)
                except subprocess.TimeoutExpired: p.kill()   # SIGKILL

# test: the child crashes 3 times, then succeeds; its count lives in a file
import os, tempfile
def test_restarts_with_backoff():
    d = tempfile.mkdtemp(); counter = os.path.join(d, "n")
    child = ("import sys,os; p=sys.argv[1]; n=int(open(p).read()) if os.path.exists(p) else 0;"
             "open(p,'w').write(str(n+1)); sys.exit(1 if n < 3 else 0)")
    sup = Supervisor(base=0.05, cap=1.5)       # scaled time: 0.05, 0.1, 0.2
    sup.register("flaky", [sys.executable, "-c", child, counter]); sup.start_all()
    deadline = time.time() + 10
    while sup.state["flaky"] not in ("exited", "failed") and time.time() < deadline: time.sleep(0.05)
    assert sup.state["flaky"] == "exited" and open(counter).read() == "4"
    assert sup.delays["flaky"] == [0.05, 0.1, 0.2]
    sup.stop_all()
```
