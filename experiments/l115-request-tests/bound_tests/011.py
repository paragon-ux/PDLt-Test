import io

class RecordingHandler:
    def __init__(self):
        self.events = []
    def on_object_start(self):
        self.events.append('object_start')
    def on_object_end(self):
        self.events.append('object_end')
    def on_array_start(self):
        self.events.append('array_start')
    def on_array_end(self):
        self.events.append('array_end')
    def on_key(self, key):
        self.events.append(('key', key))
    def on_value(self, value):
        self.events.append(('value', value))
    def on_string(self, s):
        self.events.append(('string', s))
    def on_number(self, n):
        self.events.append(('number', n))
    def on_bool(self, b):
        self.events.append(('bool', b))
    def on_null(self):
        self.events.append('null')

def test_simple_object():
    h = RecordingHandler()
    parse(io.StringIO('{"a":1}'), h)
    assert h.events == ['object_start', ('key', 'a'), ('number', 1), 'object_end'], "Simple object callbacks mismatch"

def test_simple_array():
    h = RecordingHandler()
    parse(io.StringIO('[1,2,3]'), h)
    assert h.events == ['array_start', ('number', 1), ('number', 2), ('number', 3), 'array_end'], "Simple array callbacks mismatch"

def test_string_escapes():
    h = RecordingHandler()
    parse(io.StringIO('"hello\\nworld"'), h)
    assert h.events == [('string', 'hello\nworld')], "String escape handling mismatch"

def test_string_escapes_all():
    h = RecordingHandler()
    parse(io.StringIO('"a\\\\b\\tc\\nd\\"e\\u0041"'), h)
    assert h.events == [('string', 'a\\b\tc\nd"eA')], "String escapes all mismatch"

def test_bool_and_null():
    h = RecordingHandler()
    parse(io.StringIO('true'), h)
    assert h.events == [('bool', True)], "Bool true mismatch"
    h2 = RecordingHandler()
    parse(io.StringIO('false'), h2)
    assert h2.events == [('bool', False)], "Bool false mismatch"
    h3 = RecordingHandler()
    parse(io.StringIO('null'), h3)
    assert h3.events == ['null'], "Null mismatch"

def test_nested_structures():
    h = RecordingHandler()
    parse(io.StringIO('{"a":[1,2,{"b":3}]}'), h)
    expected = [
        'object_start',
        ('key', 'a'),
        'array_start',
        ('number', 1),
        ('number', 2),
        'object_start',
        ('key', 'b'),
        ('number', 3),
        'object_end',
        'array_end',
        'object_end'
    ]
    assert h.events == expected, "Nested structures callbacks mismatch"

def test_large_array():
    numbers = list(range(1000))
    json_str = '[' + ','.join(map(str, numbers)) + ']'
    class ChunkedStream:
        def __init__(self, data, chunk_size):
            self.data = data
            self.chunk_size = chunk_size
            self.pos = 0
        def read(self, size=-1):
            if self.pos >= len(self.data):
                return ''
            end = self.pos + self.chunk_size
            chunk = self.data[self.pos:end]
            self.pos = end
            return chunk
    stream = ChunkedStream(json_str, 10)
    h = RecordingHandler()
    parse(stream, h)
    assert h.events[0] == 'array_start', "Large array: missing array_start"
    assert h.events[-1] == 'array_end', "Large array: missing array_end"
    number_events = [e for e in h.events if isinstance(e, tuple) and e[0] == 'number']
    assert len(number_events) == 1000, f"Expected 1000 numbers, got {len(number_events)}"
    for i, ev in enumerate(number_events):
        assert ev[1] == i, f"Number at index {i} mismatch: {ev[1]}"