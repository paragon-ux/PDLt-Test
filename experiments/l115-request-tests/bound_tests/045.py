import io

class MockHandler:
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


def test_simple_values():
    # Test string
    handler = MockHandler()
    parse(io.StringIO('"hello"'), handler)
    assert ('string', 'hello') in handler.events, "String callback failed"
    
    # Test number
    handler = MockHandler()
    parse(io.StringIO('123'), handler)
    assert ('number', 123) in handler.events, "Number callback failed"
    
    # Test boolean true
    handler = MockHandler()
    parse(io.StringIO('true'), handler)
    assert ('bool', True) in handler.events, "Bool true callback failed"
    
    # Test boolean false
    handler = MockHandler()
    parse(io.StringIO('false'), handler)
    assert ('bool', False) in handler.events, "Bool false callback failed"
    
    # Test null
    handler = MockHandler()
    parse(io.StringIO('null'), handler)
    assert 'null' in handler.events, "Null callback failed"


def test_objects():
    json_str = '{"key": "value", "num": 10, "nested": {"inner": true}}'
    handler = MockHandler()
    parse(io.StringIO(json_str), handler)
    
    events = handler.events
    assert events[0] == 'object_start', "Expected object_start"
    
    # Check key "key"
    assert ('key', 'key') in events
    idx_key = events.index(('key', 'key'))
    assert ('string', 'value') in events[idx_key+1:], "Expected string value for key"
    
    # Check key "num"
    assert ('key', 'num') in events
    idx_num = events.index(('key', 'num'))
    assert ('number', 10) in events[idx_num+1:], "Expected number value for num"
    
    # Check nested object
    assert ('key', 'nested') in events
    idx_nested = events.index(('key', 'nested'))
    assert 'object_start' in events[idx_nested+1:], "Expected nested object start"


def test_arrays():
    json_str = '[1, "two", [3, 4], {"a": "b"}]'
    handler = MockHandler()
    parse(io.StringIO(json_str), handler)
    
    events = handler.events
    assert events[0] == 'array_start'
    assert events[-1] == 'array_end'
    
    # Check nested array
    assert ('number', 1) in events
    assert ('string', 'two') in events


def test_string_escapes():
    # JSON string containing escapes: \n, \t, \", \\, \u0041 (which is 'A')
    json_str = '"line1\\nline2\\ttab\\"quote\\\\backslash\\u0041"'
    handler = MockHandler()
    parse(io.StringIO(json_str), handler)
    
    # Find the string event
    string_events = [ev for ev in handler.events if isinstance(ev, tuple) and ev[0] == 'string']
    assert len(string_events) == 1, f"Expected one string event, got {string_events}"
    actual_str = string_events[0][1]
    expected_str = 'line1\nline2\ttab"quote\\backslashA'
    assert actual_str == expected_str, f"Expected {repr(expected_str)}, got {repr(actual_str)}"


def test_nested_structures():
    json_str = '{"a": {"b": {"c": [1, 2, 3]}}}'
    handler = MockHandler()
    parse(io.StringIO(json_str), handler)
    
    events = handler.events
    assert events[0] == 'object_start'
    assert ('key', 'a') in events
    assert 'object_start' in events
    assert ('key', 'b') in events
    assert 'object_start' in events
    assert ('key', 'c') in events
    assert 'array_start' in events
    assert ('number', 1) in events
    assert ('number', 2) in events
    assert ('number', 3) in events
    assert 'array_end' in events
    assert 'object_end' in events
    assert 'object_end' in events
    assert 'object_end' in events


def test_streaming_large_array():
    # Generate a 1000-element JSON array
    elements = list(range(1000))
    json_str = '[' + ','.join(map(str, elements)) + ']'
    
    handler = MockHandler()
    parse(io.StringIO(json_str), handler)
    
    # Verify array start and end
    assert handler.events[0] == 'array_start', "Expected array_start"
    assert handler.events[-1] == 'array_end', "Expected array_end"
    
    # Verify number of number callbacks
    number_events = [ev for ev in handler.events if isinstance(ev, tuple) and ev[0] == 'number']
    assert len(number_events) == 1000, f"Expected 1000 numbers, got {len(number_events)}"
    
    # Verify the values are in order
    for i, ev in enumerate(number_events):
        assert ev[1] == i, f"Expected number {i} at index {i}, got {ev[1]}"
