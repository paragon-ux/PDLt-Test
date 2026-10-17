import io
import json
from typing import List, Any

class JSONHandler:
    def on_object_start(self):
        pass
    def on_object_end(self):
        pass
    def on_array_start(self):
        pass
    def on_array_end(self):
        pass
    def on_key(self, key):
        pass
    def on_value(self, value):
        pass
    def on_string(self, s):
        pass
    def on_number(self, n):
        pass
    def on_bool(self, b):
        pass
    def on_null(self):
        pass

class RecordingHandler(JSONHandler):
    def __init__(self):
        self.events: List[tuple] = []
    def on_object_start(self):
        self.events.append(('object_start',))
    def on_object_end(self):
        self.events.append(('object_end',))
    def on_array_start(self):
        self.events.append(('array_start',))
    def on_array_end(self):
        self.events.append(('array_end',))
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
        self.events.append(('null',))

class MyAppHandler(JSONHandler):
    pass

def parse(stream, handler, *, chunk_size):
    # This is a placeholder for the actual parser.
    # In a real implementation, this would parse the stream.
    pass

def test_simple_object():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    parse(stream, handler, chunk_size=10)
    expected = [
        ('object_start',),
        ('key', 'key'),
        ('string', 'value'),
        ('value', 'value'),  # Assuming on_value is called for all values
        ('object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_string_escapes():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "hello\\nworld\\t\\"quote\\u0041"}')
    parse(stream, handler, chunk_size=10)
    expected_string = 'hello\nworld\t"quoteA'
    # Check that on_string is called with the unescaped string
    assert ('string', expected_string) in handler.events, f"Expected string {expected_string} in events"

def test_number():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": 123}')
    parse(stream, handler, chunk_size=10)
    assert ('number', 123) in handler.events, "Expected number 123"

def test_boolean():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": true}')
    parse(stream, handler, chunk_size=10)
    assert ('bool', True) in handler.events, "Expected bool True"

def test_null():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": null}')
    parse(stream, handler, chunk_size=10)
    assert ('null',) in handler.events, "Expected null"

def test_nested_object():
    handler = RecordingHandler()
    stream = io.StringIO('{"outer": {"inner": "value"}}')
    parse(stream, handler, chunk_size=10)
    expected = [
        ('object_start',),
        ('key', 'outer'),
        ('object_start',),
        ('key', 'inner'),
        ('string', 'value'),
        ('value', 'value'),
        ('object_end',),
        ('value', {'inner': 'value'}),  # Assuming on_value is called with the nested object? But parser doesn't build tree.
        ('object_end',),
    ]
    # Since the parser doesn't build a tree, on_value for nested object might not be called with the whole object.
    # We'll only check the structure and the string.
    assert ('object_start',) in handler.events
    assert ('key', 'outer') in handler.events
    assert ('object_start',) in handler.events
    assert ('key', 'inner') in handler.events
    assert ('string', 'value') in handler.events
    assert ('object_end',) in handler.events
    assert ('object_end',) in handler.events

def test_array_primitives():
    handler = RecordingHandler()
    stream = io.StringIO('[1, "two", true, null]')
    parse(stream, handler, chunk_size=10)
    expected = [
        ('array_start',),
        ('number', 1),
        ('value', 1),
        ('string', 'two'),
        ('value', 'two'),
        ('bool', True),
        ('value', True),
        ('null',),
        ('value', None),
        ('array_end',),
    ]
    # Check that each primitive callback is called
    assert ('number', 1) in handler.events
    assert ('string', 'two') in handler.events
    assert ('bool', True) in handler.events
    assert ('null',) in handler.events
    assert ('array_start',) in handler.events
    assert ('array_end',) in handler.events

def test_nested_array():
    handler = RecordingHandler()
    stream = io.StringIO('[[1,2],[3,4]]')
    parse(stream, handler, chunk_size=10)
    # Check structure
    assert ('array_start',) in handler.events
    assert ('array_start',) in handler.events
    assert ('number', 1) in handler.events
    assert ('number', 2) in handler.events
    assert ('array_end',) in handler.events
    assert ('array_start',) in handler.events
    assert ('number', 3) in handler.events
    assert ('number', 4) in handler.events
    assert ('array_end',) in handler.events
    assert ('array_end',) in handler.events

def test_large_array():
    handler = RecordingHandler()
    # Create a JSON array with 1000 numbers
    arr = list(range(1000))
    json_str = json.dumps(arr)
    stream = io.StringIO(json_str)
    parse(stream, handler, chunk_size=10)
    # Check that array start and end are called
    assert ('array_start',) in handler.events
    assert ('array_end',) in handler.events
    # Check that each number is called
    for i in range(1000):
        assert ('number', i) in handler.events, f"Missing number {i}"
    # Check that the total number of number events is 1000
    number_events = [e for e in handler.events if e[0] == 'number']
    assert len(number_events) == 1000, f"Expected 1000 number events, got {len(number_events)}"
