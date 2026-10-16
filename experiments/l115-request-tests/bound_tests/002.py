import io
import json
import unittest
from unittest.mock import Mock

class TestJSONParser(unittest.TestCase):
    def test_string_with_escapes(self):
        handler = Mock()
        stream = io.StringIO('"hello\\nworld\\t\\"quoted\\"\\\\backslash\\u0041"')
        parse(stream, handler)
        handler.on_string.assert_called_once_with('hello\nworld\t"quoted"\\backslashA')

    def test_number_parsing(self):
        handler = Mock()
        stream = io.StringIO('42')
        parse(stream, handler)
        handler.on_number.assert_called_once_with(42)

    def test_boolean_and_null(self):
        handler = Mock()
        stream = io.StringIO('true false null')
        parse(stream, handler)
        handler.on_bool.assert_any_call(True)
        handler.on_bool.assert_any_call(False)
        handler.on_null.assert_called_once()

    def test_empty_object(self):
        handler = Mock()
        stream = io.StringIO('{}')
        parse(stream, handler)
        handler.on_object_start.assert_called_once()
        handler.on_object_end.assert_called_once()

    def test_empty_array(self):
        handler = Mock()
        stream = io.StringIO('[]')
        parse(stream, handler)
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()

    def test_nested_structures(self):
        handler = Mock()
        stream = io.StringIO('{"key": [1, 2, {"inner": "value"}]}')
        parse(stream, handler)
        # Verify object and array callbacks
        handler.on_object_start.assert_called_once()
        handler.on_object_end.assert_called_once()
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()
        # Verify key and value callbacks
        handler.on_key.assert_called_with("key")
        handler.on_value.assert_any_call(1)
        handler.on_value.assert_any_call(2)
        handler.on_string.assert_called_with("value")

    def test_large_array_streaming(self):
        handler = Mock()
        # Create a JSON array with 1000 numbers
        large_array = '[' + ','.join(str(i) for i in range(1000)) + ']'
        stream = io.StringIO(large_array)
        parse(stream, handler)
        # Verify array callbacks
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()
        # Verify all 1000 numbers were processed
        self.assertEqual(handler.on_value.call_count, 1000)
        # Verify specific values at start, middle, and end
        handler.on_value.assert_any_call(0)
        handler.on_value.assert_any_call(499)
        handler.on_value.assert_any_call(999)

    def test_unicode_escape(self):
        handler = Mock()
        stream = io.StringIO('"\\u00e9\\u0416"')
        parse(stream, handler)
        handler.on_string.assert_called_once_with('éЖ')

    def test_mixed_types_in_array(self):
        handler = Mock()
        stream = io.StringIO('[1, "text", true, null, {"obj": "val"}]')
        parse(stream, handler)
        handler.on_array_start.assert_called_once()
        handler.on_array_end.assert_called_once()
        handler.on_value.assert_any_call(1)
        handler.on_string.assert_called_with("text")
        handler.on_bool.assert_called_with(True)
        handler.on_null.assert_called_once()
        handler.on_object_start.assert_called_once()
        handler.on_object_end.assert_called_once()
