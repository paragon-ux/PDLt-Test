import io
import unittest

class TestJSONParser(unittest.TestCase):
    def test_basic_types(self):
        handler = MockHandler()
        parser = JSONParser(io.StringIO('true'), handler, 1024)
        parser.parse()
        self.assertEqual(handler.calls, [('on_bool', True)])

        handler = MockHandler()
        parser = JSONParser(io.StringIO('false'), handler, 1024)
        parser.parse()
        self.assertEqual(handler.calls, [('on_bool', False)])

        handler = MockHandler()
        parser = JSONParser(io.StringIO('null'), handler, 1024)
        parser.parse()
        self.assertEqual(handler.calls, [('on_null',)])

        handler = MockHandler()
        parser = JSONParser(io.StringIO('123'), handler, 1024)
        parser.parse()
        self.assertEqual(handler.calls, [('on_number', 123)])

        handler = MockHandler()
        parser = JSONParser(io.StringIO('"hello"'), handler, 1024)
        parser.parse()
        self.assertEqual(handler.calls, [('on_string', 'hello')])

    def test_string_escapes(self):
        handler = MockHandler()
        parser = JSONParser(io.StringIO('"\\n\\t\\\\"'), handler, 1024)
        parser.parse()
        self.assertEqual(handler.calls, [('on_string', '\n\t\\')])

        handler = MockHandler()
        parser = JSONParser(io.StringIO('"\\u0041"'), handler, 1024)
        parser.parse()
        self.assertEqual(handler.calls, [('on_string', 'A')])

    def test_object_parsing(self):
        handler = MockHandler()
        parser = JSONParser(io.StringIO('{"key": "value"}'), handler, 1024)
        parser.parse()
        expected = [
            ('on_object_start',),
            ('on_key', 'key'),
            ('on_value', 'value'),
            ('on_object_end',)
        ]
        self.assertEqual(handler.calls, expected)

    def test_array_parsing(self):
        handler = MockHandler()
        parser = JSONParser(io.StringIO('[1, 2, 3]'), handler, 1024)
        parser.parse()
        expected = [
            ('on_array_start',),
            ('on_value', 1),
            ('on_value', 2),
            ('on_value', 3),
            ('on_array_end',)
        ]
        self.assertEqual(handler.calls, expected)

    def test_nested_structures(self):
        handler = MockHandler()
        parser = JSONParser(io.StringIO('{"a": [1, {"b": 2}]}'), handler, 1024)
        parser.parse()
        expected = [
            ('on_object_start',),
            ('on_key', 'a'),
            ('on_array_start',),
            ('on_value', 1),
            ('on_object_start',),
            ('on_key', 'b'),
            ('on_value', 2),
            ('on_object_end',),
            ('on_array_end',),
            ('on_object_end',)
        ]
        self.assertEqual(handler.calls, expected)

    def test_streaming_1000_element_array(self):
        # Create a stream that yields the array in chunks
        class ChunkedStream:
            def __init__(self, data, chunk_size):
                self.data = data
                self.chunk_size = chunk_size
                self.pos = 0

            def read(self, size=-1):
                if self.pos >= len(self.data):
                    return ''
                end = self.pos + self.chunk_size
                chunk = self.data[self.pos:end]
                self.pos = end
                return chunk

        # Generate a 1000-element array
        array_data = '[' + ','.join(str(i) for i in range(1000)) + ']'
        stream = ChunkedStream(array_data, 128)  # Small chunk size to force multiple reads

        handler = MockHandler()
        parser = JSONParser(stream, handler, 128)
        parser.parse()

        # Verify all callbacks fired correctly
        self.assertEqual(len(handler.calls), 1002)  # array_start + 1000 values + array_end
        self.assertEqual(handler.calls[0], ('on_array_start',))
        self.assertEqual(handler.calls[-1], ('on_array_end',))
        for i in range(1000):
            self.assertEqual(handler.calls[i+1], ('on_value', i))

if __name__ == '__main__':
    unittest.main()
