import io
import json
import unittest

class TestStreamingJSONParser(unittest.TestCase):
    
    def test_string_escapes(self):
        """Test that string escape sequences are handled correctly."""
        class RecordingHandler:
            def __init__(self):
                self.strings = []
            def on_string(self, s):
                self.strings.append(s)
            # Other required methods with empty implementations
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_key(self, k): pass
            def on_number(self, n): pass
            def on_bool(self, b): pass
            def on_null(self): pass
            def on_value(self, v): pass
        
        json_string = '"\\\\\\n\\t\\\\"\\"u0041"'
        expected = '\\\n\t\"A'
        
        stream = io.StringIO(json_string)
        handler = RecordingHandler()
        parse(stream, handler, 1024, 'utf-8')
        
        self.assertEqual(handler.strings[0], expected, 
                        "String escape sequences should be unescaped correctly")

    def test_nested_structures(self):
        """Test that nested objects and arrays trigger correct callbacks."""
        class RecordingHandler:
            def __init__(self):
                self.events = []
            def on_object_start(self): self.events.append('object_start')
            def on_object_end(self): self.events.append('object_end')
            def on_array_start(self): self.events.append('array_start')
            def on_array_end(self): self.events.append('array_end')
            def on_key(self, k): self.events.append(f'key:{k}')
            def on_string(self, s): self.events.append(f'string:{s}')
            def on_number(self, n): self.events.append(f'number:{n}')
            def on_bool(self, b): self.events.append(f'bool:{b}')
            def on_null(self): self.events.append('null')
            def on_value(self, v): pass
        
        json_string = '{"key1": [1, 2, {"inner": "value"}]}'
        expected_events = [
            'object_start', 'key:key1', 'array_start',
            'number:1', 'number:2', 'object_start',
            'key:inner', 'string:value', 'object_end',
            'array_end', 'object_end'
        ]
        
        stream = io.StringIO(json_string)
        handler = RecordingHandler()
        parse(stream, handler, 1024, 'utf-8')
        
        self.assertEqual(handler.events, expected_events,
                        "Nested structures should trigger callbacks in correct order")

    def test_streaming_array_1000(self):
        """Test streaming a 1000-element array with correct callbacks."""
        class CountingHandler:
            def __init__(self):
                self.count = 0
                self.values = []
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_value(self, v):
                self.count += 1
                self.values.append(v)
            # Other required methods
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_key(self, k): pass
            def on_string(self, s): pass
            def on_number(self, n): pass
            def on_bool(self, b): pass
            def on_null(self): pass
        
        # Create a JSON array with 1000 elements
        json_array = json.dumps(list(range(1000)))
        
        stream = io.StringIO(json_array)
        handler = CountingHandler()
        parse(stream, handler, 1024, 'utf-8')
        
        self.assertEqual(handler.count, 1000,
                        "All 1000 elements should trigger on_value callback")
        self.assertEqual(handler.values, list(range(1000)),
                        "Values should be parsed correctly in order")

    def test_boolean_and_null(self):
        """Test that boolean and null values trigger correct callbacks."""
        class RecordingHandler:
            def __init__(self):
                self.bools = []
                self.nulls = []
            def on_bool(self, b): self.bools.append(b)
            def on_null(self): self.nulls.append(True)
            # Other required methods
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_key(self, k): pass
            def on_string(self, s): pass
            def on_number(self, n): pass
            def on_value(self, v): pass
        
        json_string = '[true, false, null]'
        stream = io.StringIO(json_string)
        handler = RecordingHandler()
        parse(stream, handler, 1024, 'utf-8')
        
        self.assertEqual(handler.bools, [True, False],
                        "Boolean values should trigger on_bool callback")
        self.assertEqual(len(handler.nulls), 1,
                        "Null value should trigger on_null callback")

    def test_number_parsing(self):
        """Test that numbers are parsed correctly."""
        class RecordingHandler:
            def __init__(self):
                self.numbers = []
            def on_number(self, n): self.numbers.append(n)
            # Other required methods
            def on_object_start(self): pass
            def on_object_end(self): pass
            def on_array_start(self): pass
            def on_array_end(self): pass
            def on_key(self, k): pass
            def on_string(self, s): pass
            def on_bool(self, b): pass
            def on_null(self): pass
            def on_value(self, v): pass
        
        json_string = '[1, 2.5, -3, 1e10]'
        expected = [1, 2.5, -3, 1e10]
        
        stream = io.StringIO(json_string)
        handler = RecordingHandler()
        parse(stream, handler, 1024, 'utf-8')
        
        self.assertEqual(handler.numbers, expected,
                        "Numbers should be parsed correctly")

if __name__ == '__main__':
    unittest.main()
