import io
import json
import unittest

class TestStreamingJSONParser(unittest.TestCase):
    
    def test_basic_object_callbacks(self):
        """Test object start/end and key/value callbacks"""
        class Handler:
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
        
        handler = Handler()
        json_str = '{"name": "John", "age": 30}'
        parse(io.StringIO(json_str), handler, 10)
        
        expected = [
            'object_start',
            ('key', 'name'),
            ('value', 'John'),
            ('string', 'John'),
            ('key', 'age'),
            ('value', 30),
            ('number', 30),
            'object_end'
        ]
        self.assertEqual(handler.events, expected)
    
    def test_basic_array_callbacks(self):
        """Test array start/end and value callbacks"""
        class Handler:
            def __init__(self):
                self.events = []
            def on_array_start(self): self.events.append('array_start')
            def on_array_end(self): self.events.append('array_end')
            def on_value(self, value): self.events.append(('value', value))
            def on_number(self, n): self.events.append(('number', n))
            def on_string(self, s): self.events.append(('string', s))
            def on_bool(self, b): self.events.append(('bool', b))
            def on_null(self): self.events.append('null')
        
        handler = Handler()
        json_str = '[1, "hello", true, null]'
        parse(io.StringIO(json_str), handler, 10)
        
        expected = [
            'array_start',
            ('value', 1), ('number', 1),
            ('value', 'hello'), ('string', 'hello'),
            ('value', True), ('bool', True),
            ('value', None), 'null',
            'array_end'
        ]
        self.assertEqual(handler.events, expected)
    
    def test_string_escapes(self):
        """Test string escape sequences: \\, \n, \t, \", \uXXXX"""
        class Handler:
            def __init__(self):
                self.string_value = None
            def on_string(self, s): self.string_value = s
        
        handler = Handler()
        # Test all escape sequences including unicode
        json_str = '"line1\\nline2\\ttab\\"quote\\\\backslash\\u0041"'
        parse(io.StringIO(json_str), handler, 10)
        
        expected = 'line1\nline2\ttab"quote\\backslashA'
        self.assertEqual(handler.string_value, expected)
    
    def test_nested_structures(self):
        """Test nested objects and arrays of arbitrary depth"""
        class Handler:
            def __init__(self):
                self.events = []
            def on_object_start(self): self.events.append('obj_start')
            def on_object_end(self): self.events.append('obj_end')
            def on_array_start(self): self.events.append('arr_start')
            def on_array_end(self): self.events.append('arr_end')
            def on_key(self, key): self.events.append(('key', key))
            def on_value(self, value): self.events.append(('val', value))
        
        handler = Handler()
        json_str = '{"outer": [1, {"inner": [2, 3]}]}'
        parse(io.StringIO(json_str), handler, 10)
        
        # Verify nesting structure without checking all details
        self.assertIn('obj_start', handler.events)
        self.assertIn('arr_start', handler.events)
        self.assertIn(('key', 'outer'), handler.events)
        self.assertIn(('key', 'inner'), handler.events)
        self.assertIn('obj_end', handler.events)
        self.assertIn('arr_end', handler.events)
    
    def test_1000_element_array(self):
        """Test streaming 1000-element array with memory efficiency"""
        class CountingHandler:
            def __init__(self):
                self.count = 0
                self.last_value = None
                self.values = []  # Should not store all values if memory efficient
            
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_value(self, value):
                self.count += 1
                self.last_value = value
                # In a truly memory-efficient parser, we wouldn't store all values
                # but we can't test memory usage directly, so we test callback count
            def on_number(self, n): pass
        
        handler = CountingHandler()
        # Create 1000-element JSON array
        json_array = '[' + ','.join(str(i) for i in range(1000)) + ']'
        parse(io.StringIO(json_array), handler, 50)
        
        self.assertEqual(handler.count, 1000)
        self.assertEqual(handler.last_value, 999)
    
    def test_boolean_and_null_callbacks(self):
        """Test on_bool and on_null callbacks"""
        class Handler:
            def __init__(self):
                self.bool_called = False
                self.null_called = False
                self.bool_value = None
            
            def on_bool(self, b):
                self.bool_called = True
                self.bool_value = b
            
            def on_null(self):
                self.null_called = True
        
        handler = Handler()
        json_str = '[true, false, null]'
        parse(io.StringIO(json_str), handler, 10)
        
        self.assertTrue(handler.bool_called)
        self.assertTrue(handler.null_called)
        self.assertTrue(handler.bool_value in [True, False])
    
    def test_number_parsing(self):
        """Test various number formats"""
        class Handler:
            def __init__(self):
                self.numbers = []
            def on_number(self, n): self.numbers.append(n)
        
        handler = Handler()
        json_str = '[42, -17, 3.14, -0.5, 1e10, 2.5e-3]'
        parse(io.StringIO(json_str), handler, 10)
        
        self.assertEqual(len(handler.numbers), 6)
        self.assertEqual(handler.numbers[0], 42)
        self.assertEqual(handler.numbers[1], -17)
        self.assertAlmostEqual(handler.numbers[2], 3.14)
        self.assertAlmostEqual(handler.numbers[3], -0.5)
        self.assertAlmostEqual(handler.numbers[4], 1e10)
        self.assertAlmostEqual(handler.numbers[5], 2.5e-3)
    
    def test_chunked_parsing(self):
        """Test that parsing works with different chunk sizes"""
        class Handler:
            def __init__(self):
                self.values = []
            def on_value(self, value): self.values.append(value)
            def on_number(self, n): pass
            def on_string(self, s): pass
            def on_bool(self, b): pass
            def on_null(self): pass
        
        json_str = '[1, "two", false, null, 3.14]'
        
        # Test with very small chunk size
        handler1 = Handler()
        parse(io.StringIO(json_str), handler1, 2)
        self.assertEqual(len(handler1.values), 5)
        
        # Test with larger chunk size
        handler2 = Handler()
        parse(io.StringIO(json_str), handler2, 100)
        self.assertEqual(len(handler2.values), 5)
        
        # Results should be identical
        self.assertEqual(handler1.values, handler2.values)

if __name__ == '__main__':
    unittest.main()
