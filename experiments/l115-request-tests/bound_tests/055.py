import io

def test_simple_object():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    parse(stream, handler, 10)
    expected = [
        ('on_object_start', ()),
        ('on_key', ('key',)),
        ('on_value', ('value',)),
        ('on_string', ('value',)),
        ('on_object_end', ()),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_simple_array():
    handler = RecordingHandler()
    stream = io.StringIO('[1, 2, 3]')
    parse(stream, handler, 10)
    expected = [
        ('on_array_start', ()),
        ('on_value', (1,)),
        ('on_number', (1,)),
        ('on_value', (2,)),
        ('on_number', (2,)),
        ('on_value', (3,)),
        ('on_number', (3,)),
        ('on_array_end', ()),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_string_escapes():
    handler = RecordingHandler()
    stream = io.StringIO('"hello\\nworld\\ttab\\\\"quote\\u0041"')
    parse(stream, handler, 10)
    expected = [
        ('on_string', ('hello\nworld\ttab\\"quoteA',)),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_nested_structures():
    handler = RecordingHandler()
    stream = io.StringIO('{"array": [1, {"nested": "value"}]}')
    parse(stream, handler, 10)
    expected = [
        ('on_object_start', ()),
        ('on_key', ('array',)),
        ('on_value', ([1, {"nested": "value"}],)),
        ('on_array_start', ()),
        ('on_value', (1,)),
        ('on_number', (1,)),
        ('on_value', ({"nested": "value"},)),
        ('on_object_start', ()),
        ('on_key', ('nested',)),
        ('on_value', ('value',)),
        ('on_string', ('value',)),
        ('on_object_end', ()),
        ('on_array_end', ()),
        ('on_object_end', ()),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_large_array():
    handler = RecordingHandler()
    array_content = ','.join(str(i) for i in range(1000))
    stream = io.StringIO(f'[{array_content}]')
    parse(stream, handler, 1)
    assert handler.events[0] == ('on_array_start', ()), "Array start not called"
    assert handler.events[-1] == ('on_array_end', ()), "Array end not called"
    number_events = [e for e in handler.events if e[0] == 'on_number']
    assert len(number_events) == 1000, f"Expected 1000 on_number events, got {len(number_events)}"
    for i, event in enumerate(number_events):
        assert event[1] == (i,), f"Expected number {i}, got {event[1]}"

def test_chunk_size():
    handler = RecordingHandler()
    stream = io.StringIO('{"a":1,"b":2}')
    parse(stream, handler, 2)
    expected = [
        ('on_object_start', ()),
        ('on_key', ('a',)),
        ('on_value', (1,)),
        ('on_number', (1,)),
        ('on_key', ('b',)),
        ('on_value', (2,)),
        ('on_number', (2,)),
        ('on_object_end', ()),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_bool_and_null():
    handler = RecordingHandler()
    stream = io.StringIO('[true, false, null]')
    parse(stream, handler, 10)
    expected = [
        ('on_array_start', ()),
        ('on_value', (True,)),
        ('on_bool', (True,)),
        ('on_value', (False,)),
        ('on_bool', (False,)),
        ('on_value', (None,)),
        ('on_null', ()),
        ('on_array_end', ()),
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"
