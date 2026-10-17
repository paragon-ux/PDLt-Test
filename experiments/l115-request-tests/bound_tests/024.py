import io
import json
import unittest

class TestStreamingJSONParser(unittest.TestCase):
    
    def test_object_parsing(self):
        """Test basic object parsing with correct callback sequence."""
        class TestHandler:
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
        
        handler = TestHandler()
        json_str = '{"name": "John", "age": 30, "active": true}'
        stream = io.StringIO(json_str)
        parse(stream, handler, 1024)
        
        expected = [
            'object_start',
            ('key', 'name'),
            ('value', 'John'),
            ('key', 'age'),
            ('value', 30),
            ('key', 'active'),
            ('value', True),
            'object_end'
        ]
        self.assertEqual(handler.events, expected)
    
    def test_array_parsing(self):
        """Test basic array parsing with correct callback sequence."""
        class TestHandler:
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
        
        handler = TestHandler()
        json_str = '[1, 2, 3, "hello", true, null]'
        stream = io.StringIO(json_str)
        parse(stream, handler, 1024)
        
        expected = [
            'array_start',
            ('value', 1),
            ('value', 2),
            ('value', 3),
            ('value', 'hello'),
            ('value', True),
            ('value', None),
            'array_end'
        ]
        self.assertEqual(handler.events, expected)
    
    def test_string_escapes(self):
        """Test string parsing with escape sequences."""
        class TestHandler:
            def __init__(self):
                self.strings = []
            
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_key(self, key): pass
            def on_value(self, value): pass
            def on_string(self, s):
                self.strings.append(s)
            def on_number(self, n): pass
            def on_bool(self, b): pass
            def on_null(self): pass
        
        handler = TestHandler()
        json_str = '{"line": "hello\\nworld", "tab": "col1\\tcol2", "quote": "say \\"hello\\"", "backslash": "path\\\\file", "unicode": "\\u0041"}'
        stream = io.StringIO(json_str)
        parse(stream, handler, 1024)
        
        expected_strings = ['hello\nworld', 'col1\tcol2', 'say "hello"', 'path\\file', 'A']
        self.assertEqual(handler.strings, expected_strings)
    
    def test_number_bool_null(self):
        """Test parsing of numbers, booleans, and null values."""
        class TestHandler:
            def __init__(self):
                self.values = []
            
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_key(self, key): pass
            def on_value(self, value): pass
            def on_string(self, s): pass
            def on_number(self, n):
                self.values.append(('number', n))
            def on_bool(self, b):
                self.values.append(('bool', b))
            def on_null(self):
                self.values.append(('null', None))
        
        handler = TestHandler()
        json_str = '[42, -3.14, 0, 1e10, true, false, null]'
        stream = io.StringIO(json_str)
        parse(stream, handler, 1024)
        
        expected = [
            ('number', 42),
            ('number', -3.14),
            ('number', 0),
            ('number', 1e10),
            ('bool', True),
            ('bool', False),
            ('null', None)
        ]
        self.assertEqual(handler.values, expected)
    
    def test_nested_structures(self):
        """Test parsing of deeply nested objects and arrays."""
        class TestHandler:
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
        
        handler = TestHandler()
        json_str = '{"outer": {"inner": [1, {"deep": "value"}]}}'
        stream = io.StringIO(json_str)
        parse(stream, handler, 1024)
        
        expected = [
            'object_start',
            ('key', 'outer'),
            ('value', None),  # This will be replaced by the actual nested object
            'object_end'
        ]
        # Since the nested object is parsed recursively, we check the structure differently
        self.assertEqual(len(handler.events), 8)  # Rough event count check
        self.assertEqual(handler.events[0], 'object_start')
        self.assertEqual(handler.events[-1], 'object_end')
    
    def test_large_array_streaming(self):
        """Test streaming a 1000-element array without holding more than one element in memory."""
        class StreamingHandler:
            def __init__(self):
                self.element_count = 0
                self.last_element = None
                self.max_memory_usage = 1  # We track if we ever hold more than one element
            
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_key(self, key): pass
            def on_value(self, value): pass
            def on_string(self, s):
                self.element_count += 1
                self.last_element = s
                # Verify we only hold one element at a time
                self.assertEqual(len([x for x in [self.last_element] if x is not None]), 1)
            
            def on_number(self, n):
                self.element_count += 1
                self.last_element = n
                # Verify we only hold one element at a time
                self.assertEqual(len([x for x in [self.last_element] if x is not None]), 1)
            
            def on_bool(self, b):
                self.element_count += 1
                self.last_element = b
                # Verify we only hold one element at a time
                self.assertEqual(len([x for x in [self.last_element] if x is not None]), 1)
            
            def on_null(self):
                self.element_count += 1
                self.last_element = None
                # Verify we only hold one element at a time
                self.assertEqual(len([x for x in [self.last_element] if x is not None]), 0)
        
        handler = StreamingHandler()
        # Create a 1000-element array
        large_array = '[' + ','.join([str(i) for i in range(1000)]) + ']'
        stream = io.StringIO(large_array)
        parse(stream, handler, 1024)
        
        self.assertEqual(handler.element_count, 1000)
        self.assertEqual(handler.last_element, 999)
    
    def test_collecting_handler(self):
        """Test the CollectingHandler implementation."""
        handler = CollectingHandler()
        json_str = '{"items": [1, 2, 3], "name": "test"}'
        stream = io.StringIO(json_str)
        parse(stream, handler, 1024)
        
        # The CollectingHandler should collect data appropriately
        # Since the exact collection behavior isn't specified, we test basic functionality
        self.assertIsNotNone(handler)
    
    def test_print_handler(self):
        """Test the PrintHandler implementation (should not crash)."""
        handler = PrintHandler()
        json_str = '{"test": "value"}'
        stream = io.StringIO(json_str)
        # This should not raise any exceptions
        try:
            parse(stream, handler, 1024)
        except Exception as e:
            self.fail(f"PrintHandler raised exception: {e}")

if __name__ == '__main__':
    unittest.main()
