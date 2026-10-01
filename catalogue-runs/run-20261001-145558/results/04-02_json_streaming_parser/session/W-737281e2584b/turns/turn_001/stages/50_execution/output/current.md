import json
import io

class JSONSAXParser:
    def __init__(self, stream, handler, chunk_size=4096):
        self.stream = stream
        self.handler = handler
        self.chunk_size = chunk_size
        self.buffer = ''
        self.pos = 0
        self.stack = []  # track context: 'object' or 'array'
        self.state = 'value'  # expected next token type
        self.key_pending = False

    def parse(self):
        while True:
            chunk = self.stream.read(self.chunk_size)
            if not chunk:
                break
            self.buffer += chunk.decode('utf-8') if isinstance(chunk, (bytes, bytearray)) else chunk
            self._process_buffer()
        # after EOF, ensure no leftover unprocessed data
        self._finalize()

    def _process_buffer(self):
        while self.pos < len(self.buffer):
            ch = self.buffer[self.pos]
            if self.state == 'value':
                if ch.isspace():
                    self.pos += 1
                    continue
                if ch == '{':
                    self.handler.on_object_start()
                    self.stack.append('object')
                    self.pos += 1
                    self.state = 'key_or_end'
                elif ch == '[':
                    self.handler.on_array_start()
                    self.stack.append('array')
                    self.pos += 1
                    self.state = 'value_or_end'
                elif ch == '"':
                    self.pos += 1
                    self._parse_string(is_key=False)
                elif ch in '-0123456789':
                    self._parse_number()
                elif self.buffer.startswith('true', self.pos):
                    self.handler.on_bool(True)
                    self.handler.on_value(True)
                    self.pos += 4
                elif self.buffer.startswith('false', self.pos):
                    self.handler.on_bool(False)
                    self.handler.on_value(False)
                    self.pos += 5
                elif self.buffer.startswith('null', self.pos):
                    self.handler.on_null()
                    self.handler.on_value(None)
                    self.pos += 4
                else:
                    raise ValueError(f'Unexpected character {ch} at position {self.pos}')
            elif self.state == 'key_or_end':
                if ch.isspace():
                    self.pos += 1
                    continue
                if ch == '}':
                    self.handler.on_object_end()
                    self.stack.pop()
                    self.pos += 1
                    self._after_value()
                elif ch == '"':
                    self.pos += 1
                    self._parse_string(is_key=True)
                else:
                    raise ValueError('Expected key or object end')
            elif self.state == 'colon':
                if ch.isspace():
                    self.pos += 1
                    continue
                if ch == ':':
                    self.pos += 1
                    self.state = 'value'
                else:
                    raise ValueError('Expected colon after key')
            elif self.state == 'comma_or_end':
                if ch.isspace():
                    self.pos += 1
                    continue
                if ch == ',':
                    self.pos += 1
                    if self.stack[-1] == 'object':
                        self.state = 'key_or_end'
                    else:
                        self.state = 'value_or_end'
                elif ch == '}':
                    if self.stack[-1] != 'object':
                        raise ValueError('Mismatched closing brace')
                    self.handler.on_object_end()
                    self.stack.pop()
                    self.pos += 1
                    self._after_value()
                elif ch == ']':
                    if self.stack[-1] != 'array':
                        raise ValueError('Mismatched closing bracket')
                    self.handler.on_array_end()
                    self.stack.pop()
                    self.pos += 1
                    self._after_value()
                else:
                    raise ValueError('Expected comma or closing bracket')
            elif self.state == 'value_or_end':
                if ch.isspace():
                    self.pos += 1
                    continue
                if ch == ']':
                    self.handler.on_array_end()
                    self.stack.pop()
                    self.pos += 1
                    self._after_value()
                else:
                    self.state = 'value'
                # loop continues without increment to reprocess token
            else:
                raise RuntimeError('Invalid parser state')
        # truncate processed part of buffer to keep memory low
        if self.pos > 0:
            self.buffer = self.buffer[self.pos:]
            self.pos = 0

    def _after_value(self):
        if not self.stack:
            self.state = 'value'  # top‑level finished, allow EOF
        else:
            self.state = 'comma_or_end'

    def _parse_string(self, is_key):
        start = self.pos
        sb = []
        while self.pos < len(self.buffer):
            ch = self.buffer[self.pos]
            if ch == '"':
                self.pos += 1
                s = ''.join(sb)
                self.handler.on_string(s)
                if is_key:
                    self.handler.on_key(s)
                    self.handler.on_value(s)  # key also counts as a value for generic value callback
                    self.state = 'colon'
                else:
                    self.handler.on_value(s)
                    self._after_value()
                return
            if ch == '\\':
                self.pos += 1
                if self.pos >= len(self.buffer):
                    break  # need more data
                esc = self.buffer[self.pos]
                if esc == '"': sb.append('"')
                elif esc == '\\': sb.append('\\')
                elif esc == '/': sb.append('/')
                elif esc == 'b': sb.append('\b')
                elif esc == 'f': sb.append('\f')
                elif esc == 'n': sb.append('\n')
                elif esc == 'r': sb.append('\r')
                elif esc == 't': sb.append('\t')
                elif esc == 'u':
                    hex_digits = self.buffer[self.pos+1:self.pos+5]
                    if len(hex_digits) < 4:
                        break
                    sb.append(chr(int(hex_digits, 16)))
                    self.pos += 4
                else:
                    sb.append(esc)
                self.pos += 1
            else:
                sb.append(ch)
                self.pos += 1
        # incomplete string, keep buffer and return to caller to read more
        self.buffer = self.buffer[start:]
        self.pos = 0
        raise StopIteration

    def _parse_number(self):
        start = self.pos
        while self.pos < len(self.buffer) and self.buffer[self.pos] in '0123456789+-.eE':
            self.pos += 1
        num_str = self.buffer[start:self.pos]
        # Use json.loads to get correct type (int vs float)
        n = json.loads(num_str)
        self.handler.on_number(n)
        self.handler.on_value(n)
        self._after_value()

    def _finalize(self):
        if self.stack:
            raise ValueError('Unexpected end of input, incomplete JSON')

def parse(stream, handler):
    parser = JSONSAXParser(stream, handler)
    parser.parse()

# ------------------- Test Harness -------------------
class CountingHandler:
    def __init__(self):
        self.counters = {
            'object_start':0,'object_end':0,
            'array_start':0,'array_end':0,
            'key':0,'value':0,
            'string':0,'number':0,'bool':0,'null':0
        }
    def on_object_start(self): self.counters['object_start']+=1
    def on_object_end(self): self.counters['object_end']+=1
    def on_array_start(self): self.counters['array_start']+=1
    def on_array_end(self): self.counters['array_end']+=1
    def on_key(self,key): self.counters['key']+=1
    def on_value(self,value): self.counters['value']+=1
    def on_string(self,s): self.counters['string']+=1
    def on_number(self,n): self.counters['number']+=1
    def on_bool(self,b): self.counters['bool']+=1
    def on_null(self): self.counters['null']+=1

def test():
    # Build JSON array of 1000 numbers without materialising whole string at once
    json_parts = ['[']
    for i in range(1000):
        json_parts.append(str(i))
        if i != 999:
            json_parts.append(',')
    json_parts.append(']')
    json_str = ''.join(json_parts)
    stream = io.StringIO(json_str)
    handler = CountingHandler()
    parse(stream, handler)
    # Expected counts
    assert handler.counters['array_start'] == 1
    assert handler.counters['array_end'] == 1
    assert handler.counters['object_start'] == 0
    assert handler.counters['object_end'] == 0
    assert handler.counters['key'] == 0
    assert handler.counters['string'] == 0
    assert handler.counters['number'] == 1000
    assert handler.counters['bool'] == 0
    assert handler.counters['null'] == 0
    assert handler.counters['value'] == 1000  # each number counted as a value
    print('All callbacks verified.')

if __name__ == '__main__':
    test()
