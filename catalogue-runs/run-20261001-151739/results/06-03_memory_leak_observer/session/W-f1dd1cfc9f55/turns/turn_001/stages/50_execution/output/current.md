```python
import gc
import weakref
import unittest

class EventEmitter:
    def __init__(self):
        self._listeners = {}
    
    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)
    
    def off(self, event, callback):
        # Remove a specific callback if present
        lst = self._listeners.get(event)
        if lst:
            try:
                lst.remove(callback)
            except ValueError:
                pass
        # Clean up empty list
        if lst == []:
            self._listeners.pop(event, None)
    
    def emit(self, event, *args):
        for cb in list(self._listeners.get(event, [])):
            cb(*args)

class DataProcessor:
    def __init__(self, emitter):
        self.emitter = emitter
        self.results = []
        # Register listener and keep a reference for later removal
        self._callback = self.handle_data
        self.emitter.on('data', self._callback)
    
    def handle_data(self, value):
        self.results.append(value * 2)
    
    def close(self):
        # Unsubscribe the listener so the emitter no longer holds a reference
        self.emitter.off('data', self._callback)
        # Break reference cycles
        self._callback = None
        self.emitter = None

def process_batch(emitter, batch):
    processor = DataProcessor(emitter)
    for item in batch:
        emitter.emit('data', item)
    # After processing, detach listener to allow GC of processor
    processor.close()
    return processor.results

class TestMemoryLeak(unittest.TestCase):
    def count_processors(self):
        # Count live DataProcessor instances using weakref tracking
        return len([ref for ref in DataProcessor._instances if ref() is not None])

    def setUp(self):
        # Install a weakref set on the DataProcessor class to track instances
        DataProcessor._instances = weakref.WeakSet()
        orig_init = DataProcessor.__init__
        def tracking_init(self, *args, **kwargs):
            orig_init(self, *args, **kwargs)
            DataProcessor._instances.add(self)
        DataProcessor.__init__ = tracking_init
        self.emitter = EventEmitter()

    def test_leak_before_fix(self):
        # Temporarily replace DataProcessor with the original leaky version
        # (the original version had no off method and never called close)
        # Simulate the leak by not calling close()
        def leaky_process_batch(emitter, batch):
            processor = DataProcessor(emitter)  # listener added
            for item in batch:
                emitter.emit('data', item)
            # No detach here
            return processor.results
        # Run many batches and check instance count growth
        initial = self.count_processors()
        for _ in range(1000):
            leaky_process_batch(self.emitter, [1, 2, 3])
            gc.collect()
        after = self.count_processors()
        self.assertGreater(after, initial, "Processor instances should increase, indicating a leak")

    def test_no_leak_after_fix(self):
        initial = self.count_processors()
        for _ in range(1000):
            process_batch(self.emitter, [1, 2, 3])
            gc.collect()
        after = self.count_processors()
        self.assertEqual(after, initial, "Processor instances should not increase after fix")

if __name__ == '__main__':
    unittest.main()
```
