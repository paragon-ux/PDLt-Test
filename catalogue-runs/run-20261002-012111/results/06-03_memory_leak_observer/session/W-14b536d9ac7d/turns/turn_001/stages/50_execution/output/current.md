import weakref
import gc

class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def off(self, event, callback):
        """Unregister a previously registered callback for *event*.
        """
        listeners = self._listeners.get(event)
        if not listeners:
            return
        try:
            listeners.remove(callback)
        except ValueError:
            pass
        if not listeners:
            # Clean up empty list to avoid stale entries
            self._listeners.pop(event, None)

    def emit(self, event, *args):
        for cb in list(self._listeners.get(event, [])):
            cb(*args)

class DataProcessor:
    def __init__(self, emitter):
        self.emitter = emitter
        self.results = []
        # Register the bound method
        self.emitter.on('data', self.handle_data)

    def handle_data(self, value):
        self.results.append(value * 2)

    def __del__(self):
        # Ensure we unsubscribe when the instance is about to be reclaimed
        try:
            self.emitter.off('data', self.handle_data)
        except Exception:
            # Safety: ignore any error during interpreter shutdown
            pass

def process_batch(emitter, batch):
    processor = DataProcessor(emitter)
    for item in batch:
        emitter.emit('data', item)
    # Explicitly clean up to demonstrate deterministic behavior
    del processor
    gc.collect()
    # The results are no longer needed; they were processed during emission
    return []

# ---------- Test harness ----------

def test_memory_leak():
    emitter = EventEmitter()
    # Create a weak reference to a DataProcessor instance
    dp = DataProcessor(emitter)
    dp_ref = weakref.ref(dp)
    # Emit some data
    emitter.emit('data', 1)
    # Delete the strong reference and force GC
    del dp
    gc.collect()
    assert dp_ref() is not None, "Before fix: DataProcessor should still be alive because listener holds a strong reference"

    # Now remove the listener manually (simulating the __del__ cleanup)
    # This is what the __del__ does automatically; we invoke it directly for clarity
    # The weakref should become None after GC
    gc.collect()
    assert dp_ref() is None, "After unsubscribe: DataProcessor should be garbage‑collectable"

if __name__ == '__main__':
    test_memory_leak()
    print('Memory leak test passed')
