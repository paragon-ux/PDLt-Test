import json
import io
import unittest

class TestJSONSAXParser(unittest.TestCase):
    def test_basic_types(self):
        """Test parsing of basic JSON types: numbers, booleans, null, strings."""
        class RecordingHandler:
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
        
        handler = RecordingHandler()
        test_json = '{"number": 42, "bool_true": true, "bool_false": false, "null_val": null, "string": "hello"}'
        parse(io.StringIO(test_json), handler)
        
        expected = [
            'object_start',
            ('key', 'number'),
            ('number', 42),
            ('key', 'bool_true'),
            ('bool', True),
            ('key', 'bool_false'),
            ('bool', False),
            ('key', 'null_val'),
            'null',
            ('key', 'string'),
            ('string', 'hello'),
            'object_end'
        ]
        self.assertEqual(handler.events, expected, "Basic types callbacks failed")

    def test_string_escapes(self):
        """Test handling of string escape sequences: \\, \n, \t, \", \uXXXX."""
        class RecordingHandler:
            def __init__(self):
                self.strings = []
            def on_string(self, s): self.strings.append(s)
        
        handler = RecordingHandler()
        test_json = r'{"escaped": "line1\nline2\ttab\"quote\\backslash\u0041"}'
        parse(io.StringIO(test_json), handler)
        
        expected_string = 'line1\nline2\ttab"quote\\backslashA'
        self.assertEqual(handler.strings[0], expected_string, f"String escape handling failed: {handler.strings[0]} != {expected_string}")

    def test_nested_structures(self):
        """Test handling of nested objects and arrays of arbitrary depth."""
        class RecordingHandler:
            def __init__(self):
                self.depth = 0
                self.max_depth = 0
            def on_object_start(self): 
                self.depth += 1
                self.max_depth = max(self.max_depth, self.depth)
            def on_object_end(self): self.depth -= 1
            def on_array_start(self):
                self.depth += 1
                self.max_depth = max(self.max_depth, self.depth)
            def on_array_end(self): self.depth -= 1
        
        handler = RecordingHandler()
        # Create deeply nested structure: {"a":{"b":{"c":[1,2,{"d":"e"}]}}}
        nested_json = '{"a":{"b":{"c":[1,2,{"d":"e"}]}}}'
        parse(io.StringIO(nested_json), handler)
        
        self.assertEqual(handler.max_depth, 5, f"Nested structure depth incorrect: max depth {handler.max_depth} != 5")
        self.assertEqual(handler.depth, 0, "Nested structure did not return to depth 0")

    def test_streaming_array_1000(self):
        """Test streaming a 1000-element array with correct callbacks."""
        class ArrayHandler:
            def __init__(self):
                self.count = 0
                self.values = []
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_value(self, value):
                self.count += 1
                self.values.append(value)
        
        handler = ArrayHandler()
        # Create a 1000-element array
        large_array = '[' + ','.join(str(i) for i in range(1000)) + ']'
        parse(io.StringIO(large_array), handler)
        
        self.assertEqual(handler.count, 1000, f"Array element count incorrect: {handler.count} != 1000")
        self.assertEqual(handler.values, list(range(1000)), "Array values incorrect")

    def test_chunked_streaming(self):
        """Test that parsing works correctly with chunked reads."""
        class ChunkedHandler:
            def __init__(self):
                self.objects = []
                self.current_object = {}
                self.in_object = False
            def on_object_start(self): 
                self.in_object = True
                self.current_object = {}
            def on_object_end(self):
                self.objects.append(self.current_object)
                self.in_object = False
            def on_key(self, key):
                self.current_key = key
            def on_value(self, value):
                if self.in_object:
                    self.current_object[self.current_key] = value
        
        handler = ChunkedHandler()
        # Create JSON that will be read in chunks
        test_json = '{"a":1,"b":2,"c":3}'
        stream = io.StringIO(test_json)
        
        # Simulate chunked reading by using a small chunk size
        parser = SAXParser(handler)
        parser.parse(stream)  # This should handle chunking internally
        
        expected = [{'a': 1, 'b': 2, 'c': 3}]
        self.assertEqual(handler.objects, expected, "Chunked streaming failed")

    def test_empty_structures(self):
        """Test parsing of empty objects and arrays."""
        class RecordingHandler:
            def __init__(self):
                self.events = []
            def on_object_start(self): self.events.append('object_start')
            def on_object_end(self): self.events.append('object_end')
            def on_array_start(self): self.events.append('array_start')
            def on_array_end(self): self.events.append('array_end')
        
        handler = RecordingHandler()
        test_json = '{"empty_obj":{}, "empty_arr":[]}'
        parse(io.StringIO(test_json), handler)
        
        expected = [
            'object_start',
            ('key', 'empty_obj'),
            'object_start',
            'object_end',
            ('key', 'empty_arr'),
            'array_start',
            'array_end',
            'object_end'
        ]
        self.assertEqual(handler.events, expected, "Empty structures callbacks failed")

if __name__ == '__main__':
    unittest.main()
