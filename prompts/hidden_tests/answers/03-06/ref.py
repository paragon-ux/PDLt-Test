import os
import time


def snapshot(directory):
    state = {}
    for root, dirs, files in os.walk(directory):
        for name in dirs:
            path = os.path.join(root, name)
            state[path] = ("dir", None)
        for name in files:
            path = os.path.join(root, name)
            try:
                st = os.stat(path)
            except FileNotFoundError:
                continue
            state[path] = ("file", (st.st_mtime_ns, st.st_size))
    return state


def diff(before, after, callback):
    for path in after.keys() - before.keys():
        callback("created", path)
    for path in before.keys() - after.keys():
        callback("deleted", path)
    for path in after.keys() & before.keys():
        if after[path][0] == "file" and after[path] != before[path]:
            callback("modified", path)


def watch(directory, callback, interval=1.0, stop_event=None):
    previous = snapshot(directory)
    while stop_event is None or not stop_event.is_set():
        time.sleep(interval)
        current = snapshot(directory)
        diff(previous, current, callback)
        previous = current
