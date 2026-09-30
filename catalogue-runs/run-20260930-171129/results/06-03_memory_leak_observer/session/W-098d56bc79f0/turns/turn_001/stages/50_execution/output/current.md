# Fixed implementation with listener unsubscription and memory leak test

class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)
        return (event, callback)  # return a handle for removal

    def off(self, handle):
        event, callback = handle
        listeners = self._listeners.get(event, [])
        if callback in listeners:
            listeners.remove(callback)
            if not listeners:
                del self._listeners[event]

    def emit(self, event, *args):
        for cb in list(self._listeners.get(event, [])):
            cb(*args)

class DataProcessor:
    def __init__(self, emitter):
        self.emitter = emitter
        self.results = []
        # keep the handle so we can unregister later
        self._handle = self.emitter.on('data', self.handle_data)

    def handle_data(self, value):
        self.results.append(value * 2)

    def cleanup(self):
        # unregister the listener to allow GC of this instance
        self.emitter.off(self._handle)
        self._handle = None

def process_batch(emitter, batch):
    processor = DataProcessor(emitter)
    for item in batch:
        emitter.emit('data', item)
    # after processing, unregister listener
    processor.cleanup()
    return processor.results

# ---------------------------------------------------------------------------
# Test demonstrating memory leak before fix and stability after fix.
# We simulate the "before" scenario by using a version of DataProcessor that
# does NOT unregister its listener. Then we compare memory usage with the
# fixed version above.
# ---------------------------------------------------------------------------
import tracemalloc
import gc

def run_leak_test(iterations=5000, batch_size=10):
    """Run process_batch many times and record peak memory usage.
    Returns a list of peak memory (in KiB) after each iteration.
    """
    emitter = EventEmitter()
    peaks = []
    for i in range(iterations):
        batch = list(range(batch_size))
        _ = process_batch(emitter, batch)
        # force collection and capture memory snapshot
        gc.collect()
        current, peak = tracemalloc.get_traced_memory()
        peaks.append(peak // 1024)  # KiB
    tracemalloc.stop()
    return peaks

if __name__ == "__main__":
    # Warm‑up tracemalloc
    tracemalloc.start()
    # Run with the fixed implementation
    fixed_peaks = run_leak_test()
    # Reset and run a leak‑prone version (no cleanup)
    tracemalloc.start()
    class LeakyDataProcessor:
        def __init__(self, emitter):
            self.emitter = emitter
            self.results = []
            self.emitter.on('data', self.handle_data)
        def handle_data(self, value):
            self.results.append(value * 2)
    def leaky_process_batch(emitter, batch):
        processor = LeakyDataProcessor(emitter)
        for item in batch:
            emitter.emit('data', item)
        return processor.results
    def run_leaky_test(iterations=5000, batch_size=10):
        emitter = EventEmitter()
        peaks = []
        for i in range(iterations):
            batch = list(range(batch_size))
            _ = leaky_process_batch(emitter, batch)
            gc.collect()
            current, peak = tracemalloc.get_traced_memory()
            peaks.append(peak // 1024)
        tracemalloc.stop()
        return peaks
    leaky_peaks = run_leaky_test()
    # Simple reporting
    print("Fixed implementation peak memory (KiB) after last iteration:", fixed_peaks[-1])
    print("Leaky implementation peak memory (KiB) after last iteration:", leaky_peaks[-1])
    # Assert that the fixed version does not grow unboundedly
    assert fixed_peaks[-1] < leaky_peaks[-1] * 0.5, "Memory usage did not stabilize after fix"
