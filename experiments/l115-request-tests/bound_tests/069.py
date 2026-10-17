import io

class _RecordingHandler:
    def __init__(self):
        self.events = []
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

def test_empty_object():
    handler = _RecordingHandler()
    parse(io.StringIO("{}"), handler)
    assert ('object_start',) in handler.events, "Missing object_start"
    assert ('object_end',) in handler.events, "Missing object_end"

def test_empty_array():
    handler = _RecordingHandler()
    parse(io.StringIO("[]"), handler)
    assert ('array_start',) in handler.events, "Missing array_start"
    assert ('array_end',) in handler.events, "Missing array_end"

def test_simple_object_with_string():
    handler = _RecordingHandler()
    parse(io.StringIO('{"key": "value"}'), handler)
    assert ('object_start',) in handler.events
    assert ('object_end',) in handler.events
    assert ('key', 'key') in handler.events
    assert ('string', 'value') in handler.events

def test_string_with_backslash():
    handler = _RecordingHandler()
    parse(io.StringIO(r'"a\\b"'), handler)
    string_events = [e for e in handler.events if e[0] == 'string']
    assert len(string_events) == 1, "Expected one string event"
    assert string_events[0][1] == 'a\\b', f"Expected 'a\\b', got {repr(string_events[0][1])}"

def test_string_with_newline():
    handler = _RecordingHandler()
    parse(io.StringIO(r'"line1\nline2"'), handler)
    string_events = [e for e in handler.events if e[0] == 'string']
    assert len(string_events) == 1, "Expected one string event"
    assert string_events[0][1] == 'line1\nline2', f"Expected 'line1\\nline2', got {repr(string_events[0][1])}"

def test_string_with_tab():
    handler = _RecordingHandler()
    parse(io.StringIO(r'"col1\tcol2"'), handler)
    string_events = [e for e in handler.events if e[0] == 'string']
    assert len(string_events) == 1, "Expected one string event"
    assert string_events[0][1] == 'col1\tcol2', f"Expected 'col1\\tcol2', got {repr(string_events[0][1])}"

def test_string_with_quote():
    handler = _RecordingHandler()
    parse(io.StringIO(r'"say \"hello\""'), handler)
    string_events = [e for e in handler.events if e[0] == 'string']
    assert len(string_events) == 1, "Expected one string event"
    assert string_events[0][1] == 'say "hello"', f"Expected 'say \"hello\"', got {repr(string_events[0][1])}"

def test_unicode_escape():
    handler = _RecordingHandler()
    parse(io.StringIO(r'"\u00e9"'), handler)
    string_events = [e for e in handler.events if e[0] == 'string']
    assert len(string_events) == 1, "Expected one string event"
    assert string_events[0][1] == 'é', f"Expected 'é', got {repr(string_events[0][1])}"

def test_number():
    handler = _RecordingHandler()
    parse(io.StringIO('42'), handler)
    number_events = [e for e in handler.events if e[0] == 'number']
    assert len(number_events) == 1, "Expected one number event"
    assert number_events[0][1] == 42, f"Expected 42, got {number_events[0][1]}"

def test_boolean_true():
    handler = _RecordingHandler()
    parse(io.StringIO('true'), handler)
    bool_events = [e for e in handler.events if e[0] == 'bool']
    assert len(bool_events) == 1, "Expected one bool event"
    assert bool_events[0][1] is True, "Expected True"

def test_boolean_false():
    handler = _RecordingHandler()
    parse(io.StringIO('false'), handler)
    bool_events = [e for e in handler.events if e[0] == 'bool']
    assert len(bool_events) == 1, "Expected one bool event"
    assert bool_events[0][1] is False, "Expected False"

def test_null():
    handler = _RecordingHandler()
    parse(io.StringIO('null'), handler)
    null_events = [e for e in handler.events if e[0] == 'null']
    assert len(null_events) == 1, "Expected one null event"

def test_nested_object():
    handler = _RecordingHandler()
    parse(io.StringIO('{"a":{"b":1}}'), handler)
    object_starts = [e for e in handler.events if e[0] == 'object_start']
    object_ends = [e for e in handler.events if e[0] == 'object_end']
    assert len(object_starts) == 2, "Expected two object_start"
    assert len(object_ends) == 2, "Expected two object_end"
    assert ('key', 'a') in handler.events
    assert ('key', 'b') in handler.events
    number_events = [e for e in handler.events if e[0] == 'number']
    assert len(number_events) == 1, "Expected one number event"
    assert number_events[0][1] == 1, "Expected number 1"

def test_nested_array():
    handler = _RecordingHandler()
    parse(io.StringIO('[1, [2, 3]]'), handler)
    array_starts = [e for e in handler.events if e[0] == 'array_start']
    array_ends = [e for e in handler.events if e[0] == 'array_end']
    assert len(array_starts) == 2, "Expected two array_start"
    assert len(array_ends) == 2, "Expected two array_end"
    number_events = [e for e in handler.events if e[0] == 'number']
    assert len(number_events) == 3, "Expected three number events"
    numbers = [e[1] for e in number_events]
    assert numbers == [1, 2, 3], f"Expected numbers [1,2,3], got {numbers}"

def test_streaming_1000_element_array():
    numbers = ','.join(str(i) for i in range(1000))
    json_str = '[' + numbers + ']'
    handler = _RecordingHandler()
    parse(io.StringIO(json_str), handler)
    array_starts = [e for e in handler.events if e[0] == 'array_start']
    array_ends = [e for e in handler.events if e[0] == 'array_end']
    assert len(array_starts) == 1, "Expected one array_start"
    assert len(array_ends) == 1, "Expected one array_end"
    number_events = [e for e in handler.events if e[0] == 'number']
    assert len(number_events) == 1000,