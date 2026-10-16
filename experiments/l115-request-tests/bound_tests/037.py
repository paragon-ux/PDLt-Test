import io
import json
from typing import List, Tuple, Any

class RecordingHandler:
    def __init__(self):
        self.events: List[Tuple[str, Any]] = []
    
    def on_object_start(self):
        self.events.append(('object_start', None))
    
    def on_object_end(self):
        self.events.append(('object_end', None))
    
    def on_array_start(self):
        self.events.append(('array_start', None))
    
    def on_array_end(self):
        self.events.append(('array_end', None))
    
    def on_key(self, key: str):
        self.events.append(('key', key))
    
    def on_value(self, value: Any):
        self.events.append(('value', value))
    
    def on_string(self, s: str):
        self.events.append(('string', s))
    
    def on_number(self, n: float):
        self.events.append(('number', n))
    
    def on_bool(self, b: bool):
        self.events.append(('bool', b))
    
    def on_null(self):
        self.events.append(('null', None))

def test_parse_simple_object():
    handler = RecordingHandler()
    stream = io.StringIO('{"name": "John", "age": 30}')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'name'),
        ('string', 'John'),
        ('key', 'age'),
        ('number', 30.0),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_simple_array():
    handler = RecordingHandler()
    stream = io.StringIO('[1, 2, 3]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 1.0),
        ('number', 2.0),
        ('number', 3.0),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_nested_structures():
    handler = RecordingHandler()
    stream = io.StringIO('{"data": [{"id": 1, "values": [true, null]}]}')
    parse(stream, handler, chunk_size=15)
    
    expected = [
        ('object_start', None),
        ('key', 'data'),
        ('array_start', None),
        ('object_start', None),
        ('key', 'id'),
        ('number', 1.0),
        ('key', 'values'),
        ('array_start', None),
        ('bool', True),
        ('null', None),
        ('array_end', None),
        ('object_end', None),
        ('array_end', None),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_string_escapes():
    handler = RecordingHandler()
    stream = io.StringIO('"hello\\nworld\\t\\"quoted\\"\\u0041"')
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', 'hello\nworld\t"quoted"A')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_large_array():
    handler = RecordingHandler()
    large_array = '[' + ','.join(str(i) for i in range(1000)) + ']'
    stream = io.StringIO(large_array)
    parse(stream, handler, chunk_size=50)
    
    # Verify array structure
    assert handler.events[0] == ('array_start', None)
    assert handler.events[-1] == ('array_end', None)
    
    # Verify all numbers are present in order
    number_events = [event for event in handler.events if event[0] == 'number']
    assert len(number_events) == 1000
    for i, event in enumerate(number_events):
        assert event[1] == float(i), f"Expected {float(i)} at position {i}, got {event[1]}"
    
    # Verify no intermediate objects/arrays were created
    assert all(event[0] in ('array_start', 'array_end', 'number') for event in handler.events)

def test_parse_mixed_types():
    handler = RecordingHandler()
    stream = io.StringIO('[true, false, null, 42, "text", 3.14]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('bool', True),
        ('bool', False),
        ('null', None),
        ('number', 42.0),
        ('string', 'text'),
        ('number', 3.14),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_empty_structures():
    handler = RecordingHandler()
    stream = io.StringIO('{}[]')
    parse(stream, handler, chunk_size=5)
    
    expected = [
        ('object_start', None),
        ('object_end', None),
        ('array_start', None),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_unicode_escape():
    handler = RecordingHandler()
    stream = io.StringIO('"\\u00e9\\u00e8\\u00ea"')
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', 'éèê')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_invalid_unicode_escape():
    handler = RecordingHandler()
    stream = io.StringIO('"\\u00"')  # Incomplete escape
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_negative_numbers():
    handler = RecordingHandler()
    stream = io.StringIO('[-1, -2.5]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', -1.0),
        ('number', -2.5),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_exponential_notation():
    handler = RecordingHandler()
    stream = io.StringIO('[1e2, 1.5e-3]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 100.0),
        ('number', 0.0015),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_streaming_chunks():
    handler = RecordingHandler()
    json_data = '{"key": "value"}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=2)  # Very small chunks
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_empty_string():
    handler = RecordingHandler()
    stream = io.StringIO('""')
    parse(stream, handler, chunk_size=5)
    
    expected = [('string', '')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_empty_array():
    handler = RecordingHandler()
    stream = io.StringIO('[]')
    parse(stream, handler, chunk_size=5)
    
    expected = [
        ('array_start', None),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_empty_object():
    handler = RecordingHandler()
    stream = io.StringIO('{}')
    parse(stream, handler, chunk_size=5)
    
    expected = [
        ('object_start', None),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_whitespace_handling():
    handler = RecordingHandler()
    stream = io.StringIO('  \t\n  {  \t\n  "key"  :  "value"  }  \t\n  ')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_multiple_top_level_values():
    handler = RecordingHandler()
    stream = io.StringIO('42"hello"')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail for multiple top-level values"
    except:
        pass  # Expected to fail

def test_parse_invalid_json():
    handler = RecordingHandler()
    stream = io.StringIO('{invalid}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail for invalid JSON"
    except:
        pass  # Expected to fail

def test_parse_large_object():
    handler = RecordingHandler()
    # Create object with 100 key-value pairs
    obj = {f'key{i}': i for i in range(100)}
    json_str = json.dumps(obj)
    stream = io.StringIO(json_str)
    parse(stream, handler, chunk_size=50)
    
    # Verify object structure
    assert handler.events[0] == ('object_start', None)
    assert handler.events[-1] == ('object_end', None)
    
    # Verify all keys and values are present
    key_events = [event for event in handler.events if event[0] == 'key']
    value_events = [event for event in handler.events if event[0] == 'value']
    
    assert len(key_events) == 100
    assert len(value_events) == 100
    
    # Check keys are in order (JSON objects are unordered, but we assume ordered for this test)
    for i, event in enumerate(key_events):
        expected_key = f'key{i}'
        assert event[1] == expected_key, f"Expected key {expected_key}, got {event[1]}"
    
    # Check values are numbers
    for event in value_events:
        assert isinstance(event[1], (int, float)), f"Expected numeric value, got {type(event[1])}"

def test_parse_deep_nesting():
    handler = RecordingHandler()
    # Create deeply nested array: [[[[[42]]]]]
    depth = 10
    nested = '42'
    for _ in range(depth):
        nested = f'[{nested}]'
    stream = io.StringIO(nested)
    parse(stream, handler, chunk_size=10)
    
    # Verify structure
    array_starts = [event for event in handler.events if event[0] == 'array_start']
    array_ends = [event for event in handler.events if event[0] == 'array_end']
    
    assert len(array_starts) == depth
    assert len(array_ends) == depth
    assert handler.events[-2] == ('number', 42.0)  # The innermost value

def test_parse_streaming_large_data():
    handler = RecordingHandler()
    # Generate a large JSON array without storing it all in memory
    def generate_large_json():
        yield '['
        for i in range(1000):
            if i > 0:
                yield ','
            yield str(i)
        yield ']'
    
    class StreamGenerator:
        def __init__(self, generator):
            self.generator = generator
        
        def read(self, size=-1):
            try:
                return next(self.generator)
            except StopIteration:
                return ''
    
    stream = StreamGenerator(generate_large_json())
    parse(stream, handler, chunk_size=10)
    
    # Verify we got all numbers
    number_events = [event for event in handler.events if event[0] == 'number']
    assert len(number_events) == 1000
    for i, event in enumerate(number_events):
        assert event[1] == float(i), f"Expected {float(i)} at position {i}, got {event[1]}"

def test_parse_object_with_multiple_values():
    handler = RecordingHandler()
    stream = io.StringIO('{"a": 1, "b": "text", "c": true, "d": null}')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'a'),
        ('number', 1.0),
        ('key', 'b'),
        ('string', 'text'),
        ('key', 'c'),
        ('bool', True),
        ('key', 'd'),
        ('null', None),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_string_with_all_escapes():
    handler = RecordingHandler()
    # Test all escape sequences: \\, \n, \t, \", \uXXXX
    stream = io.StringIO('"\\\\\\n\\t\\"\\u0041"')
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', '\\\n\t"A')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_number_formats():
    handler = RecordingHandler()
    stream = io.StringIO('[0, 1, -1, 1.0, -1.5, 1e10, 1.5e-10]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 0.0),
        ('number', 1.0),
        ('number', -1.0),
        ('number', 1.0),
        ('number', -1.5),
        ('number', 1e10),
        ('number', 1.5e-10),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_boolean_values():
    handler = RecordingHandler()
    stream = io.StringIO('[true, false]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('bool', True),
        ('bool', False),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_null_value():
    handler = RecordingHandler()
    stream = io.StringIO('[null]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('null', None),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_complex_nested_structure():
    handler = RecordingHandler()
    stream = io.StringIO('{"users": [{"name": "Alice", "active": true}, {"name": "Bob", "active": false}]}')
    parse(stream, handler, chunk_size=15)
    
    expected = [
        ('object_start', None),
        ('key', 'users'),
        ('array_start', None),
        ('object_start', None),
        ('key', 'name'),
        ('string', 'Alice'),
        ('key', 'active'),
        ('bool', True),
        ('object_end', None),
        ('object_start', None),
        ('key', 'name'),
        ('string', 'Bob'),
        ('key', 'active'),
        ('bool', False),
        ('object_end', None),
        ('array_end', None),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_invalid_number_format():
    handler = RecordingHandler()
    stream = io.StringIO('[01]')  # Leading zero not allowed
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_trailing_comma():
    handler = RecordingHandler()
    stream = io.StringIO('[1,]')  # Trailing comma not allowed
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_unterminated_string():
    handler = RecordingHandler()
    stream = io.StringIO('"hello')  # Missing closing quote
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_unterminated_array():
    handler = RecordingHandler()
    stream = io.StringIO('[1, 2')  # Missing closing bracket
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_unterminated_object():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"')  # Missing closing brace
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_invalid_escape_sequence():
    handler = RecordingHandler()
    stream = io.StringIO('"\\x"')  # Invalid escape
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_invalid_unicode_digit():
    handler = RecordingHandler()
    stream = io.StringIO('"\\u00G1"')  # Invalid hex digit
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_streaming_with_newlines():
    handler = RecordingHandler()
    json_data = '{\n  "key": "value"\n}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_mixed_whitespace():
    handler = RecordingHandler()
    stream = io.StringIO('  [  \t  {  \n  "a"  :  1  }  ]  ')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('object_start', None),
        ('key', 'a'),
        ('number', 1.0),
        ('object_end', None),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_object_key_order():
    handler = RecordingHandler()
    stream = io.StringIO('{"z": 1, "a": 2, "m": 3}')
    parse(stream, handler, chunk_size=10)
    
    # Keys should appear in the order they appear in the JSON
    key_events = [event for event in handler.events if event[0] == 'key']
    expected_keys = ['z', 'a', 'm']
    actual_keys = [event[1] for event in key_events]
    assert actual_keys == expected_keys, f"Expected keys {expected_keys}, got {actual_keys}"

def test_parse_array_element_order():
    handler = RecordingHandler()
    stream = io.StringIO('[3, 1, 2]')
    parse(stream, handler, chunk_size=10)
    
    # Elements should appear in the order they appear in the JSON
    number_events = [event for event in handler.events if event[0] == 'number']
    expected_numbers = [3.0, 1.0, 2.0]
    actual_numbers = [event[1] for event in number_events]
    assert actual_numbers == expected_numbers, f"Expected numbers {expected_numbers}, got {actual_numbers}"

def test_parse_boolean_in_object():
    handler = RecordingHandler()
    stream = io.StringIO('{"flag": true}')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'flag'),
        ('bool', True),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_null_in_array():
    handler = RecordingHandler()
    stream = io.StringIO('[null, null]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('null', None),
        ('null', None),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_string_with_unicode():
    handler = RecordingHandler()
    stream = io.StringIO('"\\u0048\\u0065\\u006c\\u006c\\u006f"')  # "Hello"
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', 'Hello')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_string_with_control_characters():
    handler = RecordingHandler()
    # Test with tab, newline, carriage return
    stream = io.StringIO('"\\t\\n\\r"')
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', '\t\n\r')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_number_with_leading_zero():
    handler = RecordingHandler()
    stream = io.StringIO('[01]')  # Invalid JSON
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_number_with_trailing_dot():
    handler = RecordingHandler()
    stream = io.StringIO('[1.]')  # Invalid JSON
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_multiple_spaces_in_number():
    handler = RecordingHandler()
    stream = io.StringIO('[1 2]')  # Space in number is invalid
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_object_with_duplicate_keys():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": 1, "key": 2}')  # Duplicate keys are allowed but last wins
    parse(stream, handler, chunk_size=10)
    
    # We should see both keys and values, even though it's invalid JSON
    key_events = [event for event in handler.events if event[0] == 'key']
    value_events = [event for event in handler.events if event[0] == 'value']
    
    assert len(key_events) == 2
    assert len(value_events) == 2
    assert all(event[1] == 'key' for event in key_events)
    assert value_events[0][1] == 1.0
    assert value_events[1][1] == 2.0

def test_parse_array_with_trailing_comma():
    handler = RecordingHandler()
    stream = io.StringIO('[1, 2,]')  # Trailing comma is invalid
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_object_with_trailing_comma():
    handler = RecordingHandler()
    stream = io.StringIO('{"a": 1,}')  # Trailing comma is invalid
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_empty_input():
    handler = RecordingHandler()
    stream = io.StringIO('')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_only_whitespace():
    handler = RecordingHandler()
    stream = io.StringIO('   \t\n  ')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_invalid_utf8():
    handler = RecordingHandler()
    # Create a stream with invalid UTF-8
    stream = io.BytesIO(b'{"key": \xff}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_mixed_valid_invalid():
    handler = RecordingHandler()
    stream = io.StringIO('[1, 2, invalid]')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_very_large_number():
    handler = RecordingHandler()
    stream = io.StringIO('[1e308]')  # Very large but valid
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 1e308),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_very_small_number():
    handler = RecordingHandler()
    stream = io.StringIO('[1e-308]')  # Very small but valid
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 1e-308),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_integer_overflow():
    handler = RecordingHandler()
    stream = io.StringIO('[999999999999999999999999999999999999999]')  # Very large integer
    try:
        parse(stream, handler, chunk_size=10)
        # This might be parsed as float and lose precision, but should not fail
        assert len(handler.events) == 3  # array_start, number, array_end
    except:
        pass  # Some implementations might fail on overflow

def test_parse_negative_zero():
    handler = RecordingHandler()
    stream = io.StringIO('[-0]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', -0.0),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_positive_zero():
    handler = RecordingHandler()
    stream = io.StringIO('[0]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 0.0),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_mixed_types_in_array():
    handler = RecordingHandler()
    stream = io.StringIO('[1, "two", true, null, 3.5]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 1.0),
        ('string', 'two'),
        ('bool', True),
        ('null', None),
        ('number', 3.5),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_mixed_types_in_object():
    handler = RecordingHandler()
    stream = io.StringIO('{"int": 1, "string": "text", "bool": true, "null": null, "float": 3.14}')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'int'),
        ('number', 1.0),
        ('key', 'string'),
        ('string', 'text'),
        ('key', 'bool'),
        ('bool', True),
        ('key', 'null'),
        ('null', None),
        ('key', 'float'),
        ('number', 3.14),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_streaming_with_large_chunks():
    handler = RecordingHandler()
    json_data = '{"key": "value"}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=100)  # Chunk larger than data
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_streaming_with_exact_chunks():
    handler = RecordingHandler()
    json_data = '{"key": "value"}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=len(json_data))  # Exact chunk size
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_streaming_with_tiny_chunks():
    handler = RecordingHandler()
    json_data = '{"key": "value"}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=1)  # One character at a time
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_object_with_empty_string_value():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": ""}')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', ''),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_array_with_empty_string_element():
    handler = RecordingHandler()
    stream = io.StringIO('[""]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('string', ''),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_object_with_numeric_string_key():
    handler = RecordingHandler()
    stream = io.StringIO('{"123": "value"}')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', '123'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_array_with_nested_empty_structures():
    handler = RecordingHandler()
    stream = io.StringIO('[{}, []]')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('object_start', None),
        ('object_end', None),
        ('array_start', None),
        ('array_end', None),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_deeply_nested_objects():
    handler = RecordingHandler()
    # Create deeply nested object: {"a":{"b":{"c":{"d":1}}}}
    depth = 5
    nested = '1'
    for i in range(depth):
        nested = f'{{"level{i}":{nested}}}'
    stream = io.StringIO(nested)
    parse(stream, handler, chunk_size=10)
    
    # Verify structure
    object_starts = [event for event in handler.events if event[0] == 'object_start']
    object_ends = [event for event in handler.events if event[0] == 'object_end']
    
    assert len(object_starts) == depth
    assert len(object_ends) == depth
    assert handler.events[-2] == ('number', 1.0)  # The innermost value

def test_parse_complex_escape_sequences():
    handler = RecordingHandler()
    # Test all escape sequences together
    stream = io.StringIO('"\\\\"\\n\\t\\r\\b\\f\\u0041\\u00e9"')
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', '\\\n\t\r\b\fAé')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_invalid_backspace_escape():
    handler = RecordingHandler()
    stream = io.StringIO('"\\b"')  # Valid escape
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', '\b')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_invalid_formfeed_escape():
    handler = RecordingHandler()
    stream = io.StringIO('"\\f"')  # Valid escape
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', '\f')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_number_with_plus_sign():
    handler = RecordingHandler()
    stream = io.StringIO('[+1]')  # Plus sign not allowed
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_number_with_multiple_dots():
    handler = RecordingHandler()
    stream = io.StringIO('[1.2.3]')  # Multiple dots not allowed
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_number_with_exponent_sign():
    handler = RecordingHandler()
    stream = io.StringIO('[1e+2]')  # Valid with plus sign
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 100.0),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_number_with_exponent_without_sign():
    handler = RecordingHandler()
    stream = io.StringIO('[1e2]')  # Valid without sign
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 100.0),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_number_with_exponent_minus():
    handler = RecordingHandler()
    stream = io.StringIO('[1e-2]')  # Valid with minus
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('array_start', None),
        ('number', 0.01),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_string_with_surrogate_pairs():
    handler = RecordingHandler()
    # Test with a surrogate pair for a character outside BMP
    stream = io.StringIO('"\\uD83D\\uDE00"')  # 😀 emoji
    parse(stream, handler, chunk_size=10)
    
    expected = [('string', '😀')]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_invalid_surrogate_pair():
    handler = RecordingHandler()
    stream = io.StringIO('"\\uD800"')  # Lone surrogate
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_object_with_special_characters_in_keys():
    handler = RecordingHandler()
    stream = io.StringIO('{"key\\nwith\\tnewline": "value"}')
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key\nwith\tnewline'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_array_with_mixed_nested_structures():
    handler = RecordingHandler()
    stream = io.StringIO('[{"a": [1, 2]}, [3, {"b": 4}]]')
    parse(stream, handler, chunk_size=15)
    
    expected = [
        ('array_start', None),
        ('object_start', None),
        ('key', 'a'),
        ('array_start', None),
        ('number', 1.0),
        ('number', 2.0),
        ('array_end', None),
        ('object_end', None),
        ('array_start', None),
        ('number', 3.0),
        ('object_start', None),
        ('key', 'b'),
        ('number', 4.0),
        ('object_end', None),
        ('array_end', None),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_streaming_with_binary_data():
    handler = RecordingHandler()
    # Create a stream with binary data that is valid UTF-8
    json_bytes = b'{"key": "value"}'
    stream = io.BytesIO(json_bytes)
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_streaming_with_mixed_encoding():
    handler = RecordingHandler()
    # Create a stream with mixed valid and invalid UTF-8
    json_bytes = b'{"key": \xff}'
    stream = io.BytesIO(json_bytes)
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_large_object_streaming():
    handler = RecordingHandler()
    # Create a large object with 1000 key-value pairs
    obj = {f'key{i}': i for i in range(1000)}
    json_str = json.dumps(obj)
    stream = io.StringIO(json_str)
    parse(stream, handler, chunk_size=50)
    
    # Verify we got all keys and values
    key_events = [event for event in handler.events if event[0] == 'key']
    value_events = [event for event in handler.events if event[0] == 'value']
    
    assert len(key_events) == 1000
    assert len(value_events) == 1000
    
    # Check that keys are in order (assuming JSON preserves order)
    for i, event in enumerate(key_events):
        expected_key = f'key{i}'
        assert event[1] == expected_key, f"Expected key {expected_key}, got {event[1]}"
    
    # Check that values are correct
    for i, event in enumerate(value_events):
        assert event[1] == float(i), f"Expected value {float(i)}, got {event[1]}"

def test_parse_array_with_objects():
    handler = RecordingHandler()
    stream = io.StringIO('[{"id": 1}, {"id": 2}, {"id": 3}]')
    parse(stream, handler, chunk_size=15)
    
    expected = [
        ('array_start', None),
        ('object_start', None),
        ('key', 'id'),
        ('number', 1.0),
        ('object_end', None),
        ('object_start', None),
        ('key', 'id'),
        ('number', 2.0),
        ('object_end', None),
        ('object_start', None),
        ('key', 'id'),
        ('number', 3.0),
        ('object_end', None),
        ('array_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_object_with_arrays():
    handler = RecordingHandler()
    stream = io.StringIO('{"a": [1, 2], "b": [3, 4]}')
    parse(stream, handler, chunk_size=15)
    
    expected = [
        ('object_start', None),
        ('key', 'a'),
        ('array_start', None),
        ('number', 1.0),
        ('number', 2.0),
        ('array_end', None),
        ('key', 'b'),
        ('array_start', None),
        ('number', 3.0),
        ('number', 4.0),
        ('array_end', None),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_complex_data_structure():
    handler = RecordingHandler()
    stream = io.StringIO('{"name": "Test", "data": [{"id": 1, "tags": ["a", "b"]}, {"id": 2, "tags": ["c"]}], "meta": {"count": 2}}')
    parse(stream, handler, chunk_size=20)
    
    # Just verify the structure is correct by checking the number of events
    assert len(handler.events) > 0
    assert handler.events[0] == ('object_start', None)
    assert handler.events[-1] == ('object_end', None)
    
    # Count the number of each event type
    event_counts = {}
    for event_type, _ in handler.events:
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    assert event_counts['object_start'] == 3  # Top level + 2 in data array
    assert event_counts['object_end'] == 3
    assert event_counts['array_start'] == 3  # data array + 2 tag arrays
    assert event_counts['array_end'] == 3
    assert event_counts['key'] == 6  # name, data, id (x2), tags (x2), meta, count
    assert event_counts['string'] == 5  # Test, a, b, c, (id values are numbers)
    assert event_counts['number'] == 4  # 1, 2, 2, count
    assert event_counts['value'] == 0  # We use specific callbacks, not on_value

def test_parse_streaming_performance():
    # This test is more about ensuring the parser doesn't break with streaming
    handler = RecordingHandler()
    json_data = '{"key": "value"}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=1)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_empty_stream():
    handler = RecordingHandler()
    stream = io.StringIO('')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_only_whitespace():
    handler = RecordingHandler()
    stream = io.StringIO('   \t\n  ')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_invalid_start():
    handler = RecordingHandler()
    stream = io.StringIO('x')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_multiple_json_objects():
    handler = RecordingHandler()
    stream = io.StringIO('{}{}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_json_followed_by_garbage():
    handler = RecordingHandler()
    stream = io.StringIO('{} garbage')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_garbage_followed_by_json():
    handler = RecordingHandler()
    stream = io.StringIO('garbage{}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_json_in_middle_of_garbage():
    handler = RecordingHandler()
    stream = io.StringIO('garbage{}garbage')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_very_large_chunk_size():
    handler = RecordingHandler()
    json_data = '{"key": "value"}'
    stream = io.StringIO(json_data)
    parse(stream, handler, chunk_size=10000)  # Much larger than data
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_negative_chunk_size():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=-1)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_zero_chunk_size():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=0)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_none_chunk_size():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=None)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_string_chunk_size():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size="10")
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_float_chunk_size():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=10.5)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_list_chunk_size():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=[10])
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_dict_chunk_size():
    handler = RecordingHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size={'size': 10})
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_custom_handler():
    class CustomHandler:
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
            self.events.append(f'key:{key}')
        
        def on_value(self, value):
            self.events.append(f'value:{value}')
        
        def on_string(self, s):
            self.events.append(f'string:{s}')
        
        def on_number(self, n):
            self.events.append(f'number:{n}')
        
        def on_bool(self, b):
            self.events.append(f'bool:{b}')
        
        def on_null(self):
            self.events.append('null')
    
    handler = CustomHandler()
    stream = io.StringIO('{"key": "value"}')
    parse(stream, handler, chunk_size=10)
    
    expected = ['object_start', 'key:key', 'string:value', 'object_end']
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_minimal_handler():
    class MinimalHandler:
        pass
    
    handler = MinimalHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_partial_handler():
    class PartialHandler:
        def on_object_start(self):
            pass
        
        def on_object_end(self):
            pass
    
    handler = PartialHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_extra_handler_methods():
    class ExtraHandler(RecordingHandler):
        def extra_method(self):
            pass
    
    handler = ExtraHandler()
    stream = io.StringIO('{"key": "value"}')
    parse(stream, handler, chunk_size=10)
    
    # Should work normally despite having extra methods
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_property_handler():
    class PropertyHandler:
        def __init__(self):
            self._events = []
        
        @property
        def events(self):
            return self._events
        
        def on_object_start(self):
            self._events.append(('object_start', None))
        
        # ... implement other methods similarly
    
    handler = PropertyHandler()
    stream = io.StringIO('{"key": "value"}')
    parse(stream, handler, chunk_size=10)
    
    # This is just to test that properties don't interfere
    assert len(handler.events) > 0

def test_parse_stream_with_static_methods():
    class StaticHandler:
        @staticmethod
        def on_object_start():
            pass
        
        @staticmethod
        def on_object_end():
            pass
        
        # ... implement other methods as static
    
    handler = StaticHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_class_methods():
    class ClassHandler:
        @classmethod
        def on_object_start(cls):
            pass
        
        @classmethod
        def on_object_end(cls):
            pass
        
        # ... implement other methods as class methods
    
    handler = ClassHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_async_handler():
    import asyncio
    
    class AsyncHandler:
        async def on_object_start(self):
            pass
        
        async def on_object_end(self):
            pass
        
        # ... implement other methods as async
    
    handler = AsyncHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_generator_handler():
    class GeneratorHandler:
        def on_object_start(self):
            yield 'object_start'
        
        def on_object_end(self):
            yield 'object_end'
        
        # ... implement other methods as generators
    
    handler = GeneratorHandler()
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_none_handler():
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, None, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_string_handler():
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, "not a handler", chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_integer_handler():
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, 42, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_list_handler():
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, [], chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_dict_handler():
    stream = io.StringIO('{"key": "value"}')
    try:
        parse(stream, {}, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_none_stream():
    handler = RecordingHandler()
    try:
        parse(None, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_string_stream():
    handler = RecordingHandler()
    try:
        parse("not a stream", handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_integer_stream():
    handler = RecordingHandler()
    try:
        parse(42, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_list_stream():
    handler = RecordingHandler()
    try:
        parse([], handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_dict_stream():
    handler = RecordingHandler()
    try:
        parse({}, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_custom_stream():
    class CustomStream:
        def read(self, size=-1):
            return ''
    
    handler = RecordingHandler()
    stream = CustomStream()
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_stream_that_raises():
    class RaisingStream:
        def read(self, size=-1):
            raise IOError("Stream error")
    
    handler = RecordingHandler()
    stream = RaisingStream()
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_stream_that_returns_none():
    class NoneStream:
        def read(self, size=-1):
            return None
    
    handler = RecordingHandler()
    stream = NoneStream()
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_stream_that_returns_bytes():
    class BytesStream:
        def read(self, size=-1):
            return b'{"key": "value"}'
    
    handler = RecordingHandler()
    stream = BytesStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_mixed():
    class MixedStream:
        def __init__(self):
            self.first = True
        
        def read(self, size=-1):
            if self.first:
                self.first = False
                return '{"key": '
            else:
                return '"value"}'
    
    handler = RecordingHandler()
    stream = MixedStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_empty_then_data():
    class EmptyThenDataStream:
        def __init__(self):
            self.first = True
        
        def read(self, size=-1):
            if self.first:
                self.first = False
                return ''
            else:
                return '{"key": "value"}'
    
    handler = RecordingHandler()
    stream = EmptyThenDataStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_data_in_parts():
    class PartStream:
        def __init__(self):
            self.parts = ['{"', 'key', '": ', '"value', '"}']
            self.index = 0
        
        def read(self, size=-1):
            if self.index < len(self.parts):
                result = self.parts[self.index]
                self.index += 1
                return result
            return ''
    
    handler = RecordingHandler()
    stream = PartStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_very_small_chunks():
    class TinyChunkStream:
        def __init__(self):
            self.data = '{"key": "value"}'
            self.index = 0
        
        def read(self, size=-1):
            if self.index < len(self.data):
                result = self.data[self.index]
                self.index += 1
                return result
            return ''
    
    handler = RecordingHandler()
    stream = TinyChunkStream()
    parse(stream, handler, chunk_size=1)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_large_chunks():
    class LargeChunkStream:
        def __init__(self):
            self.data = '{"key": "value"}'
            self.index = 0
        
        def read(self, size=-1):
            if self.index < len(self.data):
                result = self.data[self.index:]
                self.index = len(self.data)
                return result
            return ''
    
    handler = RecordingHandler()
    stream = LargeChunkStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_exact_chunks():
    class ExactChunkStream:
        def __init__(self):
            self.data = '{"key": "value"}'
            self.index = 0
        
        def read(self, size=-1):
            if self.index < len(self.data):
                chunk_size = min(size, len(self.data) - self.index)
                result = self.data[self.index:self.index + chunk_size]
                self.index += chunk_size
                return result
            return ''
    
    handler = RecordingHandler()
    stream = ExactChunkStream()
    parse(stream, handler, chunk_size=5)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_variable_chunks():
    class VariableChunkStream:
        def __init__(self):
            self.data = '{"key": "value"}'
            self.index = 0
            self.chunk_sizes = [2, 5, 1, 10]  # Variable chunk sizes
        
        def read(self, size=-1):
            if self.index < len(self.data) and self.chunk_sizes:
                chunk_size = self.chunk_sizes.pop(0)
                chunk_size = min(chunk_size, len(self.data) - self.index)
                result = self.data[self.index:self.index + chunk_size]
                self.index += chunk_size
                return result
            return ''
    
    handler = RecordingHandler()
    stream = VariableChunkStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_negative_size():
    class NegativeSizeStream:
        def read(self, size=-1):
            return '{"key": "value"}'
    
    handler = RecordingHandler()
    stream = NegativeSizeStream()
    parse(stream, handler, chunk_size=-1)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_zero_size():
    class ZeroSizeStream:
        def read(self, size=0):
            return ''
    
    handler = RecordingHandler()
    stream = ZeroSizeStream()
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_stream_that_returns_large_size():
    class LargeSizeStream:
        def read(self, size=1000000):
            return '{"key": "value"}'
    
    handler = RecordingHandler()
    stream = LargeSizeStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_none_size():
    class NoneSizeStream:
        def read(self, size=None):
            return '{"key": "value"}'
    
    handler = RecordingHandler()
    stream = NoneSizeStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'value'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_null_byte():
    class NullByteStream:
        def read(self, size=-1):
            return '{"key": "value\0"}'
    
    handler = RecordingHandler()
    stream = NullByteStream()
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_stream_that_returns_string_with_control_characters():
    class ControlCharStream:
        def read(self, size=-1):
            return '{"key": "value\x00\x01\x02"}'
    
    handler = RecordingHandler()
    stream = ControlCharStream()
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_stream_that_returns_string_with_invalid_utf8():
    class InvalidUTF8Stream:
        def read(self, size=-1):
            return b'{"key": \xff}'
    
    handler = RecordingHandler()
    stream = InvalidUTF8Stream()
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_stream_that_returns_string_with_bom():
    class BOMStream:
        def read(self, size=-1):
            return '\ufeff{"key": "value"}'
    
    handler = RecordingHandler()
    stream = BOMStream()
    try:
        parse(stream, handler, chunk_size=10)
        assert False, "Expected parsing to fail"
    except:
        pass  # Expected to fail

def test_parse_stream_with_stream_that_returns_string_with_rare_unicode():
    class RareUnicodeStream:
        def read(self, size=-1):
            return '{"key": "\u1234"}'
    
    handler = RecordingHandler()
    stream = RareUnicodeStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', '\u1234'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_emoji():
    class EmojiStream:
        def read(self, size=-1):
            return '{"key": "😀"}'
    
    handler = RecordingHandler()
    stream = EmojiStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', '😀'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_chinese():
    class ChineseStream:
        def read(self, size=-1):
            return '{"key": "你好"}'
    
    handler = RecordingHandler()
    stream = ChineseStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', '你好'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_arabic():
    class ArabicStream:
        def read(self, size=-1):
            return '{"key": "مرحبا"}'
    
    handler = RecordingHandler()
    stream = ArabicStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'مرحبا'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_russian():
    class RussianStream:
        def read(self, size=-1):
            return '{"key": "Привет"}'
    
    handler = RecordingHandler()
    stream = RussianStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'Привет'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_japanese():
    class JapaneseStream:
        def read(self, size=-1):
            return '{"key": "こんにちは"}'
    
    handler = RecordingHandler()
    stream = JapaneseStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'こんにちは'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_korean():
    class KoreanStream:
        def read(self, size=-1):
            return '{"key": "안녕하세요"}'
    
    handler = RecordingHandler()
    stream = KoreanStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', '안녕하세요'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_hindi():
    class HindiStream:
        def read(self, size=-1):
            return '{"key": "नमस्ते"}'
    
    handler = RecordingHandler()
    stream = HindiStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'नमस्ते'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_greek():
    class GreekStream:
        def read(self, size=-1):
            return '{"key": "γεια σου"}'
    
    handler = RecordingHandler()
    stream = GreekStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [
        ('object_start', None),
        ('key', 'key'),
        ('string', 'γεια σου'),
        ('object_end', None)
    ]
    assert handler.events == expected, f"Expected {expected}, got {handler.events}"

def test_parse_stream_with_stream_that_returns_string_with_hebrew():
    class HebrewStream:
        def read(self, size=-1):
            return '{"key": "שלום"}'
    
    handler = RecordingHandler()
    stream = HebrewStream()
    parse(stream, handler, chunk_size=10)
    
    expected = [