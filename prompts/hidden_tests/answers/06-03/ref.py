class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def off(self, event, callback):
        callbacks = self._listeners.get(event, [])
        if callback in callbacks:
            callbacks.remove(callback)
        if not callbacks:
            self._listeners.pop(event, None)

    def emit(self, event, *args):
        for cb in list(self._listeners.get(event, [])):
            cb(*args)


class DataProcessor:
    def __init__(self, emitter):
        self.emitter = emitter
        self.results = []
        self.emitter.on('data', self.handle_data)

    def handle_data(self, value):
        self.results.append(value * 2)

    def close(self):
        self.emitter.off('data', self.handle_data)


def process_batch(emitter, batch):
    processor = DataProcessor(emitter)
    try:
        for item in batch:
            emitter.emit('data', item)
        return processor.results
    finally:
        processor.close()
