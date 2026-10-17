import io

def test_decode_string_escapes():
    assert decode_string('hello') == 'hello'
    assert decode_string('hello\\nworld') == 'hello\nworld'
    assert decode_string('hello\\tworld') == 'hello\tworld'
    assert decode_string('hello\\\\world') == 'hello\\world'
    assert decode_string('hello\\"world') == 'hello"world'
    assert decode_string('\\u0041') == 'A'
    assert decode_string('a\\nb\\tc\\\"d\\u0042') == 'a\nb\tc"d B'

def test_decode_string_unicode():
    assert decode_string('\\u0041\\u0042') == 'AB'

def test_tokenize_simple_object():
    stream = io.StringIO('{"a":1}')
    tokens = list(tokenize(stream, 1024))
    assert tokens == ['{', 'a', ':', '1', '}']

def test_recording_handler():
    h = RecordingHandler()
    h.on_object_start()
    h.on_key('a')
    h.on_value(1)
    h.on_number(1)
    h.on_object_end()
    expected = [
        ('on_object_start', ()),
        ('on_key', ('a',)),
        ('on_value', (1,)),
        ('on_number', (1,)),
        ('on_object_end', ())
    ]
    assert h.calls == expected

def test_parse_simple_object():
    h = RecordingHandler()
    parse(io.StringIO('{"a":1}'), h)
    expected = [
        ('on_object_start', ()),
        ('on_key', ('a',)),
        ('on_value', (1,)),
        ('on_number', (1,)),
        ('on_object_end', ())
    ]
    assert h.calls == expected

def test_parse_array():
    h = RecordingHandler()
    parse(io.StringIO('[1,2,3]'), h)
    expected = [
        ('on_array_start', ()),
        ('on_value', (1,)),
        ('on_number', (1,)),
        ('on_value', (2,)),
        ('on_number', (2,)),
        ('on_value', (3,)),
        ('on_number', (3,)),
        ('on_array_end', ())
    ]
    assert h.calls == expected

def test_parse_nested():
    h = RecordingHandler()
    parse(io.StringIO('{"a":[1,2]}'), h)
    expected = [
        ('on_object_start', ()),
        ('on_key', ('a',)),
        ('on_array_start', ()),
        ('on_value', (1,)),
        ('on_number', (1,)),
        ('on_value', (2,)),
        ('on_number', (2,)),
        ('on_array_end', ()),
        ('on_object_end', ())
    ]
    assert h.calls == expected

def test_parse_deep_nesting():
    h = RecordingHandler()
    parse(io.StringIO('{"a":{"b":{"c":1}}}'), h)
    expected = [
        ('on_object_start', ()),
        ('on_key', ('a',)),
        ('on_object_start', ()),
        ('on_key', ('b',)),
        ('on_object_start', ()),
        ('on_key', ('c',)),
        ('on_value', (1,)),
        ('on_number', (1,)),
        ('on_object_end', ()),
        ('on_object_end', ()),
        ('on_object_end', ())
    ]
    assert h.calls == expected

def test_parse_string_escapes():
    h = RecordingHandler()
    parse(io.StringIO('{"a":"hello\\nworld"}'), h)
    expected = [
        ('on_object_start', ()),
        ('on_key', ('a',)),
        ('on_value', ('hello\nworld',)),
        ('on_string', ('hello\nworld',)),
        ('on_object_end', ())
    ]
    assert h.calls == expected

def test_parse_number():
    h = RecordingHandler()
    parse(io.StringIO('123.45'), h)
    expected = [
        ('on_value', (123.45,)),
        ('on_number', (123.45,))
    ]
    assert h.calls == expected

def test_parse_bool_null():
    h = RecordingHandler()
    parse(io.StringIO('true false null'), h)
    expected = [
        ('on_value', (True,)),
        ('on_bool', (True,)),
        ('on_value', (False,)),
        ('on_bool', (False,)),
        ('on_value', (None,)),
        ('on_null', ())
    ]
    assert h.calls == expected

def test_parse_error():
    h = RecordingHandler()
    try:
        parse(io.StringIO('invalid'), h)
        assert False, "Expected JSONParseError"
    except JSONParseError:
        pass

def test_streaming_1000_array():
    json_str = '[' + ','.join(str(i) for i in range(1000)) + ']'
    h = RecordingHandler()
    parse(io.StringIO(json_str), h)
    calls = h.calls
    assert calls[0] == ('on_array_start', ())
    assert calls[-1] == ('on_array_end', ())
    on_value_count = sum(1 for call in calls if call[0] == 'on_value')
    on_number_count = sum(1 for call in calls if call[0] == 'on_number')
    assert on_value_count == 1000
    assert on_number_count == 1000
    values = [call[1][0] for call in calls if call[0] == 'on_value']
    assert values == list(range(1000))