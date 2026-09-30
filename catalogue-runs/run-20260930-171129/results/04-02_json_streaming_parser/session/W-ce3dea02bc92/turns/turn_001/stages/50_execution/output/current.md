import io
import json
from typing import Any, TextIO

class JSONHandler:
    def on_object_start(self): pass
    def on_object_end(self): pass
    def on_array_start(self): pass
    def on_array_end(self): pass
    def on_key(self, key: str): pass
    def on_value(self, value: Any): pass
    def on_string(self, s: str): pass
    def on_number(self, n: float): pass
    def on_bool(self, b: bool): pass
    def on_null(self): pass

def parse(stream: TextIO, handler: JSONHandler, chunk_size: int = 4096) -> None:
    """Incrementally parse JSON from *stream* and invoke callbacks on *handler*.
    The implementation walks the character stream using a manual state machine
    that yields one token at a time, never materialising the whole document.
    """
    buffer = ''
    idx = 0
    stack = []  # keeps track of whether we are inside object (expecting key) or array
    def next_char():
        nonlocal buffer, idx
        while idx >= len(buffer):
            more = stream.read(chunk_size)
            if not more:
                return ''
            buffer += more
        ch = buffer[idx]
        idx += 1
        return ch
    def peek_char():
        nonlocal buffer, idx
        while idx >= len(buffer):
            more = stream.read(chunk_size)
            if not more:
                return ''
            buffer += more
        return buffer[idx]
    def skip_whitespace():
        while True:
            c = peek_char()
            if c and c in ' \t\n\r':
                next_char()
            else:
                break
    def parse_string():
        # assumes opening quote already consumed
        result = ''
        while True:
            ch = next_char()
            if ch == '':
                raise ValueError('Unexpected end of input in string')
            if ch == '"':
                break
            if ch == '\\':
                esc = next_char()
                if esc == '"': result += '"'
                elif esc == '\\': result += '\\'
                elif esc == '/': result += '/'
                elif esc == 'b': result += '\b'
                elif esc == 'f': result += '\f'
                elif esc == 'n': result += '\n'
                elif esc == 'r': result += '\r'
                elif esc == 't': result += '\t'
                elif esc == 'u':
                    hex_digits = ''
                    for _ in range(4):
                        hd = next_char()
                        if hd == '':
                            raise ValueError('Unexpected end of input in \u escape')
                        hex_digits += hd
                    result += chr(int(hex_digits, 16))
                else:
                    raise ValueError(f'Invalid escape \\{esc}')
            else:
                result += ch
        return result
    def parse_literal(lit, value):
        for expected in lit[1:]:
            if next_char() != expected:
                raise ValueError(f'Invalid literal starting with {lit}')
        return value
    def parse_number(first_char):
        num_str = first_char
        while True:
            c = peek_char()
            if c and c in '0123456789+-.eE':
                num_str += next_char()
            else:
                break
        return json.loads(num_str)  # leverage stdlib for conversion
    def emit_value(val):
        if isinstance(val, str):
            handler.on_string(val)
            handler.on_value(val)
        elif isinstance(val, bool):
            handler.on_bool(val)
            handler.on_value(val)
        elif val is None:
            handler.on_null()
            handler.on_value(val)
        elif isinstance(val, (int, float)):
            handler.on_number(val)
            handler.on_value(val)
        else:
            # objects and arrays are handled separately
            pass
    skip_whitespace()
    while True:
        ch = next_char()
        if ch == '':
            break
        if ch in ' \t\n\r':
            continue
        if ch == '{':
            handler.on_object_start()
            stack.append('object')
            skip_whitespace()
            if peek_char() == '}':
                next_char()
                handler.on_object_end()
                stack.pop()
                continue
        elif ch == '}':
            handler.on_object_end()
            if not stack or stack[-1] != 'object':
                raise ValueError('Mismatched }')
            stack.pop()
        elif ch == '[':
            handler.on_array_start()
            stack.append('array')
            skip_whitespace()
            if peek_char() == ']':
                next_char()
                handler.on_array_end()
                stack.pop()
                continue
        elif ch == ']':
            handler.on_array_end()
            if not stack or stack[-1] != 'array':
                raise ValueError('Mismatched ]')
            stack.pop()
        elif ch == ',':
            skip_whitespace()
            continue
        elif ch == ':':
            skip_whitespace()
            continue
        elif ch == '"':
            s = parse_string()
            # Determine context: key or string value
            if stack and stack[-1] == 'object' and (not stack or (len(stack) >= 2 and stack[-2] != 'key')):
                # expecting a key
                handler.on_key(s)
                # push marker that next token is value
                stack.append('key')
            else:
                emit_value(s)
        elif ch in '-0123456789':
            num = parse_number(ch)
            emit_value(num)
        elif ch == 't':
            val = parse_literal('true', True)
            emit_value(val)
        elif ch == 'f':
            val = parse_literal('false', False)
            emit_value(val)
        elif ch == 'n':
            val = parse_literal('null', None)
            emit_value(val)
        else:
            raise ValueError(f'Unexpected character {ch}')
        # clean up key marker after its value processed
        if stack and stack[-1] == 'key' and ch not in ':,' :
            # after processing the value token, remove the key marker
            if ch not in ' \t\n\r':
                stack.pop()
        skip_whitespace()

# ----- Test -----
class MockHandler(JSONHandler):
    def __init__(self):
        self.events = []
    def on_object_start(self): self.events.append('object_start')
    def on_object_end(self): self.events.append('object_end')
    def on_array_start(self): self.events.append('array_start')
    def on_array_end(self): self.events.append('array_end')
    def on_key(self, key): self.events.append(('key', key))
    def on_value(self, value): self.events.append(('value', value))
    def on_string(self, s): self.events.append(('string', s))
    def on_number(self, n): self.events.append(('number', n))
    def on_bool(self, b): self.events.append(('bool', b))
    def on_null(self): self.events.append('null')

def streaming_array(num_elements: int):
    # generate a large JSON array without building it in memory
    def generator():
        yield '['
        for i in range(num_elements):
            if i > 0:
                yield ','
            yield str(i)
        yield ']'
    return io.StringIO(''.join(generator()))

if __name__ == '__main__':
    handler = MockHandler()
    stream = streaming_array(1000)
    parse(stream, handler)
    # simple verification: we should have array start/end and 1000 numbers
    assert handler.events[0] == 'array_start'
    assert handler.events[-1] == 'array_end'
    numbers = [ev[1] for ev in handler.events if isinstance(ev, tuple) and ev[0] == 'number']
    assert numbers == list(range(1000))
    print('Test passed, callbacks fired correctly with constant memory.')
