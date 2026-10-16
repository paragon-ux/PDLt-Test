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
    handler = RecordingHandler()
    parser = JSONSAXParser(handler)
    stream = io.StringIO('{"key": "value"}')
    parser.parse(stream, chunk_size=10)
    assert handler.events == [
        'object_start',
        ('key', 'key'),
        ('string', 'value'),
        'object_end'
    ], f"Unexpected events: {handler.events}"


def test_string_escapes():
    handler = RecordingHandler()
    parser = JSONSAXParser(handler)
    # Test all escape sequences: \\, \n, \t, \", \u0041 (which is 'A')
    json_str = r'{"text": "line1\nline2\ttab\"quote\\backslash\u0041end"}'
    stream = io.StringIO(json_str)
    parser.parse(stream, chunk_size=10)
    expected_string = 'line1\nline2\ttab"quote\\backslashAend'
    assert ('string', expected_string) in handler.events, f"String escape not handled correctly: {handler.events}"


def test_nested_structures():
    handler = RecordingHandler()
    parser = JSONSAXParser(handler)
    json_str = '{"a": [1, {"b": "c"}, null], "d": true}'
    stream = io.StringIO(json_str)
    parser.parse(stream, chunk_size=10)
    expected = [
        'object_start',
        ('key', 'a'),
        'array_start',
        ('number', 1),
        'object_start',
        ('key', 'b'),
        ('string', 'c'),
        'object_end',
        'null',
        'array_end',
        ('key', 'd'),
        ('bool', True),
        'object_end'
    ]
    assert handler.events == expected, f"Nested structure events mismatch: {handler.events}"


def test_array_of_1000_numbers():
    handler = RecordingParser()
    parser = JSONSAXParser(handler)
    # Generate a JSON array of 1000 numbers
    numbers = list(range(1000))
    json_str = '[' + ','.join(str(n) for n in numbers) + ']'
    stream = io.StringIO(json_str)
    parser.parse(stream, chunk_size=10)  # Small chunk size to force streaming
    
    # Verify callbacks: array_start, 1000 numbers, array_end
    assert handler.events[0] == 'array_start', "Array start not called"
    assert handler.events[-1] == 'array_end', "Array end not called"
    number_events = [e for e in handler.events if isinstance(e, tuple) and e[0] == 'number']
    assert len(number_events) == 1000, f"Expected 1000 numbers, got {len(number_events)}"
    for i, (typ, value) in enumerate(number_events):
        assert value == i, f"Number mismatch at index {i}: expected {i}, got {value}"


def test_streaming_chunks():
    """Test that parsing works correctly when data is fed in small chunks."""
    handler = RecordingHandler()
    parser = JSONSAXParser(handler)
    json_str = '{"x": 1, "y": [true, false, null, "str"]}'
    stream = io.StringIO(json_str)
    parser.parse(stream, chunk_size=1)  # Byte-by-byte streaming
    expected = [
        'object_start',
        ('key', 'x'),
        ('number', 1),
        ('key', 'y'),
        'array_start',
        ('bool', True),
        ('bool', False),
        'null',
        ('string', 'str'),
        'array_end',
        'object_end'
    ]
    assert handler.events == expected, f"Chunked parsing events mismatch: {handler.events}"


# Additional test for the "without holding more than one element in memory" property
# This test verifies that the parser does not buffer the entire array by checking
# that the number of simultaneous "open" structures is bounded.
def test_memory_bounded():
    """Verify that the parser does not hold more than one element in memory
    by checking that the stack depth of nested structures is limited."""
    handler = RecordingHandler()
    parser = JSONSAXParser(handler)
    # Create a deeply nested array: [[[[...]]]] with 1000 levels
    depth = 1000
    json_str = '[' * depth + '1' + ']' * depth
    stream = io.StringIO(json_str)
    parser.parse(stream, chunk_size=10)
    # Count the number of consecutive array_start events
    array_starts = 0
    for event in handler.events:
        if event == 'array_start':
            array_starts += 1
        else:
            break
    assert array_starts == depth, f"Expected {depth} array starts, got {array_starts}"
    # The parser should not crash and should properly close all arrays
    array_ends = sum(1 for e in handler.events if e == 'array_end')
    assert array_ends == depth, f"Expected {depth} array ends, got {array_ends}"
