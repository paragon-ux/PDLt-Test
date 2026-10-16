import io
import json
import struct
import unittest

class TestJSONSAXParser(unittest.TestCase):
    def test_simple_object_parsing(self):
        """Test parsing a simple object with string and number values."""
        recorder = CallbackRecorder()
        json_data = '{"name": "John", "age": 30}'
        parser = JSONSAXParser(chunk_size=10)
        parser.parse(io.StringIO(json_data), recorder)
        
        expected = [
            ('on_object_start', ()),
            ('on_key', ('name',)),
            ('on_string', ('John',)),
            ('on_key', ('age',)),
            ('on_number', (30,)),
            ('on_object_end', ())
        ]
        self.assertEqual(recorder.events, expected)

    def test_simple_array_parsing(self):
        """Test parsing a simple array with mixed value types."""
        recorder = CallbackRecorder()
        json_data = '[1, "hello", true, null]'
        parser = JSONSAXParser(chunk_size=5)
        parser.parse(io.StringIO(json_data), recorder)
        
        expected = [
            ('on_array_start', ()),
            ('on_number', (1,)),
            ('on_string', ('hello',)),
            ('on_bool', (True,)),
            ('on_null', ()),
            ('on_array_end', ())
        ]
        self.assertEqual(recorder.events, expected)

    def test_escape_sequences(self):
        """Test handling of string escape sequences."""
        recorder = CallbackRecorder()
        json_data = '{"text": "line1\\nline2\\ttab", "quote": "say \\"hello\\""}'
        parser = JSONSAXParser(chunk_size=8)
        parser.parse(io.StringIO(json_data), recorder)
        
        # Find the string callbacks
        string_events = [event for event in recorder.events if event[0] == 'on_string']
        self.assertEqual(len(string_events), 2)
        self.assertEqual(string_events[0][1][0], 'line1\nline2\ttab')
        self.assertEqual(string_events[1][1][0], 'say "hello"')

    def test_unicode_escape(self):
        """Test handling of unicode escape sequences."""
        recorder = CallbackRecorder()
        json_data = '{"greeting": "hello\\u0020world"}'  # \u0020 is space
        parser = JSONSAXParser(chunk_size=6)
        parser.parse(io.StringIO(json_data), recorder)
        
        string_events = [event for event in recorder.events if event[0] == 'on_string']
        self.assertEqual(len(string_events), 1)
        self.assertEqual(string_events[0][1][0], 'hello world')

    def test_nested_structures(self):
        """Test parsing of deeply nested objects and arrays."""
        recorder = CallbackRecorder()
        json_data = '{"outer": [{"inner": [1, 2, {"deep": true}]}]}'
        parser = JSONSAXParser(chunk_size=4)
        parser.parse(io.StringIO(json_data), recorder)
        
        # Verify structure by checking key events and depth indicators
        key_events = [event for event in recorder.events if event[0] == 'on_key']
        self.assertEqual(len(key_events), 3)
        self.assertEqual([e[1][0] for e in key_events], ['outer', 'inner', 'deep'])
        
        # Verify boolean value at deepest level
        bool_events = [event for event in recorder.events if event[0] == 'on_bool']
        self.assertEqual(len(bool_events), 1)
        self.assertEqual(bool_events[0][1][0], True)

    def test_large_array_streaming(self):
        """Test streaming a 1000-element array without building complete tree."""
        recorder = CallbackRecorder()
        # Create a JSON array with 1000 numbers
        large_array = '[' + ','.join(str(i) for i in range(1000)) + ']'
        parser = JSONSAXParser(chunk_size=16)
        parser.parse(io.StringIO(large_array), recorder)
        
        # Verify array structure
        array_start_events = [e for e in recorder.events if e[0] == 'on_array_start']
        array_end_events = [e for e in recorder.events if e[0] == 'on_array_end']
        self.assertEqual(len(array_start_events), 1)
        self.assertEqual(len(array_end_events), 1)
        
        # Verify all 1000 numbers are parsed
        number_events = [e for e in recorder.events if e[0] == 'on_number']
        self.assertEqual(len(number_events), 1000)
        
        # Verify numbers are in order
        for i, event in enumerate(number_events):
            self.assertEqual(event[1][0], i)

    def test_empty_structures(self):
        """Test parsing empty objects and arrays."""
        recorder = CallbackRecorder()
        json_data = '{"empty_obj": {}, "empty_arr": []}'
        parser = JSONSAXParser(chunk_size=12)
        parser.parse(io.StringIO(json_data), recorder)
        
        expected = [
            ('on_object_start', ()),
            ('on_key', ('empty_obj',)),
            ('on_object_start', ()),
            ('on_object_end', ()),
            ('on_key', ('empty_arr',)),
            ('on_array_start', ()),
            ('on_array_end', ()),
            ('on_object_end', ())
        ]
        self.assertEqual(recorder.events, expected)

    def test_number_parsing(self):
        """Test parsing of various number formats."""
        recorder = CallbackRecorder()
        json_data = '{"int": 42, "float": 3.14, "negative": -17, "exponent": 1e10}'
        parser = JSONSAXParser(chunk_size=9)
        parser.parse(io.StringIO(json_data), recorder)
        
        number_events = [e for e in recorder.events if e[0] == 'on_number']
        self.assertEqual(len(number_events), 4)
        self.assertEqual(number_events[0][1][0], 42)
        self.assertEqual(number_events[1][1][0], 3.14)
        self.assertEqual(number_events[2][1][0], -17)
        self.assertEqual(number_events[3][1][0], 1e10)

    def test_boolean_and_null(self):
        """Test parsing of boolean and null values."""
        recorder = CallbackRecorder()
        json_data = '{"true_val": true, "false_val": false, "null_val": null}'
        parser = JSONSAXParser(chunk_size=11)
        parser.parse(io.StringIO(json_data), recorder)
        
        bool_events = [e for e in recorder.events if e[0] == 'on_bool']
        null_events = [e for e in recorder.events if e[0] == 'on_null']
        
        self.assertEqual(len(bool_events), 2)
        self.assertEqual(bool_events[0][1][0], True)
        self.assertEqual(bool_events[1][1][0], False)
        self.assertEqual(len(null_events), 1)

    def test_chunked_parsing_consistency(self):
        """Test that results are consistent regardless of chunk size."""
        json_data = '{"a": 1, "b": [2, 3, 4], "c": "test"}'
        
        # Test with different chunk sizes
        for chunk_size in [1, 2, 5, 10, 100]:
            with self.subTest(chunk_size=chunk_size):
                recorder = CallbackRecorder()
                parser = JSONSAXParser(chunk_size=chunk_size)
                parser.parse(io.StringIO(json_data), recorder)
                
                # Verify we get the same structure regardless of chunking
                key_events = [e for e in recorder.events if e[0] == 'on_key']
                self.assertEqual([e[1][0] for e in key_events], ['a', 'b', 'c'])

if __name__ == '__main__':
    unittest.main()
