# Wrong: compares only the set of paths, so modifications are never reported.
import os
import time


def watch(directory, callback, interval=1.0):
    def scan():
        return {os.path.join(r, f) for r, _d, fs in os.walk(directory) for f in fs}

    seen = scan()
    while True:
        time.sleep(interval)
        now = scan()
        for p in now - seen:
            callback("created", p)
        for p in seen - now:
            callback("deleted", p)
        seen = now
