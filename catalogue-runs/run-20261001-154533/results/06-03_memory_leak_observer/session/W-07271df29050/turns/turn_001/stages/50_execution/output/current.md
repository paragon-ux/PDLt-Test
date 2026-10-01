import weakref
import gc

class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)
        return lambda: self._listeners[event].remove(callback)  # return unsubscribe function

    def emit(self, event, *args, **kwargs):
        for cb in list(self._listeners.get(event, [])):
            cb(*args, **kwargs)

class DataProcessor:
    def __init__(self, emitter):
        self.emitter = emitter
        self.results = []
        # subscribe and keep the unsubscribe callable
        self._unsub = self.emitter.on('data', self.handle_data)

    def handle_data(self, value):
        self.results.append(value * 2)

    def close(self):
        # unsubscribe when done processing a batch
        self._unsub()
        self._unsub = None

def process_batch(emitter, batch):
    processor = DataProcessor(emitter)
    for item in batch:
        emitter.emit('data', item)
    # after processing, unsubscribe to allow GC
    processor.close()
    return processor.results

# --- Test demonstrating the leak before the fix ---
def test_leak_before_fix():
    # recreate the original buggy classes locally
    class BuggyEventEmitter:
        def __init__(self):
            self._listeners = {}
        def on(self, event, callback):
            self._listeners.setdefault(event, []).append(callback)
        def emit(self, event, *args):
            for cb in self._listeners.get(event, []):
                cb(*args)
    class BuggyDataProcessor:
        def __init__(self, emitter):
            self.emitter = emitter
            self.results = []
            self.emitter.on('data', self.handle_data)
        def handle_data(self, value):
            self.results.append(value * 2)
    def buggy_process_batch(emitter, batch):
        processor = BuggyDataProcessor(emitter)
        for item in batch:
            emitter.emit('data', item)
        return processor.results

    emitter = BuggyEventEmitter()
    dp_ref = None
    for _ in range(1000):
        dp = BuggyDataProcessor(emitter)
        dp_ref = weakref.ref(dp)
        for i in range(5):
            emitter.emit('data', i)
        # dp goes out of scope here, but listeners keep it alive
        del dp
        gc.collect()
    assert dp_ref() is not None, "Buggy processor should still be alive (memory leak)"

# --- Test after applying the fix ---
def test_no_leak_after_fix():
    emitter = EventEmitter()
    dp_ref = None
    for _ in range(1000):
        dp = DataProcessor(emitter)
        dp_ref = weakref.ref(dp)
        for i in range(5):
            emitter.emit('data', i)
        # close is called inside process_batch, but we mimic direct use here
        dp.close()
        del dp
        gc.collect()
    assert dp_ref() is None, "Processor should be garbage‑collected after unsubscribe"

if __name__ == "__main__":
    test_leak_before_fix()
    test_no_leak_after_fix()
    print("All tests passed")
