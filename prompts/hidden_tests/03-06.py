"""Hidden tests for 03-06: a polling file-change detector built on os.stat.

From the prompt:
- watch(directory, callback, interval=1.0) polls the tree;
- it reports creation, deletion and modification (by mtime) through
  callback(event_type, filepath);
- it handles subdirectories being created and deleted.

**Interface.** The candidate is either a watch-like function or a class built
from (directory, callback, interval) with a start method. It runs on a daemon
thread with a short interval, since the prompt's watch() may block forever;
stop() is called afterwards if the class has one.

**Event names.** Event types are read by meaning:
- created: "creat", "add" or "new";
- deleted: "delet" or "remov";
- modified: "modif", "chang" or "updat".

**Paths.** They may be absolute or relative to the watched directory.

**Subdirectories.** Creating one that holds a file must produce a created event
for the directory or the file, and deleting it a deleted event for either.

**False reports.** A file that stays untouched must not be reported deleted.
"""
TEST_SECONDS = 60
_KINDS = {"created": ("creat", "add", "new"), "deleted": ("delet", "remov"), "modified": ("modif", "chang", "updat")}


def CANDIDATES():
    found = [_function_adapter(f) for f in functions_named("watch", "watch_directory", "poll_directory", "watch_dir")]
    for cls in classes_with("start"):
        found.append(_class_adapter(cls))
    return found


def _call(fn, directory, callback, interval):
    import inspect

    try:
        names = list(inspect.signature(fn).parameters)
    except (TypeError, ValueError):
        names = []
    if "interval" in names:
        return fn(directory, callback, interval=interval)
    if len([n for n in names if n != "self"]) >= 3:
        return fn(directory, callback, interval)
    return fn(directory, callback)


def _function_adapter(f):
    def start(directory, callback, interval):
        import threading

        threading.Thread(target=_call, args=(f, directory, callback, interval), daemon=True).start()
        return None

    start.__name__ = f.__name__
    return start


def _class_adapter(cls):
    def start(directory, callback, interval):
        import threading

        watcher = _call(cls, directory, callback, interval)
        threading.Thread(target=watcher.start, daemon=True).start()
        return watcher

    start.__name__ = f"{cls.__name__}.start"
    return start


def _kind(event_type):
    text = str(getattr(event_type, "name", event_type)).lower()
    for kind, words in _KINDS.items():
        if any(w in text for w in words):
            return kind
    return text


def test_detects_create_modify_delete_and_subdirectories(start):
    import os
    import shutil
    import threading
    import time

    root = os.path.abspath(f"hidden_watch_{os.getpid()}")
    shutil.rmtree(root, ignore_errors=True)
    os.makedirs(root)
    with open(os.path.join(root, "keep.txt"), "w") as fh:
        fh.write("unchanged")
    with open(os.path.join(root, "edit.txt"), "w") as fh:
        fh.write("v1")
    with open(os.path.join(root, "gone.txt"), "w") as fh:
        fh.write("bye")
    events, guard = [], threading.Lock()

    def callback(event_type, filepath):
        path = os.path.normcase(os.path.abspath(os.path.join(root, str(filepath))))
        with guard:
            events.append((_kind(event_type), path))

    def norm(*parts):
        return os.path.normcase(os.path.abspath(os.path.join(root, *parts)))

    def wait_for(predicate, what, seconds=4.0):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            with guard:
                if predicate(list(events)):
                    return
            time.sleep(0.05)
        with guard:
            raise AssertionError(f"no {what} event; saw {events[-12:]}")

    def has(kind, *paths):
        targets = {norm(*p) if isinstance(p, tuple) else norm(p) for p in paths}
        return lambda evs: any(k == kind and p in targets for k, p in evs)

    watcher = start(root, callback, 0.05)
    time.sleep(0.6)  # let the first snapshot be taken
    try:
        with open(os.path.join(root, "new.txt"), "w") as fh:
            fh.write("hello")
        wait_for(has("created", "new.txt"), "created new.txt")

        with open(os.path.join(root, "edit.txt"), "w") as fh:
            fh.write("v2 longer")
        later = time.time() + 5
        os.utime(os.path.join(root, "edit.txt"), (later, later))
        wait_for(has("modified", "edit.txt"), "modified edit.txt")

        os.remove(os.path.join(root, "gone.txt"))
        wait_for(has("deleted", "gone.txt"), "deleted gone.txt")

        os.makedirs(os.path.join(root, "sub"))
        with open(os.path.join(root, "sub", "inner.txt"), "w") as fh:
            fh.write("x")
        wait_for(has("created", "sub", ("sub", "inner.txt")), "created sub/ or sub/inner.txt")

        shutil.rmtree(os.path.join(root, "sub"))
        wait_for(has("deleted", "sub", ("sub", "inner.txt")), "deleted sub/ or sub/inner.txt")

        time.sleep(0.3)
        with guard:
            assert not has("deleted", "keep.txt")(events), "an untouched file was reported deleted"
    finally:
        stop = getattr(watcher, "stop", None)
        if callable(stop):
            try:
                stop()
            except Exception:  # noqa: BLE001
                pass


TESTS = [test_detects_create_modify_delete_and_subdirectories]
