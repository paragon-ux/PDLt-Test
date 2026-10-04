# Wrong: lists only the top directory, so files in subdirectories are never seen
# (and a deleted directory is not reported either).
import os
import time


def watch(directory, callback, interval=1.0):
    def scan():
        out = {}
        for name in os.listdir(directory):
            path = os.path.join(directory, name)
            if os.path.isfile(path):
                out[path] = os.stat(path).st_mtime
        return out

    seen = scan()
    while True:
        time.sleep(interval)
        now = scan()
        for p in now.keys() - seen.keys():
            callback("created", p)
        for p in seen.keys() - now.keys():
            callback("deleted", p)
        for p in now.keys() & seen.keys():
            if now[p] != seen[p]:
                callback("modified", p)
        seen = now
