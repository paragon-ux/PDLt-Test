import io
import json

class RecordingHandler(SAXHandler):
    def __init__(self):
        self.events = []
        self.current_object = None
        self.current_array = None
        
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
    stream = io.StringIO('{"name": "John", "age": 30}')
    parse(stream, handler, 10)
    
    expected = [
        'object_start',
        ('key', 'name'),
        ('string', 'John'),
        ('key', 'age'),
        ('number', 30),
        'object_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_simple_array():
    handler = RecordingHandler()
    stream = io.StringIO('[1, 2, 3]')
    parse(stream, handler, 10)
    
    expected = [
        'array_start',
        ('number', 1),
        ('number', 2),
        ('number', 3),
        'array_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_nested_structure():
    handler = RecordingHandler()
    stream = io.StringIO('{"items": [1, {"nested": true}]}')
    parse(stream, handler, 10)
    
    expected = [
        'object_start',
        ('key', 'items'),
        'array_start',
        ('number', 1),
        'object_start',
        ('key', 'nested'),
        ('bool', True),
        'object_end',
        'array_end',
        'object_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_string_escapes():
    handler = RecordingHandler()
    stream = io.StringIO('"line1\\nline2\\ttab"')
    parse(stream, handler, 10)
    
    expected = [('string', 'line1\nline2\ttab')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_unicode_escape():
    handler = RecordingHandler()
    stream = io.StringIO('"\\u0041\\u0042"')
    parse(stream, handler, 10)
    
    expected = [('string', 'AB')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_boolean_and_null():
    handler = RecordingHandler()
    stream = io.StringIO('[true, false, null]')
    parse(stream, handler, 10)
    
    expected = [
        'array_start',
        ('bool', True),
        ('bool', False),
        'null',
        'array_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_large_array_streaming():
    handler = RecordingHandler()
    large_array = '[' + ','.join(str(i) for i in range(1000)) + ']'
    stream = io.StringIO(large_array)
    parse(stream, handler, 10)
    
    assert handler.events[0] == 'array_start', "Array should start"
    assert handler.events[-1] == 'array_end', "Array should end"
    
    number_events = [event for event in handler.events if isinstance(event, tuple) and event[0] == 'number']
    assert len(number_events) == 1000, f"Expected 1000 numbers, got {len(number_events)}"
    
    for i, event in enumerate(number_events):
        assert event[1] == i, f"Number at position {i} should be {i}, got {event[1]}"

def test_empty_object():
    handler = RecordingHandler()
    stream = io.StringIO('{}')
    parse(stream, handler, 10)
    
    expected = ['object_start', 'object_end']
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_empty_array():
    handler = RecordingHandler()
    stream = io.StringIO('[]')
    parse(stream, handler, 10)
    
    expected = ['array_start', 'array_end']
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_float_numbers():
    handler = RecordingHandler()
    stream = io.StringIO('[3.14, 2.0, 0.5]')
    parse(stream, handler, 10)
    
    expected = [
        'array_start',
        ('number', 3.14),
        ('number', 2.0),
        ('number', 0.5),
        'array_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_negative_numbers():
    handler = RecordingHandler()
    stream = io.StringIO('[-1, -2.5]')
    parse(stream, handler, 10)
    
    expected = [
        'array_start',
        ('number', -1),
        ('number', -2.5),
        'array_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_chunk_size_handling():
    handler = RecordingHandler()
    stream = io.StringIO('{"a":1,"b":2}')
    parse(stream, handler, 5)  # Small chunk size
    
    expected = [
        'object_start',
        ('key', 'a'),
        ('number', 1),
        ('key', 'b'),
        ('number', 2),
        'object_end'
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"
