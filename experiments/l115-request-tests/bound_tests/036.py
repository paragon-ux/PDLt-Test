import io
import json
import unittest
from typing import List, Any

class CallbackRecorder:
    def __init__(self):
        self.callbacks = []
    
    def on_object_start(self):
        self.callbacks.append('object_start')
    
    def on_object_end(self):
        self.callbacks.append('object_end')
    
    def on_array_start(self):
        self.callbacks.append('array_start')
    
    def on_array_end(self):
        self.callbacks.append('array_end')
    
    def on_key(self, key: str):
        self.callbacks.append(('key', key))
    
    def on_value(self, value: Any):
        self.callbacks.append(('value', value))
    
    def on_string(self, s: str):
        self.callbacks.append(('string', s))
    
    def on_number(self, n: float):
        self.callbacks.append(('number', n))
    
    def on_bool(self, b: bool):
        self.callbacks.append(('bool', b))
    
    def on_null(self):
        self.callbacks.append('null')

class TestJSONSAXParser(unittest.TestCase):
    def test_basic_object(self):
        stream = io.StringIO('{"key": "value"}')
        recorder = CallbackRecorder()
        parse(stream, recorder)
        expected = [
            'object_start',
            ('key', 'key'),
            ('string', 'value'),
            'object_end'
        ]
        self.assertEqual(recorder.callbacks, expected)
    
    def test_basic_array(self):
        stream = io.StringIO('[1, 2, 3]')
        recorder = CallbackRecorder()
        parse(stream, recorder)
        expected = [
            'array_start',
            ('number', 1.0),
            ('number', 2.0),
            ('number', 3.0),
            'array_end'
        ]
        self.assertEqual(recorder.callbacks, expected)
    
    def test_nested_structures(self):
        stream = io.StringIO('{"a": [1, {"b": "c"}]}')
        recorder = CallbackRecorder()
        parse(stream, recorder)
        expected = [
            'object_start',
            ('key', 'a'),
            'array_start',
            ('number', 1.0),
            'object_start',
            ('key', 'b'),
            ('string', 'c'),
            'object_end',
            'array_end',
            'object_end'
        ]
        self.assertEqual(recorder.callbacks, expected)
    
    def test_string_escapes(self):
        test_cases = [
            ('"hello\\nworld"', 'hello\nworld'),
            ('"quote\\""', 'quote"'),
            ('"tab\\ttab"', 'tab\ttab'),
            ('"backslash\\\\"', 'backslash\\'),
            ('"unicode \\u00e9"', 'unicode é')
        ]
        for json_str, expected_str in test_cases:
            with self.subTest(json_str=json_str):
                stream = io.StringIO(json_str)
                recorder = CallbackRecorder()
                parse(stream, recorder)
                self.assertEqual(recorder.callbacks, [('string', expected_str)])
    
    def test_boolean_and_null(self):
        stream = io.StringIO('[true, false, null]')
        recorder = CallbackRecorder()
        parse(stream, recorder)
        expected = [
            'array_start',
            ('bool', True),
            ('bool', False),
            'null',
            'array_end'
        ]
        self.assertEqual(recorder.callbacks, expected)
    
    def test_large_array_streaming(self):
        # Create a 1000-element array
        large_array = list(range(1000))
        json_str = json.dumps(large_array)
        stream = io.StringIO(json_str)
        recorder = CallbackRecorder()
        parse(stream, recorder)
        
        # Verify callbacks
        self.assertEqual(recorder.callbacks[0], 'array_start')
        self.assertEqual(recorder.callbacks[-1], 'array_end')
        
        # Check all numbers are present
        number_callbacks = [cb for cb in recorder.callbacks if isinstance(cb, tuple) and cb[0] == 'number']
        self.assertEqual(len(number_callbacks), 1000)
        
        # Verify numbers are in order
        for i, cb in enumerate(number_callbacks):
            self.assertEqual(cb[1], float(i))
    
    def test_chunked_reading(self):
        # Test that parser works with chunked reading
        json_str = '{"x": 1, "y": [2, 3, 4]}'
        stream = ChunkedStringIO(json_str, chunk_size=3)
        recorder = CallbackRecorder()
        parse(stream, recorder)
        
        expected = [
            'object_start',
            ('key', 'x'),
            ('number', 1.0),
            ('key', 'y'),
            'array_start',
            ('number', 2.0),
            ('number', 3.0),
            ('number', 4.0),
            'array_end',
            'object_end'
        ]
        self.assertEqual(recorder.callbacks, expected)

class ChunkedStringIO(io.StringIO):
    def __init__(self, initial_value='', chunk_size=10):
        super().__init__(initial_value)
        self.chunk_size = chunk_size
    
    def read(self, size=-1):
        if size == -1:
            return super().read()
        return super().read(min(size, self.chunk_size))

if __name__ == '__main__':
    unittest.main()
