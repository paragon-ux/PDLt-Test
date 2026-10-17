import io
import json
import unittest

class TestStreamingJSONParser(unittest.TestCase):
    def test_string_parsing(self):
        """Test basic string parsing with escape sequences"""
        handler = RecordingHandler()
        parse(io.StringIO('"hello world"'), handler, 100,
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        self.assertEqual(handler.string_calls, ["hello world"])

    def test_escape_sequences(self):
        """Test string escape sequences: \\, \n, \t, \", \uXXXX"""
        test_string = 'line1\nline2\ttab\\"quote\\u0041'
        handler = RecordingHandler()
        parse(io.StringIO(json.dumps(test_string)), handler, 100,
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        self.assertEqual(handler.string_calls, [test_string])

    def test_number_parsing(self):
        """Test integer and float parsing"""
        handler = RecordingHandler()
        parse(io.StringIO('42'), handler, 100,
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        self.assertEqual(handler.number_calls, [42])
        
        handler = RecordingHandler()
        parse(io.StringIO('3.14'), handler, 100,
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        self.assertEqual(handler.number_calls, [3.14])

    def test_boolean_parsing(self):
        """Test true/false parsing"""
        for value in [True, False]:
            handler = RecordingHandler()
            parse(io.StringIO(json.dumps(value)), handler, 100,
                  on_object_start=handler.on_object_start,
                  on_object_end=handler.on_object_end,
                  on_array_start=handler.on_array_start,
                  on_array_end=handler.on_array_end,
                  on_key=handler.on_key,
                  on_value=handler.on_value,
                  on_string=handler.on_string,
                  on_number=handler.on_number,
                  on_bool=handler.on_bool,
                  on_null=handler.on_null)
            self.assertEqual(handler.bool_calls, [value])

    def test_null_parsing(self):
        """Test null parsing"""
        handler = RecordingHandler()
        parse(io.StringIO('null'), handler, 100,
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        self.assertEqual(handler.null_calls, [None])

    def test_object_parsing(self):
        """Test object with key-value pairs"""
        test_obj = {"key1": "value1", "key2": 123}
        handler = RecordingHandler()
        parse(io.StringIO(json.dumps(test_obj)), handler, 100,
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        self.assertEqual(handler.object_start_calls, 1)
        self.assertEqual(handler.object_end_calls, 1)
        self.assertEqual(handler.key_calls, ["key1", "key2"])
        self.assertEqual(handler.string_calls, ["value1"])
        self.assertEqual(handler.number_calls, [123])

    def test_array_parsing(self):
        """Test array with mixed types"""
        test_array = [1, "two", False, None]
        handler = RecordingHandler()
        parse(io.StringIO(json.dumps(test_array)), handler, 100,
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        self.assertEqual(handler.array_start_calls, 1)
        self.assertEqual(handler.array_end_calls, 1)
        self.assertEqual(handler.number_calls, [1])
        self.assertEqual(handler.string_calls, ["two"])
        self.assertEqual(handler.bool_calls, [False])
        self.assertEqual(handler.null_calls, [None])

    def test_nested_structures(self):
        """Test deeply nested objects and arrays"""
        nested = {
            "array": [{"nested": [1, 2, 3]}, {"value": True}],
            "deep": {"deeper": {"deepest": "end"}}
        }
        handler = RecordingHandler()
        parse(io.StringIO(json.dumps(nested)), handler, 100,
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        # Verify structural callbacks
        self.assertGreater(handler.object_start_calls, 1)
        self.assertGreater(handler.array_start_calls, 1)
        self.assertEqual(handler.object_end_calls, handler.object_start_calls)
        self.assertEqual(handler.array_end_calls, handler.array_start_calls)

    def test_large_array_streaming(self):
        """Test streaming 1000-element array without holding full structure in memory"""
        large_array = list(range(1000))
        handler = RecordingHandler()
        stream = io.StringIO(json.dumps(large_array))
        parse(stream, handler, 10,  # Small chunk size to force multiple reads
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        
        self.assertEqual(handler.array_start_calls, 1)
        self.assertEqual(handler.array_end_calls, 1)
        self.assertEqual(len(handler.number_calls), 1000)
        self.assertEqual(handler.number_calls, large_array)
        # Verify no object callbacks were made (pure array)
        self.assertEqual(handler.object_start_calls, 0)
        self.assertEqual(handler.object_end_calls, 0)

    def test_chunked_reading(self):
        """Test that parsing works with very small chunk sizes"""
        test_data = '{"key": "value", "array": [1, 2, 3]}'
        handler = RecordingHandler()
        parse(io.StringIO(test_data), handler, 2,  # Read 2 chars at a time
              on_object_start=handler.on_object_start,
              on_object_end=handler.on_object_end,
              on_array_start=handler.on_array_start,
              on_array_end=handler.on_array_end,
              on_key=handler.on_key,
              on_value=handler.on_value,
              on_string=handler.on_string,
              on_number=handler.on_number,
              on_bool=handler.on_bool,
              on_null=handler.on_null)
        self.assertEqual(handler.key_calls, ["key"])
        self.assertEqual(handler.string_calls, ["value"])
        self.assertEqual(handler.number_calls, [1, 2, 3])
