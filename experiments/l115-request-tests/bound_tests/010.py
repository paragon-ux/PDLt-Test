import io
import json
import unittest

class TestJSONSAXParser(unittest.TestCase):
    def test_simple_object(self):
        handler = RecordingHandler()
        parser = JSONSAXParser(handler, chunk_size=1024)
        json_str = '{"name": "John", "age": 30, "is_student": false, "courses": ["Math", "Science"]}'
        stream = io.StringIO(json_str)
        parser.parse(stream)
        
        events = handler.events
        self.assertEqual(events[0], ('on_object_start', ()))
        self.assertEqual(events[1], ('on_key', ('name',)))
        self.assertEqual(events[2], ('on_value', ('John',)))
        self.assertEqual(events[3], ('on_key', ('age',)))
        self.assertEqual(events[4], ('on_value', (30,)))
        self.assertEqual(events[5], ('on_key', ('is_student',)))
        self.assertEqual(events[6], ('on_value', (False,)))
        self.assertEqual(events[7], ('on_key', ('courses',)))
        self.assertEqual(events[8], ('on_array_start', ()))
        self.assertEqual(events[9], ('on_value', ('Math',)))
        self.assertEqual(events[10], ('on_value', ('Science',)))
        self.assertEqual(events[11], ('on_array_end', ()))
        self.assertEqual(events[12], ('on_object_end', ()))

    def test_nested_structures(self):
        handler = RecordingHandler()
        parser = JSONSAXParser(handler, chunk_size=1024)
        json_str = '{"person": {"name": "Alice", "hobbies": ["reading", "hiking"]}, "active": true}'
        stream = io.StringIO(json_str)
        parser.parse(stream)
        
        events = handler.events
        self.assertEqual(events[0], ('on_object_start', ()))
        self.assertEqual(events[1], ('on_key', ('person',)))
        self.assertEqual(events[2], ('on_object_start', ()))
        self.assertEqual(events[3], ('on_key', ('name',)))
        self.assertEqual(events[4], ('on_value', ('Alice',)))
        self.assertEqual(events[5], ('on_key', ('hobbies',)))
        self.assertEqual(events[6], ('on_array_start', ()))
        self.assertEqual(events[7], ('on_value', ('reading',)))
        self.assertEqual(events[8], ('on_value', ('hiking',)))
        self.assertEqual(events[9], ('on_array_end', ()))
        self.assertEqual(events[10], ('on_object_end', ()))
        self.assertEqual(events[11], ('on_key', ('active',)))
        self.assertEqual(events[12], ('on_value', (True,)))
        self.assertEqual(events[13], ('on_object_end', ()))

    def test_string_escapes(self):
        handler = RecordingHandler()
        parser = JSONSAXParser(handler, chunk_size=1024)
        json_str = '{"text": "Hello\\nWorld\\t\\"Quote\\u0041"}'
        stream = io.StringIO(json_str)
        parser.parse(stream)
        
        events = handler.events
        self.assertEqual(events[0], ('on_object_start', ()))
        self.assertEqual(events[1], ('on_key', ('text',)))
        self.assertEqual(events[2], ('on_value', ('Hello\nWorld\t"QuoteA',)))
        self.assertEqual(events[3], ('on_object_end', ()))

    def test_null_and_numbers(self):
        handler = RecordingHandler()
        parser = JSONSAXParser(handler, chunk_size=1024)
        json_str = '{"value": null, "pi": 3.14159, "count": 42}'
        stream = io.StringIO(json_str)
        parser.parse(stream)
        
        events = handler.events
        self.assertEqual(events[0], ('on_object_start', ()))
        self.assertEqual(events[1], ('on_key', ('value',)))
        self.assertEqual(events[2], ('on_value', (None,)))
        self.assertEqual(events[3], ('on_key', ('pi',)))
        self.assertEqual(events[4], ('on_value', (3.14159,)))
        self.assertEqual(events[5], ('on_key', ('count',)))
        self.assertEqual(events[6], ('on_value', (42,)))
        self.assertEqual(events[7], ('on_object_end', ()))

    def test_large_array_streaming(self):
        num_elements = 1000
        handler = RecordingHandler()
        parser = JSONSAXParser(handler, chunk_size=1024)
        
        # Create a JSON array string with 1000 numbers
        json_array = '[' + ','.join(str(i) for i in range(num_elements)) + ']'
        stream = io.StringIO(json_array)
        parser.parse(stream)
        
        events = handler.events
        # Should have: array_start, 1000 value callbacks, array_end
        self.assertEqual(len(events), num_elements + 2)
        self.assertEqual(events[0], ('on_array_start', ()))
        for i in range(num_elements):
            self.assertEqual(events[i+1], ('on_value', (i,)))
        self.assertEqual(events[-1], ('on_array_end', ()))

    def test_empty_structures(self):
        handler = RecordingHandler()
        parser = JSONSAXParser(handler, chunk_size=1024)
        json_str = '{"empty_obj": {}, "empty_arr": []}'
        stream = io.StringIO(json_str)
        parser.parse(stream)
        
        events = handler.events
        self.assertEqual(events[0], ('on_object_start', ()))
        self.assertEqual(events[1], ('on_key', ('empty_obj',)))
        self.assertEqual(events[2], ('on_object_start', ()))
        self.assertEqual(events[3], ('on_object_end', ()))
        self.assertEqual(events[4], ('on_key', ('empty_arr',)))
        self.assertEqual(events[5], ('on_array_start', ()))
        self.assertEqual(events[6], ('on_array_end', ()))
        self.assertEqual(events[7], ('on_object_end', ()))

if __name__ == '__main__':
    unittest.main()
