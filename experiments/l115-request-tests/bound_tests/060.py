import io
import json
from typing import List, Any, Callable

class TestHandler:
    def __init__(self):
        self.events: List[tuple] = []
        self.current_object_depth = 0
        self.current_array_depth = 0
        self.max_object_depth = 0
        self.max_array_depth = 0

    def on_object_start(self):
        self.current_object_depth += 1
        self.max_object_depth = max(self.max_object_depth, self.current_object_depth)
        self.events.append(('object_start',))

    def on_object_end(self):
        self.current_object_depth -= 1
        self.events.append(('object_end',))

    def on_array_start(self):
        self.current_array_depth += 1
        self.max_array_depth = max(self.max_array_depth, self.current_array_depth)
        self.events.append(('array_start',))

    def on_array_end(self):
        self.current_array_depth -= 1
        self.events.append(('array_end',))

    def on_key(self, key: str):
        self.events.append(('key', key))

    def on_value(self, value: Any):
        self.events.append(('value', value))

    def on_string(self, s: str):
        self.events.append(('string', s))

    def on_number(self, n: float):
        self.events.append(('number', n))

    def on_bool(self, b: bool):
        self.events.append(('bool', b))

    def on_null(self):
        self.events.append(('null',))

def test_simple_object_parsing():
    handler = TestHandler()
    stream = io.StringIO('{"name": "John", "age": 30, "is_student": false, "hobbies": null}')
    parser = SAXJSONParser(stream, handler, chunk_size=10)
    parser.parse()
    
    expected = [
        ('object_start',),
        ('key', 'name'),
        ('string', 'John'),
        ('key', 'age'),
        ('number', 30.0),
        ('key', 'is_student'),
        ('bool', False),
        ('key', 'hobbies'),
        ('null',),
        ('object_end',)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_nested_structures():
    handler = TestHandler()
    stream = io.StringIO('{"outer": {"inner": [1, 2, {"deep": true}]}}')
    parser = SAXJSONParser(stream, handler, chunk_size=15)
    parser.parse()
    
    assert handler.max_object_depth == 2, f"Expected max object depth 2, got {handler.max_object_depth}"
    assert handler.max_array_depth == 1, f"Expected max array depth 1, got {handler.max_array_depth}"
    assert len(handler.events) == 12, f"Expected 12 events, got {len(handler.events)}"

def test_string_escapes():
    handler = TestHandler()
    stream = io.StringIO('{"text": "line1\\nline2\\ttab", "quote": "\\"", "unicode": "\\u0041"}')
    parser = SAXJSONParser(stream, handler, chunk_size=10)
    parser.parse()
    
    string_events = [e for e in handler.events if e[0] == 'string']
    assert len(string_events) == 3, f"Expected 3 string events, got {len(string_events)}"
    assert string_events[0][1] == "line1\nline2\ttab", f"Expected newline/tab handling"
    assert string_events[1][1] == '"', f"Expected quote handling"
    assert string_events[2][1] == 'A', f"Expected unicode handling"

def test_large_array_streaming():
    handler = TestHandler()
    large_array = generate_large_json_array(1000)
    stream = io.StringIO(large_array)
    parser = SAXJSONParser(stream, handler, chunk_size=50)
    parser.parse()
    
    array_start_events = [e for e in handler.events if e == ('array_start',)]
    array_end_events = [e for e in handler.events if e == ('array_end',)]
    value_events = [e for e in handler.events if e[0] == 'value']
    
    assert len(array_start_events) == 1, "Expected exactly one array_start event"
    assert len(array_end_events) == 1, "Expected exactly one array_end event"
    assert len(value_events) == 1000, f"Expected 1000 value events, got {len(value_events)}"
    
    for i, event in enumerate(value_events):
        assert event[1] == float(i), f"Value at index {i} should be {i}, got {event[1]}"

def test_chunked_parsing():
    handler = TestHandler()
    stream = io.StringIO('[1,2,3,4,5]')
    parser = SAXJSONParser(stream, handler, chunk_size=2)
    parser.parse()
    
    value_events = [e for e in handler.events if e[0] == 'value']
    values = [e[1] for e in value_events]
    assert values == [1.0, 2.0, 3.0, 4.0, 5.0], f"Expected [1,2,3,4,5], got {values}"

def test_mixed_types():
    handler = TestHandler()
    stream = io.StringIO('[null, true, false, 42, "text", 3.14]')
    parser = SAXJSONParser(stream, handler, chunk_size=10)
    parser.parse()
    
    expected_types = [
        ('null',),
        ('bool', True),
        ('bool', False),
        ('value', 42.0),
        ('string', 'text'),
        ('value', 3.14)
    ]
    
    value_events = [e for e in handler.events if e[0] in ('null', 'bool', 'value', 'string')]
    assert value_events == expected_types, f"Expected {expected_types}, got {value_events}"

def test_empty_structures():
    handler = TestHandler()
    stream = io.StringIO('{"empty_object": {}, "empty_array": []}')
    parser = SAXJSONParser(stream, handler, chunk_size=10)
    parser.parse()
    
    object_events = [e for e in handler.events if e[0] in ('object_start', 'object_end')]
    array_events = [e for e in handler.events if e[0] in ('array_start', 'array_end')]
    
    assert len(object_events) == 4, f"Expected 4 object events (2 starts, 2 ends), got {len(object_events)}"
    assert len(array_events) == 2, f"Expected 2 array events (1 start, 1 end), got {len(array_events)}"

def generate_large_json_array(num_elements: int) -> str:
    return '[' + ','.join(str(i) for i in range(num_elements)) + ']'
