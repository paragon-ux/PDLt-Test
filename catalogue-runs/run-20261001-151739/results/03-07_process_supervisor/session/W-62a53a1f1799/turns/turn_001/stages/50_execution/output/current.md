import subprocess
import threading
import time
import signal
import os
from collections import deque

class ProcessSupervisor:
    def __init__(self):
        self._registry = {}
        self._processes = {}
        self._restart_info = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()

    def register(self, name: str, cmd: list[str]):
        with self._lock:
            if name in self._registry:
                raise ValueError(f"Process '{name}' already registered")
            self._registry[name] = cmd
            self._restart_info[name] = {
                "attempts": deque(),  # timestamps of recent crashes
                "backoff": 1,
                "failed": False,
            }

    def start_all(self):
        with self._lock:
            for name, cmd in self._registry.items():
                self._launch(name, cmd)
        # start monitor thread
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _launch(self, name: str, cmd: list[str]):
        if self._restart_info[name]["failed"]:
            return
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        with self._lock:
            self._processes[name] = proc
        threading.Thread(target=self._waiter, args=(name, proc), daemon=True).start()

    def _waiter(self, name: str, proc: subprocess.Popen):
        returncode = proc.wait()
        # capture output (optional)
        stdout, stderr = proc.communicate()
        # Notify monitor via a queue or shared state – here we simply rely on _monitor_loop reading returncode.
        # Store exit info
        with self._lock:
            self._processes.pop(name, None)
            self._restart_info[name]["last_returncode"] = returncode
            self._restart_info[name]["last_exit_time"] = time.time()

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            time.sleep(0.5)
            with self._lock:
                for name in list(self._processes.keys()):
                    # already handled by _waiter; check if process vanished without being removed
                    pass
                # handle crashed processes
                for name, info in self._restart_info.items():
                    if info.get("failed"):
                        continue
                    if "last_returncode" in info and info["last_returncode"] != 0:
                        now = time.time()
                        # record crash timestamp
                        info["attempts"].append(now)
                        # prune old attempts (outside 60‑second window)
                        while info["attempts"] and now - info["attempts"][0] > 60:
                            info["attempts"].popleft()
                        if len(info["attempts"]) >= 5:
                            info["failed"] = True
                            continue
                        # exponential backoff
                        backoff = info["backoff"]
                        time.sleep(backoff)
                        info["backoff"] = min(backoff * 2, 30)
                        # relaunch
                        self._launch(name, self._registry[name])
                # reset per‑iteration markers
                for info in self._restart_info.values():
                    info.pop("last_returncode", None)
                    info.pop("last_exit_time", None)

    def stop_all(self):
        self._stop_event.set()
        with self._lock:
            procs = list(self._processes.items())
        for name, proc in procs:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                deadline = time.time() + 5
                while proc.poll() is None and time.time() < deadline:
                    time.sleep(0.1)
                if proc.poll() is None:
                    os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                pass
        with self._lock:
            self._processes.clear()

# --- Test harness ---
if __name__ == "__main__":
    import textwrap, sys, pathlib
    # create a temporary child script that crashes three times then exits cleanly
    script_path = pathlib.Path("crasher.py")
    script_path.write_text(textwrap.dedent('''
        import sys, time
        state_file = "crash_state.txt"
        try:
            with open(state_file, "r") as f:
                count = int(f.read())
        except FileNotFoundError:
            count = 0
        if count < 3:
            count += 1
            with open(state_file, "w") as f:
                f.write(str(count))
            print(f"Crash #{count}")
            sys.exit(1)
        else:
            print("Succeeded after crashes")
            sys.exit(0)
    '''))
    sup = ProcessSupervisor()
    sup.register("crasher", [sys.executable, str(script_path)])
    sup.start_all()
    # let it run for a while
    time.sleep(20)
    sup.stop_all()
    # cleanup
    script_path.unlink(missing_ok=True)
    try:
        pathlib.Path("crash_state.txt").unlink(missing_ok=True)
    except Exception:
        pass
    print("Test completed")
