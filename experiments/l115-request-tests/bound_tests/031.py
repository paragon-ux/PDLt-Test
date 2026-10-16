import io
import unittest

class RecordingHandler:
    def __init__(self):
        self.events = []
    
    def on_object_start(self):
        self.events.append('object_start')
    
    def on_object_end(self):
        self.events.append('object_end')
    
    def on_array_start(self):
        self.events.append('array_start')
    
    def on_array_end(self):
        self.events.append('array_end')
    
    def on_key(self, key):
        self.events.append(('key', key))
    
    def on_value(self, value):
        self.events.append(('value', value))
    
    def on_string(self, s):
        self.events.append(('string', s))
    
    def on_number(self, n):
        self.events.append(('number', n))
    
    def on_bool(self, b):
        self.events.append(('bool', b))
    
    def on_null(self):
        self.events.append('null')

class TestJSONParser(unittest.TestCase):
    def test_basic_types(self):
        handler = RecordingHandler()
        stream = io.StringIO('true')
        parse(stream, handler)
        self.assertEqual(handler.events, [('bool', True)], "Failed to parse boolean true")
        
        handler = RecordingHandler()
        stream = io.StringIO('false')
        parse(stream, handler)
        self.assertEqual(handler.events, [('bool', False)], "Failed to parse boolean false")
        
        handler = RecordingHandler()
        stream = io.StringIO('null')
        parse(stream, handler)
        self.assertEqual(handler.events, ['null'], "Failed to parse null")
        
        handler = RecordingHandler()
        stream = io.StringIO('123')
        parse(stream, handler)
        self.assertEqual(handler.events, [('number', 123)], "Failed to parse integer")
        
        handler = RecordingHandler()
        stream = io.StringIO('123.45')
        parse(stream, handler)
        self.assertEqual(handler.events, [('number', 123.45)], "Failed to parse float")
    
    def test_string_escapes(self):
        handler = RecordingHandler()
        stream = io.StringIO('"hello\\nworld"')
        parse(stream, handler)
        self.assertEqual(handler.events, [('string', 'hello\nworld')], "Failed to parse \\n escape")
        
        handler = RecordingHandler()
        stream = io.StringIO('"tab\\there"')
        parse(stream, handler)
        self.assertEqual(handler.events, [('string', 'tab\there')], "Failed to parse \\t escape")
        
        handler = RecordingHandler()
        stream = io.StringIO('"quote\\\"inside"')
        parse(stream, handler)
        self.assertEqual(handler.events, [('string', 'quote"inside')], "Failed to parse \\\" escape")
        
        handler = RecordingHandler()
        stream = io.StringIO('"backslash\\\\end"')
        parse(stream, handler)
        self.assertEqual(handler.events, [('string', 'backslash\\end')], "Failed to parse \\\\ escape")
    
    def test_unicode_escape(self):
        handler = RecordingHandler()
        stream = io.StringIO('"\\u00e9"')
        parse(stream, handler)
        self.assertEqual(handler.events, [('string', 'é')], "Failed to parse \\u00e9 escape")
    
    def test_nested_objects(self):
        handler = RecordingHandler()
        stream = io.StringIO('{"a":1,"b":{"c":2}}')
        parse(stream, handler)
        expected = [
            'object_start',
            ('key', 'a'), ('value', 1),
            ('key', 'b'), 'object_start',
            ('key', 'c'), ('value', 2),
            'object_end',
            'object_end'
        ]
        self.assertEqual(handler.events, expected, "Failed to parse nested objects")
    
    def test_nested_arrays(self):
        handler = RecordingHandler()
        stream = io.StringIO('[[1,2],[3,4]]')
        parse(stream, handler)
        expected = [
            'array_start', 'array_start',
            ('value', 1), ('value', 2),
            'array_end', 'array_start',
            ('value', 3), ('value', 4),
            'array_end', 'array_end'
        ]
        self.assertEqual(handler.events, expected, "Failed to parse nested arrays")
    
    def test_mixed_structures(self):
        handler = RecordingHandler()
        stream = io.StringIO('{"arr":[1,2],"obj":{"x":true}}')
        parse(stream, handler)
        expected = [
            'object_start',
            ('key', 'arr'), 'array_start',
            ('value', 1), ('value', 2),
            'array_end',
            ('key', 'obj'), 'object_start',
            ('key', 'x'), ('value', True),
            'object_end',
            'object_end'
        ]
        self.assertEqual(handler.events, expected, "Failed to parse mixed structures")
    
    def test_streaming_large_array(self):
        handler = RecordingHandler()
        # Create a JSON array with 1000 elements
        json_data = '[' + ','.join(str(i) for i in range(1000)) + ']'
        stream = io.StringIO(json_data)
        parse(stream, handler)
        
        # Verify array start and end
        self.assertEqual(handler.events[0], 'array_start', "Missing array start")
        self.assertEqual(handler.events[-1], 'array_end', "Missing array end")
        
        # Verify all 1000 numbers are parsed
        number_events = [e for e in handler.events if isinstance(e, tuple) and e[0] == 'value']
        self.assertEqual(len(number_events), 1000, "Not all 1000 elements were parsed")
        
        # Verify values are correct
        for i, event in enumerate(number_events):
            self.assertEqual(event[1], i, f"Element {i} has wrong value")
    
    def test_chunked_streaming(self):
        handler = RecordingHandler()
        json_data = '{"a":1,"b":[2,3],"c":{"d":4}}'
        # Split into chunks to test streaming
        chunks = [json_data[i:i+5] for i in range(0, len(json_data), 5)]
        stream = ChunkedStream(chunks)
        parse(stream, handler)
        
        expected = [
            'object_start',
            ('key', 'a'), ('value', 1),
            ('key', 'b'), 'array_start',
            ('value', 2), ('value', 3),
            'array_end',
            ('key', 'c'), 'object_start',
            ('key', 'd'), ('value', 4),
            'object_end', 'object_end'
        ]
        self.assertEqual(handler.events, expected, "Failed to parse chunked stream")

class ChunkedStream:
    def __init__(self, chunks):
        self.chunks = chunks
        self.current_chunk = 0
        self.position = 0
    
    def read(self, size=-1):
        if self.current_chunk >= len(self.chunks):
            return ''
        
        chunk = self.chunks[self.current_chunk]
        if self.position >= len(chunk):
            self.current_chunk += 1
            self.position = 0
            return self.read(size)
        
        end = self.position + size if size > 0 else len(chunk)
        data = chunk[self.position:end]
        self.position += len(data)
        
        if self.position >= len(chunk):
            self.current_chunk += 1
            self.position = 0
        
        return data

# This function will be provided by the implementation
def parse(stream, handler):
    # This is a placeholder - the actual implementation will be here
    # We're only testing, so we assume the real implementation exists
    pass

if __name__ == '__main__':
    unittest.main()
