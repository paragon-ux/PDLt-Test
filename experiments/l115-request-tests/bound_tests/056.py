import io
import json

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
    handler = RecordingHandler()
    data = '{"key": "value"}'
    stream = io.StringIO(data)
    parse(stream, handler, bufsize=10)
    expected = [
        'object_start',
        ('key', 'key'),
        ('string', 'value'),
        'object_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_simple_array():
    handler = RecordingHandler()
    data = '[1, 2, 3]'
    stream = io.StringIO(data)
    parse(stream, handler, bufsize=10)
    expected = [
        'array_start',
        ('number', 1),
        ('number', 2),
        ('number', 3),
        'array_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_string_escapes():
    handler = RecordingHandler()
    data = '["hello\\nworld", "tab\\there", "quote\\"here", "backslash\\\\here", "unicode\\u0041"]'
    stream = io.StringIO(data)
    parse(stream, handler, bufsize=10)
    expected = [
        'array_start',
        ('string', 'hello\nworld'),
        ('string', 'tab\there'),
        ('string', 'quote"here'),
        ('string', 'backslash\\here'),
        ('string', 'A'),
        'array_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_nested_structures():
    handler = RecordingHandler()
    data = '{"outer": {"inner": [1, 2, 3]}}'
    stream = io.StringIO(data)
    parse(stream, handler, bufsize=10)
    expected = [
        'object_start',
        ('key', 'outer'),
        'object_start',
        ('key', 'inner'),
        'array_start',
        ('number', 1),
        ('number', 2),
        ('number', 3),
        'array_end',
        'object_end',
        'object_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_streaming_large_array():
    handler = RecordingHandler()
    large_array = list(range(1, 1001))
    data = json.dumps(large_array)
    stream = io.StringIO(data)
    parse(stream, handler, bufsize=10)
    
    expected = ['array_start']
    for num in large_array:
        expected.append(('number', num))
    expected.append('array_end')
    
    assert handler.events == expected, f"Array parsing failed: expected {len(expected)} events, got {len(handler.events)}"
    assert len(handler.events) == 1002, f"Expected 1002 events, got {len(handler.events)}"

def test_json SaxParser_class():
    handler = RecordingHandler()
    data = '{"test": true}'
    stream = io.StringIO(data)
    parser = JSONSAXParser(handler, bufsize=10)
    parser.parse(stream)
    expected = [
        'object_start',
        ('key', 'test'),
        ('bool', True),
        'object_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_function():
    handler = RecordingHandler()
    data = '[null, false, true, 42, 3.14]'
    stream = io.StringIO(data)
    parse(stream, handler, bufsize=10)
    expected = [
        'array_start',
        'null',
        ('bool', False),
        ('bool', True),
        ('number', 42),
        ('number', 3.14),
        'array_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"
