# Wrong: weak references free the processors, but the dead references are never
# pruned, so the emitter's lists still grow with every call.
import weakref


class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(weakref.WeakMethod(callback))

    def emit(self, event, *args):
        for ref in self._listeners.get(event, []):
            cb = ref()
            if cb is not None:
                cb(*args)


class DataProcessor:
    def __init__(self, emitter):
        self.results = []
        emitter.on('data', self.handle_data)

    def handle_data(self, value):
        self.results.append(value * 2)


def process_batch(emitter, batch):
    processor = DataProcessor(emitter)
    for item in batch:
        emitter.emit('data', item)
    return processor.results
