import io
import json
import unittest

class MockHandler:
    def __init__(self):
        self.calls = []
        self.current_path = []
    
    def on_object_start(self):
        self.calls.append(('object_start',))
        self.current_path.append({})
    
    def on_object_end(self):
        self.calls.append(('object_end',))
        self.current_path.pop()
    
    def on_array_start(self):
        self.calls.append(('array_start',))
        self.current_path.append([])
    
    def on_array_end(self):
        self.calls.append(('array_end',))
        self.current_path.pop()
    
    def on_key(self, key):
        self.calls.append(('key', key))
    
    def on_value(self, value):
        self.calls.append(('value', value))
    
    def on_string(self, s):
        self.calls.append(('string', s))
    
    def on_number(self, n):
        self.calls.append(('number', n))
    
    def on_bool(self, b):
        self.calls.append(('bool', b))
    
    def on_null(self):
        self.calls.append(('null',))

class TestStreamingJSONParser(unittest.TestCase):
    
    def test_parse_simple_object(self):
        handler = MockHandler()
        stream = io.StringIO('{"name": "John", "age": 30}')
        parse(stream, handler)
        
        expected = [
            ('object_start',),
            ('key', 'name'),
            ('string', 'John'),
            ('key', 'age'),
            ('number', 30),
            ('object_end',)
        ]
        self.assertEqual(handler.calls, expected)
    
    def test_parse_simple_array(self):
        handler = MockHandler()
        stream = io.StringIO('[1, 2, 3]')
        parse(stream, handler)
        
        expected = [
            ('array_start',),
            ('number', 1),
            ('number', 2),
            ('number', 3),
            ('array_end',)
        ]
        self.assertEqual(handler.calls, expected)
    
    def test_parse_string_escapes(self):
        handler = MockHandler()
        stream = io.StringIO('"hello\\nworld\\ttab\\"quote\\u0041"')
        parse(stream, handler)
        
        self.assertEqual(len(handler.calls), 2)
        self.assertEqual(handler.calls[0][0], 'string')
        self.assertEqual(handler.calls[0][1], 'hello\nworld\ttab"quoteA')
    
    def test_parse_boolean_and_null(self):
        handler = MockHandler()
        stream = io.StringIO('[true, false, null]')
        parse(stream, handler)
        
        expected = [
            ('array_start',),
            ('bool', True),
            ('bool', False),
            ('null',),
            ('array_end',)
        ]
        self.assertEqual(handler.calls, expected)
    
    def test_parse_nested_structure(self):
        handler = MockHandler()
        stream = io.StringIO('{"a": [1, {"b": "c"}]}')
        parse(stream, handler)
        
        expected = [
            ('object_start',),
            ('key', 'a'),
            ('array_start',),
            ('number', 1),
            ('object_start',),
            ('key', 'b'),
            ('string', 'c'),
            ('object_end',),
            ('array_end',),
            ('object_end',)
        ]
        self.assertEqual(handler.calls, expected)
    
    def test_streaming_large_array(self):
        handler = MockHandler()
        large_array = '[' + ','.join(str(i) for i in range(1000)) + ']'
        stream = io.StringIO(large_array)
        parse(stream, handler)
        
        # Verify array start and end
        self.assertEqual(handler.calls[0], ('array_start',))
        self.assertEqual(handler.calls[-1], ('array_end',))
        
        # Verify all 1000 numbers are processed
        number_calls = [call for call in handler.calls if call[0] == 'number']
        self.assertEqual(len(number_calls), 1000)
        
        # Verify numbers are in order
        for i, call in enumerate(number_calls):
            self.assertEqual(call[1], i)
    
    def test_parse_unicode_escape(self):
        handler = MockHandler()
        stream = io.StringIO('"\\u00e9\\u00e0"')
        parse(stream, handler)
        
        self.assertEqual(handler.calls[0], ('string', 'éà'))
    
    def test_parse_empty_object_and_array(self):
        handler = MockHandler()
        stream = io.StringIO('{}[]')
        parse(stream, handler)
        
        expected = [
            ('object_start',),
            ('object_end',),
            ('array_start',),
            ('array_end',)
        ]
        self.assertEqual(handler.calls, expected)

if __name__ == '__main__':
    unittest.main()
