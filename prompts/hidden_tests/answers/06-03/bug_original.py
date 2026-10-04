# Wrong: the original; every DataProcessor stays subscribed forever.
class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, *args):
        for cb in self._listeners.get(event, []):
            cb(*args)


class DataProcessor:
    def __init__(self, emitter):
        self.emitter = emitter
        self.results = []
        self.emitter.on('data', self.handle_data)

    def handle_data(self, value):
        self.results.append(value * 2)


def process_batch(emitter, batch):
    processor = DataProcessor(emitter)
    for item in batch:
        emitter.emit('data', item)
    return processor.results
