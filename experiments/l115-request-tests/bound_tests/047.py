import io
import json
from typing import List, Any

class RecordingHandler:
    def __init__(self):
        self.events: List[tuple] = []
        self.current_object_context: dict = {}
        self.current_array_context: list = []
        self.expected_key: str = None

    def on_object_start(self):
        self.events.append(('object_start',))
        self.current_object_context = {}

    def on_object_end(self):
        self.events.append(('object_end',))
        self.current_object_context = {}

    def on_array_start(self):
        self.events.append(('array_start',))
        self.current_array_context = []

    def on_array_end(self):
        self.events.append(('array_end',))
        self.current_array_context = []

    def on_key(self, key):
        self.events.append(('key', key))
        self.expected_key = key

    def on_value(self, v):
        if self.expected_key is not None:
            self.current_object_context[self.expected_key] = v
            self.expected_key = None
        else:
            self.current_array_context.append(v)
        self.events.append(('value', v))

    def on_string(self, s):
        self.on_value(s)
        self.events.append(('string', s))

    def on_number(self, n):
        self.on_value(n)
        self.events.append(('number', n))

    def on_bool(self, b):
        self.on_value(b)
        self.events.append(('bool', b))

    def on_null(self):
        self.on_value(None)
        self.events.append(('null',))

def generate_large_json_array(n: int) -> str:
    """Generate a JSON array string with n integer elements."""
    return json.dumps(list(range(n)))

class StreamingJSONParser:
    def __init__(self, chunk_size: int):
        self.chunk_size = chunk_size
        self.buffer = ""
        self.pos = 0
        self.state = "start"
        self.stack = []
        self.current_string = ""
        self.unicode_buffer = ""
        self.unicode_count = 0
        self.escape_next = False

    def parse(self, stream, handler):
        while True:
            chunk = stream.read(self.chunk_size)
            if not chunk:
                break
            self.buffer += chunk
            self._process_buffer(handler)
        
        # Process any remaining data
        if self.buffer:
            self._process_buffer(handler, final=True)

    def _process_buffer(self, handler, final=False):
        i = 0
        while i < len(self.buffer):
            char = self.buffer[i]
            
            if self.state == "start":
                if char.isspace():
                    i += 1
                    continue
                self.state = "value"
                continue
            
            if self.state == "value":
                if char.isspace():
                    i += 1
                    continue
                if char == '{':
                    handler.on_object_start()
                    self.stack.append('object')
                    self.state = "object_key_or_end"
                elif char == '[':
                    handler.on_array_start()
                    self.stack.append('array')
                    self.state = "array_value_or_end"
                elif char == '"':
                    self.state = "string"
                    self.current_string = ""
                elif char == 't':
                    self.state = "true"
                    self.buffer = self.buffer[i:]
                    return
                elif char == 'f':
                    self.state = "false"
                    self.buffer = self.buffer[i:]
                    return
                elif char == 'n':
                    self.state = "null"
                    self.buffer = self.buffer[i:]
                    return
                elif char in '-0123456789':
                    self.state = "number"
                    self.buffer = self.buffer[i:]
                    return
                else:
                    raise ValueError(f"Unexpected character: {char}")
            
            elif self.state == "object_key_or_end":
                if char.isspace():
                    i += 1
                    continue
                if char == '}':
                    handler.on_object_end()
                    self.stack.pop()
                    if self.stack:
                        self.state = self.stack[-1] + "_after_value"
                    else:
                        self.state = "done"
                elif char == '"':
                    self.state = "string_key"
                    self.current_string = ""
                else:
                    raise ValueError(f"Expected key or end of object, got: {char}")
            
            elif self.state == "array_value_or_end":
                if char.isspace():
                    i += 1
                    continue
                if char == ']':
                    handler.on_array_end()
                    self.stack.pop()
                    if self.stack:
                        self.state = self.stack[-1] + "_after_value"
                    else:
                        self.state = "done"
                else:
                    self.state = "value"
                    continue
            
            elif self.state == "string" or self.state == "string_key":
                if self.escape_next:
                    if char == 'u':
                        self.unicode_buffer = ""
                        self.unicode_count = 0
                        self.state = "unicode_escape"
                        self.escape_next = False
                    else:
                        escape_map = {
                            '"': '"', '\\': '\\', '/': '/',
                            'b': '\b', 'f': '\f', 'n': '\n',
                            'r': '\r', 't': '\t'
                        }
                        self.current_string += escape_map.get(char, char)
                        self.escape_next = False
                elif char == '\\':
                    self.escape_next = True
                elif char == '"':
                    if self.state == "string":
                        handler.on_string(self.current_string)
                    else:  # string_key
                        handler.on_key(self.current_string)
                        self.state = "object_colon"
                    self.state = "value" if self.state == "string" else "object_colon"
                else:
                    self.current_string += char
            
            elif self.state == "object_colon":
                if char.isspace():
                    i += 1
                    continue
                if char == ':':
                    self.state = "value"
                else:
                    raise ValueError(f"Expected colon, got: {char}")
            
            elif self.state == "object_after_value":
                if char.isspace():
                    i += 1
                    continue
                if char == ',':
                    self.state = "object_key_or_end"
                elif char == '}':
                    handler.on_object_end()
                    self.stack.pop()
                    if self.stack:
                        self.state = self.stack[-1] + "_after_value"
                    else:
                        self.state = "done"
                else:
                    raise ValueError(f"Expected comma or end, got: {char}")
            
            elif self.state == "array_after_value":
                if char.isspace():
                    i += 1
                    continue
                if char == ',':
                    self.state = "array_value_or_end"
                elif char == ']':
                    handler.on_array_end()
                    self.stack.pop()
                    if self.stack:
                        self.state = self.stack[-1] + "_after_value"
                    else:
                        self.state = "done"
                else:
                    raise ValueError(f"Expected comma or end, got: {char}")
            
            elif self.state == "unicode_escape":
                if char in '0123456789abcdefABCDEF':
                    self.unicode_buffer += char
                    self.unicode_count += 1
                    if self.unicode_count == 4:
                        code_point = int(self.unicode_buffer, 16)
                        self.current_string += chr(code_point)
                        self.state = "string" if self.state == "string" else "string_key"
                else:
                    raise ValueError(f"Invalid unicode escape: \\u{self.unicode_buffer}")
            
            elif self.state in ["true", "false", "null"]:
                expected = self.state[1:]
                if char != expected[len(self.buffer) - i - 1]:
                    raise ValueError(f"Invalid literal: {self.state}")
                if len(self.buffer) - i - 1 == len(expected) - 1:
                    if self.state == "true":
                        handler.on_bool(True)
                    elif self.state == "false":
                        handler.on_bool(False)
                    elif self.state == "null":
                        handler.on_null()
                    self.state = "value" if self.stack and self.stack[-1] == 'array' else "object_after_value"
                i += 1
                continue
            
            elif self.state == "number":
                if char.isspace() or char in ',}]':
                    # End of number
                    try:
                        num = float(self.buffer)
                        if num.is_integer():
                            num = int(num)
                        handler.on_number(num)
                    except ValueError:
                        raise ValueError(f"Invalid number: {self.buffer}")
                    self.state = "value" if self.stack and self.stack[-1] == 'array' else "object_after_value"
                    self.buffer = ""
                    continue
                else:
                    self.buffer += char
            
            i += 1
        
        self.buffer = self.buffer[i:] if i < len(self.buffer) else ""

def test_basic_types():
    handler = RecordingHandler()
    parser = StreamingJSONParser(chunk_size=10)
    json_str = '{"a": 1, "b": "hello", "c": true, "d": null}'
    parser.parse(io.StringIO(json_str), handler)
    
    events = handler.events
    assert ('object_start',) in events
    assert ('key', 'a') in events
    assert ('number', 1) in events
    assert ('key', 'b') in events
    assert ('string', 'hello') in events
    assert ('key', 'c') in events
    assert ('bool', True) in events
    assert ('key', 'd') in events
    assert ('null',) in events
    assert ('object_end',) in events

def test_nested_structures():
    handler = RecordingHandler()
    parser = StreamingJSONParser(chunk_size=10)
    json_str = '{"arr": [1, {"inner": "value"}], "obj": {"nested": [2, 3]}}'
    parser.parse(io.StringIO(json_str), handler)
    
    events = handler.events
    assert ('object_start',) in events
    assert ('key', 'arr') in events
    assert ('array_start',) in events
    assert ('number', 1) in events
    assert ('object_start',) in events
    assert ('key', 'inner') in events
    assert ('string', 'value') in events
    assert ('object_end',) in events
    assert ('array_end',) in events
    assert ('key', 'obj') in events
    assert ('object_start',) in events
    assert ('key', 'nested') in events
    assert ('array_start',) in events
    assert ('number', 2) in events
    assert ('number', 3) in events
    assert ('array_end',) in events
    assert ('object_end',) in events
    assert ('object_end',) in events

def test_escape_sequences():
    handler = RecordingHandler()
    parser = StreamingJSONParser(chunk_size=10)
    json_str = r'{"text": "line1\nline2\ttab\"quote\\backslash\u0041"}'
    parser.parse(io.StringIO(json_str), handler)
    
    events = handler.events
    assert ('key', 'text') in events
    string_event = next(e for e in events if e[0] == 'string')
    expected = 'line1\nline2\ttab"quote\\backslashA'
    assert string_event[1] == expected

def test_large_array():
    n = 1000
    handler = RecordingHandler()
    parser = StreamingJSONParser(chunk_size=100)
    json_str = generate_large_json_array(n)
    parser.parse(io.StringIO(json_str), handler)
    
    # Verify array structure
    assert ('array_start',) in handler.events
    assert ('array_end',) in handler.events
    
    # Count number events (should be exactly n)
    number_events = [e for e in handler.events if e[0] == 'number']
    assert len(number_events) == n
    
    # Verify values are in order
    for i, event in enumerate(number_events):
        assert event[1] == i
    
    # Verify no intermediate structures (only array and numbers)
    non_number_events = [e for e in handler.events if e[0] != 'number']
    assert len(non_number_events) == 2  # array_start and array_end

def test_streaming_memory_efficiency():
    """Test that parser doesn't hold entire structure in memory."""
    handler = RecordingHandler()
    parser = StreamingJSONParser(chunk_size=50)
    
    # Create a generator that yields chunks
    class ChunkedStream:
        def __init__(self, data, chunk_size):
            self.data = data
            self.chunk_size = chunk_size
            self.pos = 0
        
        def read(self, size=-1):
            if self.pos >= len(self.data):
                return ""
            end = self.pos + self.chunk_size if size == -1 else min(self.pos + size, len(self.data))
            chunk = self.data[self.pos:end]
            self.pos = end
            return chunk
    
    json_str = generate_large_json_array(100)
    stream = ChunkedStream(json_str, 50)
    parser.parse(stream, handler)
    
    # Verify we got all numbers
    number_events = [e for e in handler.events if e[0] == 'number']
    assert len(number_events) == 100
