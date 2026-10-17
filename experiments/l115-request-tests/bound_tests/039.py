import io

class _TestHandler:
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

def test_parse_simple_object():
    handler = _TestHandler()
    parse(io.StringIO('{"key": "value"}'), handler, 10)
    assert 'object_start' in handler.events
    assert ('key', 'key') in handler.events
    assert ('string', 'value') in handler.events
    assert 'object_end' in handler.events

def test_parse_simple_array():
    handler = _TestHandler()
    parse(io.StringIO('[1, 2, 3]'), handler, 10)
    assert 'array_start' in handler.events
    assert ('number', 1) in handler.events
    assert ('number', 2) in handler.events
    assert ('number', 3) in handler.events
    assert 'array_end' in handler.events

def test_parse_nested_structures():
    handler = _TestHandler()
    parse(io.StringIO('{"a": [1, {"b": "c"}]}'), handler, 10)
    assert 'object_start' in handler.events
    assert ('key', 'a') in handler.events
    assert 'array_start' in handler.events
    assert ('number', 1) in handler.events
    assert 'object_start' in handler.events
    assert ('key', 'b') in handler.events
    assert ('string', 'c') in handler.events
    assert 'object_end' in handler.events
    assert 'array_end' in handler.events
    assert 'object_end' in handler.events

def test_parse_string_escapes():
    handler = _TestHandler()
    json_str = r'{"key": "line1\nline2\ttab\"quote\\backslash"}'
    parse(io.StringIO(json_str), handler, 10)
    string_events = [event for event in handler.events if isinstance(event, tuple) and event[0] == 'string']
    assert len(string_events) == 1
    s = string_events[0][1]
    assert s == 'line1\nline2\ttab"quote\\backslash'

def test_parse_unicode_escape():
    handler = _TestHandler()
    json_str = '{"key": "\\u00e9"}'
    parse(io.StringIO(json_str), handler, 10)
    string_events = [event for event in handler.events if isinstance(event, tuple) and event[0] == 'string']
    assert len(string_events) == 1
    assert string_events[0][1] == 'é'

def test_parse_bool_and_null():
    handler = _TestHandler()
    parse(io.StringIO('{"true": true, "false": false, "null": null}'), handler, 10)
    assert ('bool', True) in handler.events
    assert ('bool', False) in handler.events
    assert 'null' in handler.events

def test_streaming_large_array():
    handler = _TestHandler()
    json_data = '[' + ','.join(str(i) for i in range(1, 1001)) + ']'
    stream = io.StringIO(json_data)
    parse(stream, handler, 10)
    number_events = [event for event in handler.events if isinstance(event, tuple) and event[0] == 'number']
    assert len(number_events) == 1000
    for i, event in enumerate(number_events):
        assert event[1] == i + 1

def test_recording_handler_basic():
    handler = RecordingHandler()
    parse(io.StringIO('{"a": 1}'), handler, 10)
    recorded = [v for v in handler.__dict__.values() if isinstance(v, list)]
    assert len(recorded) > 0