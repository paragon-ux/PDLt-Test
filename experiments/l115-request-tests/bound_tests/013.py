import io
import json
from typing import List, Tuple, Any

class RecordingHandler:
    def __init__(self):
        self.events: List[Tuple[str, Any]] = []
    
    def on_object_start(self):
        self.events.append(('on_object_start',))
    
    def on_object_end(self):
        self.events.append(('on_object_end',))
    
    def on_array_start(self):
        self.events.append(('on_array_start',))
    
    def on_array_end(self):
        self.events.append(('on_array_end',))
    
    def on_key(self, key: str):
        self.events.append(('on_key', key))
    
    def on_value(self, value: Any):
        self.events.append(('on_value', value))
    
    def on_string(self, s: str):
        self.events.append(('on_string', s))
    
    def on_number(self, n: float):
        self.events.append(('on_number', n))
    
    def on_bool(self, b: bool):
        self.events.append(('on_bool', b))
    
    def on_null(self):
        self.events.append(('on_null',))

def test_simple_object():
    """Test parsing a simple JSON object with various value types."""
    data = '{"name": "John", "age": 30, "active": true, "address": null}'
    stream = io.StringIO(data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('on_object_start',),
        ('on_key', 'name'),
        ('on_string', 'John'),
        ('on_key', 'age'),
        ('on_number', 30.0),
        ('on_key', 'active'),
        ('on_bool', True),
        ('on_key', 'address'),
        ('on_null',),
        ('on_object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_nested_structures():
    """Test parsing nested objects and arrays."""
    data = '{"outer": {"inner": [1, 2, {"deep": "value"}]}}'
    stream = io.StringIO(data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=15)
    
    expected = [
        ('on_object_start',),
        ('on_key', 'outer'),
        ('on_object_start',),
        ('on_key', 'inner'),
        ('on_array_start',),
        ('on_number', 1.0),
        ('on_number', 2.0),
        ('on_object_start',),
        ('on_key', 'deep'),
        ('on_string', 'value'),
        ('on_object_end',),
        ('on_array_end',),
        ('on_object_end',),
        ('on_object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_string_escapes():
    """Test handling of string escape sequences."""
    data = '{"text": "line1\\nline2\\ttab", "quote": "he said \\"hello\\""}'
    stream = io.StringIO(data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('on_object_start',),
        ('on_key', 'text'),
        ('on_string', 'line1\nline2\ttab'),
        ('on_key', 'quote'),
        ('on_string', 'he said "hello"'),
        ('on_object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_unicode_escape():
    """Test handling of unicode escape sequences."""
    data = '{"greek": "\\u03b1\\u03b2\\u03b3"}'
    stream = io.StringIO(data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('on_object_start',),
        ('on_key', 'greek'),
        ('on_string', 'αβγ'),
        ('on_object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_large_array_streaming():
    """Test streaming a 1000-element array with minimal memory usage."""
    # Create a JSON array with 1000 numbers
    array_data = [str(i) for i in range(1000)]
    json_data = '[' + ','.join(array_data) + ']'
    
    # Use a small chunk size to force streaming
    stream = io.StringIO(json_data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=50)
    
    # Verify array structure
    assert handler.events[0] == ('on_array_start',)
    assert handler.events[-1] == ('on_array_end',)
    
    # Verify all 1000 numbers are parsed
    number_events = [event for event in handler.events if event[0] == 'on_number']
    assert len(number_events) == 1000
    
    # Verify numbers are in order
    for i, event in enumerate(number_events):
        assert event[1] == float(i)
    
    # Verify no intermediate structures were created (only array callbacks)
    structural_events = [event for event in handler.events if event[0] in 
                        ('on_object_start', 'on_object_end', 'on_array_start', 'on_array_end')]
    assert len(structural_events) == 2  # Only the outer array

def test_empty_containers():
    """Test parsing empty objects and arrays."""
    data = '{"empty_obj": {}, "empty_arr": []}'
    stream = io.StringIO(data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('on_object_start',),
        ('on_key', 'empty_obj'),
        ('on_object_start',),
        ('on_object_end',),
        ('on_key', 'empty_arr'),
        ('on_array_start',),
        ('on_array_end',),
        ('on_object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_chunked_streaming():
    """Test that parsing works correctly with very small chunk sizes."""
    data = '{"a": 1, "b": [2, 3, 4], "c": "hello"}'
    stream = io.StringIO(data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=2)  # Very small chunks
    
    expected = [
        ('on_object_start',),
        ('on_key', 'a'),
        ('on_number', 1.0),
        ('on_key', 'b'),
        ('on_array_start',),
        ('on_number', 2.0),
        ('on_number', 3.0),
        ('on_number', 4.0),
        ('on_array_end',),
        ('on_key', 'c'),
        ('on_string', 'hello'),
        ('on_object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_number_formats():
    """Test parsing different number formats."""
    data = '{"int": 42, "float": 3.14, "negative": -17, "scientific": 1e10}'
    stream = io.StringIO(data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('on_object_start',),
        ('on_key', 'int'),
        ('on_number', 42.0),
        ('on_key', 'float'),
        ('on_number', 3.14),
        ('on_key', 'negative'),
        ('on_number', -17.0),
        ('on_key', 'scientific'),
        ('on_number', 1e10),
        ('on_object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_boolean_and_null():
    """Test parsing boolean and null values."""
    data = '{"true_val": true, "false_val": false, "null_val": null}'
    stream = io.StringIO(data)
    handler = RecordingHandler()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('on_object_start',),
        ('on_key', 'true_val'),
        ('on_bool', True),
        ('on_key', 'false_val'),
        ('on_bool', False),
        ('on_key', 'null_val'),
        ('on_null',),
        ('on_object_end',),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"
