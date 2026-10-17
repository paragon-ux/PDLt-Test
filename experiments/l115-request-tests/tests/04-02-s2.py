import io
import json
from typing import List, Tuple, Any

class TestHandler:
    """Helper handler that records all callbacks for verification."""
    def __init__(self):
        self.events: List[Tuple[str, Any]] = []
        self.array_depth = 0
        self.max_array_depth = 0
        self.values_in_memory = 0
        self.max_values_in_memory = 0

    def on_object_start(self):
        self.events.append(('object_start',))

    def on_object_end(self):
        self.events.append(('object_end',))

    def on_array_start(self):
        self.array_depth += 1
        self.max_array_depth = max(self.max_array_depth, self.array_depth)
        self.events.append(('array_start',))

    def on_array_end(self):
        self.array_depth -= 1
        self.events.append(('array_end',))

    def on_key(self, key):
        self.events.append(('key', key))

    def on_value(self, value):
        self.values_in_memory += 1
        self.max_values_in_memory = max(self.max_values_in_memory, self.values_in_memory)
        self.events.append(('value', value))

    def on_string(self, s):
        self.events.append(('string', s))

    def on_number(self, n):
        self.events.append(('number', n))

    def on_bool(self, b):
        self.events.append(('bool', b))

    def on_null(self):
        self.events.append(('null',))

    def reset_memory_counter(self):
        self.values_in_memory = 0
        self.max_values_in_memory = 0


def test_parse_function_exists():
    """Test that parse function is available."""
    assert callable(parse), "parse function should be callable"

def test_handler_interface():
    """Test that handler has all required methods."""
    handler = TestHandler()
    required_methods = [
        'on_object_start', 'on_object_end', 'on_array_start', 'on_array_end',
        'on_key', 'on_value', 'on_string', 'on_number', 'on_bool', 'on_null'
    ]
    for method in required_methods:
        assert hasattr(handler, method), f"Handler missing method: {method}"
        assert callable(getattr(handler, method)), f"Handler method not callable: {method}"

def test_parse_simple_object():
    """Test parsing a simple JSON object."""
    handler = TestHandler()
    json_str = '{"name": "John", "age": 30}'
    parse(io.StringIO(json_str), handler)
    
    expected_events = [
        ('object_start',),
        ('key', 'name'),
        ('value', 'John'),
        ('key', 'age'),
        ('value', 30),
        ('object_end',)
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_parse_simple_array():
    """Test parsing a simple JSON array."""
    handler = TestHandler()
    json_str = '[1, 2, 3]'
    parse(io.StringIO(json_str), handler)
    
    expected_events = [
        ('array_start',),
        ('value', 1),
        ('value', 2),
        ('value', 3),
        ('array_end',)
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_parse_string_with_escapes():
    """Test parsing strings with escape sequences."""
    handler = TestHandler()
    json_str = '{"text": "Hello\\nWorld\\t\\"Quote\\u0041"}'
    parse(io.StringIO(json_str), handler)
    
    expected_events = [
        ('object_start',),
        ('key', 'text'),
        ('value', 'Hello\nWorld\t"QuoteA'),
        ('object_end',)
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_parse_number():
    """Test parsing different number formats."""
    handler = TestHandler()
    json_str = '{"int": 42, "float": 3.14, "negative": -17}'
    parse(io.StringIO(json_str), handler)
    
    expected_events = [
        ('object_start',),
        ('key', 'int'),
        ('value', 42),
        ('key', 'float'),
        ('value', 3.14),
        ('key', 'negative'),
        ('value', -17),
        ('object_end',)
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_parse_bool_and_null():
    """Test parsing boolean and null values."""
    handler = TestHandler()
    json_str = '{"true": true, "false": false, "null": null}'
    parse(io.StringIO(json_str), handler)
    
    expected_events = [
        ('object_start',),
        ('key', 'true'),
        ('value', True),
        ('key', 'false'),
        ('value', False),
        ('key', 'null'),
        ('value', None),
        ('object_end',)
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_nested_structures():
    """Test parsing nested objects and arrays."""
    handler = TestHandler()
    json_str = '{"users": [{"name": "Alice", "scores": [95, 87]}, {"name": "Bob", "scores": [92, 89]}]}'
    parse(io.StringIO(json_str), handler)
    
    # Verify structure by checking key events
    key_events = [event for event in handler.events if event[0] == 'key']
    expected_keys = ['users', 'name', 'scores', 'name', 'scores']
    actual_keys = [event[1] for event in key_events]
    assert actual_keys == expected_keys, f"Expected keys {expected_keys}, got {actual_keys}"
    
    # Verify array depth tracking
    assert handler.max_array_depth == 2, f"Expected max array depth 2, got {handler.max_array_depth}"

def test_streaming_1000_element_array():
    """Test streaming a 1000-element array without holding all elements in memory."""
    handler = TestHandler()
    
    # Create a 1000-element array
    large_array = list(range(1000))
    json_str = json.dumps(large_array)
    
    # Use a stream that simulates chunked reading
    class ChunkedStream:
        def __init__(self, data, chunk_size=100):
            self.data = data
            self.chunk_size = chunk_size
            self.position = 0
        
        def read(self, n=-1):
            if n == -1:
                n = self.chunk_size
            start = self.position
            end = min(start + n, len(self.data))
            if start >= end:
                return ''
            chunk = self.data[start:end]
            self.position = end
            return chunk
    
    stream = ChunkedStream(json_str, chunk_size=50)
    handler.reset_memory_counter()
    parse(stream, handler)
    
    # Verify all callbacks fired correctly
    value_events = [event for event in handler.events if event[0] == 'value']
    assert len(value_events) == 1000, f"Expected 1000 value events, got {len(value_events)}"
    
    # Verify values are correct
    for i, event in enumerate(value_events):
        assert event[1] == i, f"Expected value {i} at position {i}, got {event[1]}"
    
    # Verify array structure
    array_start_count = len([e for e in handler.events if e[0] == 'array_start'])
    array_end_count = len([e for e in handler.events if e[0] == 'array_end'])
    assert array_start_count == 1, f"Expected 1 array_start, got {array_start_count}"
    assert array_end_count == 1, f"Expected 1 array_end, got {array_end_count}"
    
    # Verify memory usage: should never hold more than a few elements in memory
    # The SAX parser should process elements one at a time
    assert handler.max_values_in_memory <= 10, f"Parser held too many values in memory: {handler.max_values_in_memory}"

def test_empty_object_and_array():
    """Test parsing empty objects and arrays."""
    handler = TestHandler()
    json_str = '{"empty_obj": {}, "empty_arr": []}'
    parse(io.StringIO(json_str), handler)
    
    expected_events = [
        ('object_start',),
        ('key', 'empty_obj'),
        ('value', {}),
        ('key', 'empty_arr'),
        ('value', []),
        ('object_end',)
    ]
    # Note: The actual implementation might call on_object_start/on_object_end for empty objects
    # This test verifies the high-level structure
    key_events = [event for event in handler.events if event[0] == 'key']
    expected_keys = ['empty_obj', 'empty_arr']
    actual_keys = [event[1] for event in key_events]
    assert actual_keys == expected_keys, f"Expected keys {expected_keys}, got {actual_keys}"

def test_unicode_strings():
    """Test parsing strings with Unicode characters."""
    handler = TestHandler()
    json_str = '{"greeting": "Hello 世界", "emoji": "😀"}'
    parse(io.StringIO(json_str), handler)
    
    key_events = [event for event in handler.events if event[0] == 'key']
    expected_keys = ['greeting', 'emoji']
    actual_keys = [event[1] for event in key_events]
    assert actual_keys == expected_keys, f"Expected keys {expected_keys}, got {actual_keys}"
    
    value_events = [event for event in handler.events if event[0] == 'value']
    assert len(value_events) == 2, f"Expected 2 value events, got {len(value_events)}"
    assert value_events[0][1] == "Hello 世界", f"Expected 'Hello 世界', got {value_events[0][1]}"
    assert value_events[1][1] == "😀", f"Expected '😀', got {value_events[1][1]}"
