```python
import subprocess, time

class Supervisor:
    def __init__(self): self.cmds, self.procs = {}, {}
    def register(self, name, cmd): self.cmds[name] = cmd
    def start_all(self):
        for name, cmd in self.cmds.items(): self.procs[name] = subprocess.Popen(cmd)
    def run(self):
        while True:
            for name, p in self.procs.items():
                if p.poll() not in (None, 0):
                    time.sleep(1)                         # wait a bit, then restart
                    self.procs[name] = subprocess.Popen(self.cmds[name])
            time.sleep(0.1)
    def stop_all(self):
        for p in self.procs.values(): p.kill()
```
Test: a child that exits 1 three times then 0 is restarted three times.
