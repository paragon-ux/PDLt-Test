import io
import json
from typing import List, Any

class RecordingHandler:
    def __init__(self):
        self.events: List[str] = []
        self.current_string: str = ""
        self.string_depth: int = 0

    def on_object_start(self):
        self.events.append("object_start")

    def on_object_end(self):
        self.events.append("object_end")

    def on_array_start(self):
        self.events.append("array_start")

    def on_array_end(self):
        self.events.append("array_end")

    def on_key(self, key):
        self.events.append(f"key:{key}")

    def on_value(self, value):
        self.events.append(f"value:{value}")

    def on_string(self, s):
        self.events.append(f"string:{s}")

    def on_number(self, n):
        self.events.append(f"number:{n}")

    def on_bool(self, b):
        self.events.append(f"bool:{b}")

    def on_null(self):
        self.events.append("null")

def test_basic_object_parsing():
    handler = RecordingHandler()
    json_data = '{"name": "John", "age": 30, "is_student": false}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=10)
    
    expected_events = [
        "object_start",
        "key:name", "string:John",
        "key:age", "number:30",
        "key:is_student", "bool:False",
        "object_end"
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_nested_structures():
    handler = RecordingHandler()
    json_data = '{"outer": {"inner": [1, 2, 3]}}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=5)
    
    expected_events = [
        "object_start",
        "key:outer", "object_start",
        "key:inner", "array_start",
        "number:1", "number:2", "number:3",
        "array_end", "object_end",
        "object_end"
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_string_escape_sequences():
    handler = RecordingHandler()
    json_data = '{"text": "line1\\nline2\\ttab", "quote": "he said \\"hello\\""}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=10)
    
    expected_events = [
        "object_start",
        "key:text", "string:line1\nline2\ttab",
        "key:quote", 'string:he said "hello"',
        "object_end"
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_unicode_escape_sequences():
    handler = RecordingHandler()
    json_data = '{"emoji": "\\u2764", "chinese": "\\u4f60\\u597d"}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=10)
    
    expected_events = [
        "object_start",
        "key:emoji", "string:❤",
        "key:chinese", "string:你好",
        "object_end"
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_null_value_parsing():
    handler = RecordingHandler()
    json_data = '{"value": null}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=10)
    
    expected_events = [
        "object_start",
        "key:value", "null",
        "object_end"
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_large_array_streaming():
    handler = RecordingHandler()
    n = 1000
    json_array = "[" + ",".join(str(i) for i in range(n)) + "]"
    stream = io.StringIO(json_array)
    
    # Track memory usage by ensuring handler doesn't store all values
    original_on_number = handler.on_number
    call_count = [0]
    
    def counting_on_number(num):
        call_count[0] += 1
        original_on_number(num)
    
    handler.on_number = counting_on_number
    
    parse(stream, handler, chunk_size=10)
    
    assert call_count[0] == n, f"Expected {n} number callbacks, got {call_count[0]}"
    assert handler.events[0] == "array_start", "Expected array_start as first event"
    assert handler.events[-1] == "array_end", "Expected array_end as last event"
    
    # Verify all numbers are present
    numbers = [int(event.split(':')[1]) for event in handler.events if event.startswith('number:')]
    assert numbers == list(range(n)), "Numbers in array don't match expected sequence"

def test_chunked_streaming():
    handler = RecordingHandler()
    json_data = '{"a": 1, "b": [2, 3, 4], "c": "hello"}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=3)  # Very small chunks
    
    expected_events = [
        "object_start",
        "key:a", "number:1",
        "key:b", "array_start",
        "number:2", "number:3", "number:4",
        "array_end",
        "key:c", "string:hello",
        "object_end"
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_empty_object_and_array():
    handler = RecordingHandler()
    json_data = '{"empty_obj": {}, "empty_arr": []}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=10)
    
    expected_events = [
        "object_start",
        "key:empty_obj", "object_start", "object_end",
        "key:empty_arr", "array_start", "array_end",
        "object_end"
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"

def test_mixed_types_in_array():
    handler = RecordingHandler()
    json_data = '[1, "two", true, null, 3.14]'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=10)
    
    expected_events = [
        "array_start",
        "number:1", "string:two", "bool:True", "null", "number:3.14",
        "array_end"
    ]
    assert handler.events == expected_events, f"Expected {expected_events}, got {handler.events}"
