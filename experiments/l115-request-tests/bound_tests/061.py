import io
import json
from typing import List, Any, Optional

# ========== Test Handler Classes ==========

class RecordingHandler(JsonHandler):
    """Records all callbacks for verification."""
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

class ChunkedStream:
    """File-like object that returns data in fixed-size chunks."""
    def __init__(self, data: str, chunk_size: int):
        self.data = data.encode('utf-8')
        self.chunk_size = chunk_size
        self.pos = 0
    
    def read(self, size: int = -1) -> bytes:
        if self.pos >= len(self.data):
            return b''
        if size == -1 or size is None:
            end = len(self.data)
        else:
            end = min(self.pos + size, len(self.data))
        chunk = self.data[self.pos:end]
        self.pos = end
        return chunk
    
    def close(self):
        pass

# ========== Helper Functions ==========

def parse_json_string(json_str: str, chunk_size: int = 1) -> List[tuple]:
    """Parse JSON string with given chunk size and return recorded events."""
    stream = ChunkedStream(json_str, chunk_size)
    handler = RecordingHandler()
    parse(stream, handler)
    return handler.events

# ========== Basic Value Tests ==========

def test_string_parsing():
    """Test basic string parsing."""
    events = parse_json_string('"hello"')
    assert events == [('string', 'hello')], f"Expected [('string', 'hello')], got {events}"

def test_number_parsing():
    """Test number parsing."""
    events = parse_json_string('42')
    assert events == [('number', 42)], f"Expected [('number', 42)], got {events}"

def test_float_number_parsing():
    """Test float number parsing."""
    events = parse_json_string('3.14')
    assert events == [('number', 3.14)], f"Expected [('number', 3.14)], got {events}"

def test_negative_number_parsing():
    """Test negative number parsing."""
    events = parse_json_string('-17')
    assert events == [('number', -17)], f"Expected [('number', -17)], got {events}"

def test_bool_true_parsing():
    """Test true boolean parsing."""
    events = parse_json_string('true')
    assert events == [('bool', True)], f"Expected [('bool', True)], got {events}"

def test_bool_false_parsing():
    """Test false boolean parsing."""
    events = parse_json_string('false')
    assert events == [('bool', False)], f"Expected [('bool', False)], got {events}"

def test_null_parsing():
    """Test null parsing."""
    events = parse_json_string('null')
    assert events == [('null',)], f"Expected [('null',)], got {events}"

# ========== String Escape Sequence Tests ==========

def test_string_escape_quotes():
    """Test string with escaped quotes."""
    events = parse_json_string('"say \\"hello\\""')
    assert events == [('string', 'say "hello"')], f"Got {events}"

def test_string_escape_backslash():
    """Test string with escaped backslash."""
    events = parse_json_string('"path\\\\to\\\\file"')
    assert events == [('string', 'path\\to\\file')], f"Got {events}"

def test_string_escape_newline():
    """Test string with escaped newline."""
    events = parse_json_string('"line1\\nline2"')
    assert events == [('string', 'line1\nline2')], f"Got {events}"

def test_string_escape_tab():
    """Test string with escaped tab."""
    events = parse_json_string('"col1\\tcol2"')
    assert events == [('string', 'col1\tcol2')], f"Got {events}"

def test_string_escape_unicode():
    """Test string with unicode escape."""
    events = parse_json_string('"\\u0041\\u0042\\u0043"')
    assert events == [('string', 'ABC')], f"Got {events}"

def test_string_escape_mixed():
    """Test string with multiple escape sequences."""
    events = parse_json_string('"\\u0041\\n\\t\\u0042"')
    assert events == [('string', 'A\n\tB')], f"Got {events}"

# ========== Object Tests ==========

def test_empty_object():
    """Test empty object parsing."""
    events = parse_json_string('{}')
    assert events == [('object_start',), ('object_end',)], f"Got {events}"

def test_object_with_single_key():
    """Test object with single key-value pair."""
    events = parse_json_string('{"key": "value"}')
    expected = [
        ('object_start',),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end',)
    ]
    assert events == expected, f"Expected {expected}, got {events}"

def test_object_with_multiple_keys():
    """Test object with multiple key-value pairs."""
    events = parse_json_string('{"a": 1, "b": 2}')
    expected = [
        ('object_start',),
        ('key', 'a'),
        ('number', 1),
        ('key', 'b'),
        ('number', 2),
        ('object_end',)
    ]
    assert events == expected, f"Expected {expected}, got {events}"

def test_object_with_nested_object():
    """Test object containing nested object."""
    events = parse_json_string('{"outer": {"inner": "value"}}')
    expected = [
        ('object_start',),
        ('key', 'outer'),
        ('object_start',),
        ('key', 'inner'),
        ('string', 'value'),
        ('object_end',),
        ('object_end',)
    ]
    assert events == expected, f"Expected {expected}, got {events}"

# ========== Array Tests ==========

def test_empty_array():
    """Test empty array parsing."""
    events = parse_json_string('[]')
    assert events == [('array_start',), ('array_end',)], f"Got {events}"

def test_array_with_elements():
    """Test array with multiple elements."""
    events = parse_json_string('[1, 2, 3]')
    expected = [
        ('array_start',),
        ('number', 1),
        ('number', 2),
        ('number', 3),
        ('array_end',)
    ]
    assert events == expected, f"Expected {expected}, got {events}"

def test_array_with_mixed_types():
    """Test array with mixed value types."""
    events = parse_json_string('[1, "two", true, null]')
    expected = [
        ('array_start',),
        ('number', 1),
        ('string', 'two'),
        ('bool', True),
        ('null',),
        ('array_end',)
    ]
    assert events == expected, f"Expected {expected}, got {events}"

def test_array_with_nested_array():
    """Test array containing nested array."""
    events = parse_json_string('[[1, 2], [3, 4]]')
    expected = [
        ('array_start',),
        ('array_start',),
        ('number', 1),
        ('number', 2),
        ('array_end',),
        ('array_start',),
        ('number', 3),
        ('number', 4),
        ('array_end',),
        ('array_end',)
    ]
    assert events == expected, f"Expected {expected}, got {events}"

# ========== Streaming Behavior Tests ==========

def test_streaming_with_chunk_size_1():
    """Test parsing with 1-byte chunks to verify streaming."""
    data = '{"key": "value"}'
    events = parse_json_string(data, chunk_size=1)
    expected = [
        ('object_start',),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end',)
    ]
    assert events == expected, f"Expected {expected}, got {events}"

def test_streaming_with_varying_chunk_sizes():
    """Test parsing with different chunk sizes produces same results."""
    data = '[1, 2, "three", true]'
    events_1 = parse_json_string(data, chunk_size=1)
    events_3 = parse_json_string(data, chunk_size=3)
    events_10 = parse_json_string(data, chunk_size=10)
    
    expected = [
        ('array_start',),
        ('number', 1),
        ('number', 2),
        ('string', 'three'),
        ('bool', True),
        ('array_end',)
    ]
    
    assert events_1 == expected, f"Chunk size 1: expected {expected}, got {events_1}"
    assert events_3 == expected, f"Chunk size 3: expected {expected}, got {events_3}"
    assert events_10 == expected, f"Chunk size 10: expected {expected}, got {events_10}"

# ========== Nested Structure Tests ==========

def test_deeply_nested_object():
    """Test deeply nested objects (depth 10)."""
    # Create nested object: {"a":{"b":{"c":{"d":{"e":{"f":{"g":{"h":{"i":{"j":1}}}}}}}}}}
    data = '{"a":{"b":{"c":{"d":{"e":{"f":{"g":{"h":{"i":{"j":1}}}}}}}}}}'
    events = parse_json_string(data)
    
    # Verify structure: 10 object starts, then key "j", number 1, then 10 object ends
    object_starts = [e for e in events if e[0] == 'object_start']
    object_ends = [e for e in events if e[0] == 'object_end']
    assert len(object_starts) == 10, f"Expected 10 object starts, got {len(object_starts)}"
    assert len(object_ends) == 10, f"Expected 10 object ends, got {len(object_ends)}"
    
    # Check that the innermost value is correct
    assert ('key', 'j') in events
    assert ('number', 1) in events

def test_deeply_nested_array():
    """Test deeply nested arrays (depth 10)."""
    # Create nested array: [[[[[[[[[[1]]]]]]]]]]
    data = '[[[[[[[[[[1]]]]]]]]]]'
    events = parse_json_string(data)
    
    array_starts = [e for e in events if e[0] == 'array_start']
    array_ends = [e for e in events if e[0] == 'array_end']
    assert len(array_starts) == 10, f"Expected 10 array starts, got {len(array_starts)}"
    assert len(array_ends) == 10, f"Expected 10 array ends, got {len(array_ends)}"
    assert ('number', 1) in events

def test_mixed_nested_structures():
    """Test mixed nested objects and arrays."""
    data = '{"array": [{"value": 1}, {"value": 2}], "nested": {"inner": [3, 4]}}'
    events = parse_json_string(data)
    
    # Verify structure
    assert ('object_start',) in events
    assert ('key', 'array') in events
    assert ('array_start',) in events
    assert ('object_start',) in events
    assert ('key', 'value') in events
    assert ('number', 1) in events
    assert ('object_end',) in events
    assert ('object_start',) in events
    assert ('key', 'value') in events
    assert ('number', 2) in events
    assert ('object_end',) in events
    assert ('array_end',) in events
    assert ('key', 'nested') in events
    assert ('object_start',) in events
    assert ('key', 'inner') in events
    assert ('array_start',) in events
    assert ('number', 3) in events
    assert ('number', 4) in events
    assert ('array_end',) in events
    assert ('object_end',) in events
    assert ('object_end',) in events

# ========== Large Array Test ==========

def test_1000_element_array():
    """Test streaming a 1000-element JSON array and verify all callbacks fire correctly."""
    # Create a JSON array with 1000 numbers
    numbers = list(range(1000))
    json_str = json.dumps(numbers)
    
    # Parse with streaming (small chunk size to verify streaming behavior)
    events = parse_json_string(json_str, chunk_size=7)
    
    # Verify array structure
    assert events[0] == ('array_start',), f"First event should be array_start, got {events[0]}"
    assert events[-1] == ('array_end',), f"Last event should be array_end, got {events[-1]}"
    
    # Verify all number callbacks
    number_events = [e for e in events if e[0] == 'number']
    assert len(number_events) == 1000, f"Expected 1000 number events, got {len(number_events)}"
    
    # Verify correct values
    for i, event in enumerate(number_events):
        expected_value = i
        actual_value = event[1]
        assert actual_value == expected_value, f"Element {i}: expected {expected_value}, got {actual_value}"
    
    # Verify no other value events (only numbers in this array)
    value_events = [e for e in events if e[0] in ('string', 'bool', 'null')]
    assert len(value_events) == 0, f"Unexpected value events: {value_events}"

def test_1000_element_array_with_strings():
    """Test 1000-element array with strings to verify different callback types."""
    strings = [f"item_{i}" for i in range(1000)]
    json_str = json.dumps(strings)
    events = parse_json_string(json_str, chunk_size=13)
    
    # Verify structure
    assert events[0] == ('array_start',)
    assert events[-1] == ('array_end',)
    
    # Verify all string callbacks
    string_events = [e for e in events if e[0] == 'string']
    assert len(string_events) == 1000, f"Expected 1000 string events, got {len(string_events)}"
    
    # Verify correct values
    for i, event in enumerate(string_events):
        expected = f"item_{i}"
        actual = event[1]
        assert actual == expected, f"Element {i}: expected {expected}, got {actual}"

# ========== Edge Cases ==========

def test_whitespace_handling():
    """Test that whitespace is properly skipped."""
    data = '  {  "key"  :  "value"  }  '
    events = parse_json_string(data)
    expected = [
        ('object_start',),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end',)
    ]
    assert events == expected, f"Expected {expected}, got {events}"

def test_empty_string():
    """Test empty string parsing."""
    events = parse_json_string('""')
    assert events == [('string', '')], f"Expected [('string', '')], got {events}"

def test_escaped_unicode_boundary():
    """Test unicode escape at chunk boundaries."""
    # This tests that the parser handles unicode escapes correctly even when split across chunks
    data = '"\\u0041"'
    events = parse_json_string(data, chunk_size=2)  # Split in middle of escape
    assert events == [('string', 'A')], f"Got {events}"

def test_max_int_boundary():
    """Test parsing of large integers."""
    # Test with a value near Python's int limit
    large_int = 2**63 - 1
    json_str = str(large_int)
    events = parse_json_string(json_str)
    assert events == [('number', large_int)], f"Got {events}"

# ========== Handler Interface Tests ==========

def test_handler_callbacks_exist():
    """Verify all required handler methods exist."""
    handler = JsonHandler()
    required_methods = [
        'on_object_start', 'on_object_end', 'on_array_start', 'on_array_end',
        'on_key', 'on_value', 'on_string', 'on_number', 'on_bool', 'on_null'
    ]
    for method in required_methods:
        assert hasattr(handler, method), f"Handler missing method: {method}"
        assert callable(getattr(handler, method)), f"Method {method} is not callable"

def test_custom_handler_receives_callbacks():
    """Test that a custom handler receives all callbacks."""
    class TestHandler(JsonHandler):
        def __init__(self):
            self.call_count = 0
        
        def on_object_start(self):
            self.call_count += 1
        
        def on_object_end(self):
            self.call_count += 1
        
        def on_array_start(self):
            self.call_count += 1
        
        def on_array_end(self):
            self.call_count += 1
        
        def on_key(self, key):
            self.call_count += 1
        
        def on_value(self, value):
            self.call_count += 1
        
        def on_string(self, s):
            self.call_count += 1
        
        def on_number(self, n):
            self.call_count += 1
        
        def on_bool(self, b):
            self.call_count += 1
        
        def on_null(self):
            self.call_count += 1
    
    handler = TestHandler()
    parse(io.StringIO('{"key": [1, 2, true, null, "string"]}'), handler)
    
    # Expected callbacks: object_start, key, array_start, number, number, bool, null, string, array_end, object_end
    expected_count = 10
    assert handler.call_count == expected_count, f"Expected {expected_count} callbacks, got {handler.call_count}"
