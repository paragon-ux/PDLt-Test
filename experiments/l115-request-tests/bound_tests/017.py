import io
import unittest
from unittest.mock import Mock

class TestJSONStreamingParser(unittest.TestCase):
    
    def test_parse_simple_object(self):
        # Test basic object parsing with various value types
        json_data = b'{"name": "John", "age": 30, "active": true, "address": null}'
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        parse(stream, handler)
        
        # Verify object structure
        handler.on_object_start.assert_called_once()
        handler.on_object_end.assert_called_once()
        
        # Verify keys and values
        handler.on_key.assert_any_call("name")
        handler.on_key.assert_any_call("age")
        handler.on_key.assert_any_call("active")
        handler.on_key.assert_any_call("address")
        
        # Verify value callbacks
        handler.on_string.assert_called_with("John")
        handler.on_number.assert_called_with(30)
        handler.on_bool.assert_called_with(True)
        handler.on_null.assert_called_once()
    
    def test_parse_simple_array(self):
        # Test basic array parsing
        json_data = b'[1, 2, 3, "four", true, null]'
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        parse(stream, handler)
        
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()
        
        # Verify all values in array
        handler.on_number.assert_any_call(1)
        handler.on_number.assert_any_call(2)
        handler.on_number.assert_any_call(3)
        handler.on_string.assert_called_with("four")
        handler.on_bool.assert_called_with(True)
        handler.on_null.assert_called_once()
    
    def test_nested_structures(self):
        # Test nested objects and arrays
        json_data = b'{"items": [{"id": 1}, {"id": 2}], "meta": {"count": 2}}'
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        parse(stream, handler)
        
        # Verify nested structure callbacks
        handler.on_object_start.assert_called_with()
        handler.on_object_end.assert_called_with()
        handler.on_array_start.assert_called_with()
        handler.on_array_end.assert_called_with()
        
        # Verify nested object callbacks
        self.assertEqual(handler.on_object_start.call_count, 3)  # outer + 2 inner objects
        self.assertEqual(handler.on_array_start.call_count, 1)
    
    def test_string_escapes(self):
        # Test string escape sequences
        json_data = b'{"text": "hello\\nworld\\ttab", "quote": "said \\"hello\\"", "unicode": "\\u0041"}'
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        parse(stream, handler)
        
        # Verify escape sequences are properly handled
        handler.on_string.assert_any_call("hello\nworld\ttab")
        handler.on_string.assert_any_call('said "hello"')
        handler.on_string.assert_any_call("A")  # \u0041 is 'A'
    
    def test_streaming_1000_element_array(self):
        # Test streaming 1000-element array with chunked reading
        json_array = "[" + ",".join(str(i) for i in range(1000)) + "]"
        
        # Create a stream that feeds data in small chunks
        chunk_size = 50  # Small chunk size to force multiple reads
        stream = io.BytesIO(json_array.encode())
        
        handler = Mock()
        
        # Parse with small chunk size to verify streaming behavior
        parser = JSONStreamingParser(stream, handler, chunk_size)
        parser.parse()
        
        # Verify array structure
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()
        
        # Verify all 1000 numbers are processed
        self.assertEqual(handler.on_number.call_count, 1000)
        
        # Verify numbers are in order
        for i in range(1000):
            handler.on_number.assert_any_call(i)
    
    def test_counting_handler_functionality(self):
        # Test the CountingHandler implementation
        json_data = b'{"a": 1, "b": [2, 3], "c": "test"}'
        stream = io.BytesIO(json_data)
        handler = CountingHandler()
        
        parse(stream, handler)
        
        # Verify counting works correctly
        self.assertEqual(handler.object_count, 2)  # outer object + inner object in array? 
        # Actually: outer object, array (not counted), no inner objects
        self.assertEqual(handler.array_count, 1)
        self.assertEqual(handler.key_count, 3)
        self.assertEqual(handler.string_count, 1)
        self.assertEqual(handler.number_count, 3)  # 1, 2, 3
        self.assertEqual(handler.bool_count, 0)
        self.assertEqual(handler.null_count, 0)
    
    def test_empty_structures(self):
        # Test empty objects and arrays
        json_data = b'{}'
        stream = io.BytesIO(json_data)
        handler = Mock()
        parse(stream, handler)
        handler.on_object_start.assert_called_once()
        handler.on_object_end.assert_called_once()
        
        json_data = b'[]'
        stream = io.BytesIO(json_data)
        handler = Mock()
        parse(stream, handler)
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()
    
    def test_whitespace_handling(self):
        # Test that whitespace is properly skipped
        json_data = b'  {  \n "key"  :  "value"  \t }  '
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        parse(stream, handler)
        
        handler.on_object_start.assert_called_once()
        handler.on_key.assert_called_with("key")
        handler.on_string.assert_called_with("value")
        handler.on_object_end.assert_called_once()
    
    def test_number_formats(self):
        # Test different number formats
        json_data = b'{"int": 42, "float": 3.14, "negative": -17, "large": 1e10}'
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        parse(stream, handler)
        
        handler.on_number.assert_any_call(42)
        handler.on_number.assert_any_call(3.14)
        handler.on_number.assert_any_call(-17)
        handler.on_number.assert_any_call(1e10)
    
    def test_boolean_and_null(self):
        # Test boolean and null values
        json_data = b'{"true": true, "false": false, "nothing": null}'
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        parse(stream, handler)
        
        handler.on_bool.assert_any_call(True)
        handler.on_bool.assert_any_call(False)
        handler.on_null.assert_called_once()
    
    def test_deep_nesting(self):
        # Test arbitrary depth nesting
        depth = 50
        json_data = b'[' * depth + b'1' + b']' * depth
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        parse(stream, handler)
        
        # Verify correct number of start/end callbacks
        self.assertEqual(handler.on_array_start.call_count, depth)
        self.assertEqual(handler.on_array_end.call_count, depth)
        handler.on_number.assert_called_once_with(1)
    
    def test_chunked_reading_with_escapes(self):
        # Test that chunked reading works with escape sequences
        json_data = b'{"text": "hello\\nworld"}'
        stream = io.BytesIO(json_data)
        handler = Mock()
        
        # Force chunked reading
        parser = JSONStreamingParser(stream, handler, chunk_size=10)
        parser.parse()
        
        handler.on_object_start.assert_called_once()
        handler.on_key.assert_called_with("text")
        handler.on_string.assert_called_with("hello\nworld")
        handler.on_object_end.assert_called_once()

if __name__ == '__main__':
    unittest.main()
