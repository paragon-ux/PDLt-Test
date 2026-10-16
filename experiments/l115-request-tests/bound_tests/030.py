import io
import json
import sys
import unittest

class TestJSONSAXParser(unittest.TestCase):
    def test_simple_object(self):
        """Test parsing a simple object with various types."""
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
        json_str = '{"name": "John", "age": 30, "active": true, "address": null}'
        parser = JSONSAXParser(chunk_size=10)
        parser.parse(io.StringIO(json_str), handler)

        expected = [
            'object_start',
            ('key', 'name'),
            ('string', 'John'),
            ('key', 'age'),
            ('number', 30),
            ('key', 'active'),
            ('bool', True),
            ('key', 'address'),
            'null',
            'object_end'
        ]
        self.assertEqual(handler.events, expected)

    def test_escape_sequences(self):
        """Test string escape sequences: \\, \n, \t, \", \uXXXX."""
        class Handler:
            def __init__(self):
                self.strings = []
            def on_string(self, s): self.strings.append(s)
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_key(self, key): pass
            def on_value(self, value): pass

        handler = Handler()
        json_str = '{"text": "line1\\nline2\\ttab", "quote": "he said \\"hello\\"", "unicode": "\\u0041"}'
        parser = JSONSAXParser(chunk_size=15)
        parser.parse(io.StringIO(json_str), handler)

        self.assertEqual(len(handler.strings), 3)
        self.assertEqual(handler.strings[0], 'line1\nline2\ttab')
        self.assertEqual(handler.strings[1], 'he said "hello"')
        self.assertEqual(handler.strings[2], 'A')

    def test_nested_structures(self):
        """Test nested objects and arrays of arbitrary depth."""
        class Handler:
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
            def on_key(self, key): pass
            def on_value(self, value): pass
            def on_string(self, s): pass
            def on_number(self, n): pass
            def on_bool(self, b): pass
            def on_null(self): pass

        handler = Handler()
        # Create deeply nested structure: {"a": {"b": {"c": [1, 2, {"d": "e"}]}}}
        json_str = '{"a": {"b": {"c": [1, 2, {"d": "e"}]}}}'
        parser = JSONSAXParser(chunk_size=10)
        parser.parse(io.StringIO(json_str), handler)

        self.assertEqual(handler.max_depth, 4)
        self.assertEqual(handler.depth, 0)

    def test_large_array_streaming(self):
        """Test streaming a 1000-element array with proper callbacks."""
        class CountingHandler:
            def __init__(self):
                self.array_start_count = 0
                self.array_end_count = 0
                self.value_count = 0
                self.values = []
            def on_array_start(self): self.array_start_count += 1
            def on_array_end(self): self.array_end_count += 1
            def on_value(self, value): 
                self.value_count += 1
                self.values.append(value)
            def on_string(self, s): pass
            def on_number(self, n): pass
            def on_bool(self, b): pass
            def on_null(self): pass
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_key(self, key): pass

        handler = CountingHandler()
        json_array = generate_json_array(1000)
        parser = JSONSAXParser(chunk_size=50)
        parser.parse(io.StringIO(json_array), handler)

        self.assertEqual(handler.array_start_count, 1)
        self.assertEqual(handler.array_end_count, 1)
        self.assertEqual(handler.value_count, 1000)
        self.assertEqual(len(handler.values), 1000)
        # Verify all values are numbers 0-999
        self.assertEqual(handler.values, list(range(1000)))

    def test_generate_json_array(self):
        """Test generate_json_array produces valid JSON array of given size."""
        n = 5
        result = generate_json_array(n)
        # Verify it's valid JSON
        parsed = json.loads(result)
        self.assertIsInstance(parsed, list)
        self.assertEqual(len(parsed), n)
        # Verify it contains numbers 0 to n-1
        self.assertEqual(parsed, list(range(n)))

    def test_mixed_nested_structure(self):
        """Test complex nested structure with mixed types."""
        class Handler:
            def __init__(self):
                self.events = []
            def on_object_start(self): self.events.append('obj_start')
            def on_object_end(self): self.events.append('obj_end')
            def on_array_start(self): self.events.append('arr_start')
            def on_array_end(self): self.events.append('arr_end')
            def on_key(self, key): self.events.append(('key', key))
            def on_value(self, value): self.events.append(('val', value))
            def on_string(self, s): self.events.append(('str', s))
            def on_number(self, n): self.events.append(('num', n))
            def on_bool(self, b): self.events.append(('bool', b))
            def on_null(self): self.events.append('null')

        handler = Handler()
        json_str = '''
        {
            "users": [
                {"name": "Alice", "scores": [95, 88, 92]},
                {"name": "Bob", "active": false, "scores": null}
            ],
            "metadata": {
                "count": 2,
                "generated": true
            }
        }
        '''
        parser = JSONSAXParser(chunk_size=20)
        parser.parse(io.StringIO(json_str), handler)

        # Verify structure by checking key events
        keys = [event for event in handler.events if isinstance(event, tuple) and event[0] == 'key']
        key_names = [k[1] for k in keys]
        self.assertEqual(key_names, ['users', 'name', 'scores', 'name', 'active', 'scores', 'count', 'generated'])

    def test_chunk_boundaries(self):
        """Test that parsing works correctly across chunk boundaries."""
        class Handler:
            def __init__(self):
                self.strings = []
            def on_string(self, s): self.strings.append(s)
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_key(self, key): pass
            def on_value(self, value): pass

        handler = Handler()
        # Create a long string that will be split across chunks
        long_string = "a" * 100
        json_str = f'{{"data": "{long_string}"}}'
        # Use small chunk size to force multiple chunks
        parser = JSONSAXParser(chunk_size=10)
        parser.parse(io.StringIO(json_str), handler)

        self.assertEqual(len(handler.strings), 1)
        self.assertEqual(handler.strings[0], long_string)

def run_test():
    """Run all tests."""
    unittest.main(verbosity=2)

if __name__ == '__main__':
    run_test()
