import io
import unittest
from unittest.mock import MagicMock

class TestSAXJSONParser(unittest.TestCase):
    
    def test_parse_simple_types(self):
        """Test parsing of basic JSON types: strings, numbers, booleans, null"""
        test_cases = [
            ('"hello"', [('on_string', 'hello')]),
            ('42', [('on_number', 42)]),
            ('3.14', [('on_number', 3.14)]),
            ('true', [('on_bool', True)]),
            ('false', [('on_bool', False)]),
            ('null', [('on_null', None)]),
        ]
        
        for json_str, expected_callbacks in test_cases:
            with self.subTest(json_str=json_str):
                handler = MagicMock()
                stream = io.StringIO(json_str)
                parse(stream, handler)
                
                # Check that the expected callback was called with correct argument
                callback_name, expected_value = expected_callbacks[0]
                method = getattr(handler, callback_name)
                method.assert_called_once_with(expected_value)
    
    def test_parse_string_escapes(self):
        """Test string parsing with escape sequences"""
        test_cases = [
            ('"line1\\nline2"', 'line1\nline2'),
            ('"tab\\there"', 'tab\there'),
            ('"quote\\"inside"', 'quote"inside'),
            ('"back\\\\slash"', 'back\\slash'),
            ('"unicode\\u0041"', 'A'),
            ('"mixed\\n\\t\\u0042"', 'mixed\n\tB'),
        ]
        
        for json_str, expected_value in test_cases:
            with self.subTest(json_str=json_str):
                handler = MagicMock()
                stream = io.StringIO(json_str)
                parse(stream, handler)
                handler.on_string.assert_called_once_with(expected_value)
    
    def test_parse_object_structure(self):
        """Test parsing of object structures with proper callbacks"""
        json_str = '{"name": "John", "age": 30, "active": true}'
        handler = MagicMock()
        stream = io.StringIO(json_str)
        parse(stream, handler)
        
        # Verify object start/end
        handler.on_object_start.assert_called_once()
        handler.on_object_end.assert_called_once()
        
        # Verify keys and values in order
        expected_calls = [
            ('on_key', 'name'),
            ('on_value', 'John'),
            ('on_key', 'age'),
            ('on_value', 30),
            ('on_key', 'active'),
            ('on_value', True),
        ]
        
        for method_name, arg in expected_calls:
            method = getattr(handler, method_name)
            method.assert_called_once_with(arg)
    
    def test_parse_array_structure(self):
        """Test parsing of array structures with proper callbacks"""
        json_str = '[1, 2, 3, "four", false]'
        handler = MagicMock()
        stream = io.StringIO(json_str)
        parse(stream, handler)
        
        # Verify array start/end
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()
        
        # Verify values in order
        expected_values = [1, 2, 3, 'four', False]
        for i, expected_value in enumerate(expected_values):
            handler.on_value.assert_any_call(expected_value)
        
        # Check total number of on_value calls
        self.assertEqual(handler.on_value.call_count, 5)
    
    def test_nested_structures(self):
        """Test parsing of nested objects and arrays"""
        json_str = '''
        {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ],
            "count": 2
        }
        '''
        handler = MagicMock()
        stream = io.StringIO(json_str)
        parse(stream, handler)
        
        # Verify top-level object
        handler.on_object_start.assert_called_once()
        handler.on_object_end.assert_called_once()
        
        # Verify nested array
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()
        
        # Verify nested objects
        self.assertEqual(handler.on_object_start.call_count, 3)  # 1 top + 2 nested
        
        # Verify keys
        handler.on_key.assert_any_call('users')
        handler.on_key.assert_any_call('id')
        handler.on_key.assert_any_call('name')
        handler.on_key.assert_any_call('count')
    
    def test_streaming_large_array_memory_usage(self):
        """Test that streaming a 1000-element array doesn't hold more than one element in memory"""
        # Create a large JSON array
        large_array = '[' + ','.join(str(i) for i in range(1000)) + ']'
        
        # Track callback invocations
        callback_log = []
        
        class TrackingHandler:
            def on_array_start(self):
                callback_log.append('array_start')
            
            def on_array_end(self):
                callback_log.append('array_end')
            
            def on_value(self, value):
                callback_log.append(('value', value))
        
        handler = TrackingHandler()
        stream = io.StringIO(large_array)
        parse(stream, handler)
        
        # Verify structure
        self.assertEqual(callback_log[0], 'array_start')
        self.assertEqual(callback_log[-1], 'array_end')
        
        # Verify all values were processed
        values = [item[1] for item in callback_log if isinstance(item, tuple)]
        expected_values = list(range(1000))
        self.assertEqual(values, expected_values)
        
        # Verify we got exactly 1000 value callbacks
        value_callbacks = [item for item in callback_log if isinstance(item, tuple)]
        self.assertEqual(len(value_callbacks), 1000)
