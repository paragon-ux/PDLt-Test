# Correct with a different interface: the original is kept; the fixed emitter
# holds bound methods through WeakMethod and prunes dead ones as it emits.
import weakref


class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, *args):
        for cb in self._listeners.get(event, []):
            cb(*args)


class WeakEventEmitter:
    def __init__(self):
        self._listeners = {}

    def subscribe(self, event, callback):
        ref = weakref.WeakMethod(callback) if hasattr(callback, "__self__") else (lambda cb=callback: cb)
        self._listeners.setdefault(event, []).append(ref)

    def emit(self, event, *args):
        live = []
        for ref in self._listeners.get(event, []):
            cb = ref()
            if cb is not None:
                live.append(ref)
                cb(*args)
        self._listeners[event] = live


class DataProcessor:
    def __init__(self, emitter):
        self.results = []
        subscribe = getattr(emitter, "subscribe", None) or emitter.on
        subscribe('data', self.handle_data)

    def handle_data(self, value):
        self.results.append(value * 2)


def process_batch_original(emitter, batch):
    processor = DataProcessor(emitter)
    for item in batch:
        emitter.emit('data', item)
    return processor.results


def process_batch_fixed(emitter, batch):
    processor = DataProcessor(emitter)
    for item in batch:
        emitter.emit('data', item)
    results = processor.results
    del processor
    return results
