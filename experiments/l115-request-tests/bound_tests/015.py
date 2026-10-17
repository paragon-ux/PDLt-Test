import io

class MockHandler:
    def __init__(self):
        self.calls = []

    def on_object_start(self):
        self.calls.append(('on_object_start',))

    def on_object_end(self):
        self.calls.append(('on_object_end',))

    def on_array_start(self):
        self.calls.append(('on_array_start',))

    def on_array_end(self):
        self.calls.append(('on_array_end',))

    def on_key(self, key):
        self.calls.append(('on_key', key))

    def on_value(self, value):
        self.calls.append(('on_value', value))

    def on_string(self, s):
        self.calls.append(('on_string', s))

    def on_number(self, n):
        self.calls.append(('on_number', n))

    def on_bool(self, b):
        self.calls.append(('on_bool', b))

    def on_null(self):
        self.calls.append(('on_null',))


def test_parse_simple_object():
    handler = MockHandler()
    parse(io.StringIO('{"name": "John", "age": 30, "is_student": false, "nickname": null}'), handler)
    
    assert handler.calls[0] == ('on_object_start',), f"Expected on_object_start, got {handler.calls[0]}"
    assert handler.calls[-1] == ('on_object_end',), f"Expected on_object_end, got {handler.calls[-1]}"
    
    keys = [call[1] for call in handler.calls if call[0] == 'on_key']
    assert keys == ["name", "age", "is_student", "nickname"], f"Keys mismatch: {keys}"
    
    strings = [call[1] for call in handler.calls if call[0] == 'on_string']
    assert "John" in strings, f"String 'John' not found in {strings}"
    
    numbers = [call[1] for call in handler.calls if call[0] == 'on_number']
    assert 30 in numbers, f"Number 30 not found in {numbers}"
    
    bools = [call[1] for call in handler.calls if call[0] == 'on_bool']
    assert False in bools, f"Bool False not found in {bools}"
    
    nulls = [call for call in handler.calls if call[0] == 'on_null']
    assert len(nulls) == 1, f"Expected 1 null, got {len(nulls)}"


def test_parse_simple_array():
    handler = MockHandler()
    parse(io.StringIO('[1, "two", true, null]'), handler)
    
    assert handler.calls[0] == ('on_array_start',), f"Expected on_array_start, got {handler.calls[0]}"
    assert handler.calls[-1] == ('on_array_end',), f"Expected on_array_end, got {handler.calls[-1]}"
    
    numbers = [call[1] for call in handler.calls if call[0] == 'on_number']
    assert 1 in numbers, f"Number 1 not found in {numbers}"
    
    strings = [call[1] for call in handler.calls if call[0] == 'on_string']
    assert "two" in strings, f"String 'two' not found in {strings}"
    
    bools = [call[1] for call in handler.calls if call[0] == 'on_bool']
    assert True in bools, f"Bool True not found in {bools}"
    
    nulls = [call for call in handler.calls if call[0] == 'on_null']
    assert len(nulls) == 1, f"Expected 1 null, got {len(nulls)}"


def test_parse_string_escapes():
    handler = MockHandler()
    json_str = r'{"escaped": "line1\nline2\ttab\"quote\\backslash\u0041"}'
    parse(io.StringIO(json_str), handler)
    
    strings = [call[1] for call in handler.calls if call[0] == 'on_string']
    assert len(strings) == 1, f"Expected 1 string, got {len(strings)}"
    expected_str = "line1\nline2\ttab\"quote\\backslashA"
    assert strings[0] == expected_str, f"Expected '{expected_str}', got '{strings[0]}'"


def test_parse_nested_structures():
    handler = MockHandler()
    parse(io.StringIO('{"outer": {"inner": [1, 2, {"deep": true}]}}'), handler)
    
    events = [call[0] for call in handler.calls]
    structure = [e for e in events if e in ('on_object_start', 'on_object_end', 'on_array_start', 'on_array_end')]
    
    expected_structure = [
        'on_object_start',
        'on_object_start',
        'on_array_start',
        'on_object_start',
        'on_object_end',
        'on_array_end',
        'on_object_end',
        'on_object_end'
    ]
    assert structure == expected_structure, f"Structure mismatch: {structure}"


def test_stream_1000_element_array():
    json_str = "[" + ", ".join(str(i) for i in range(1, 1001)) + "]"
    handler = MockHandler()
    parse(io.StringIO(json_str), handler)
    
    assert handler.calls[0] == ('on_array_start',), "Expected on_array_start"
    assert handler.calls[-1] == ('on_array_end',), "Expected on_array_end"
    
    numbers_only = [call[1] for call in handler.calls if call[0] == 'on_number']
    if len(numbers_only) == 1000:
        for idx, num in enumerate(numbers_only, 1):
            assert num == idx, f"Expected {idx}, got {num} at position {idx}"
    else:
        values = [call[1] for call in handler.calls if call[0] == 'on_value']
        assert len(values) == 1000, f"Expected 1000 values, got {len(values)}"
        for idx, val in enumerate(values, 1):
            assert val == idx, f"Expected {idx}, got {val} at position {idx}"
