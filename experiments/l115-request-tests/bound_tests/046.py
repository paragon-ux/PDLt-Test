import io
import unittest

class TestStreamingJSONParser(unittest.TestCase):
    def test_simple_string(self):
        handler = RecordingHandler()
        parse(io.StringIO('"hello"'), handler)
        self.assertEqual(handler.events, [("on_string", "hello")])

    def test_escaped_string(self):
        handler = RecordingHandler()
        parse(io.StringIO('"line1\\nline2\\ttab"'), handler)
        self.assertEqual(handler.events, [("on_string", "line1\nline2\ttab")])

    def test_unicode_escape(self):
        handler = RecordingHandler()
        parse(io.StringIO('"\\u00e9"'), handler)
        self.assertEqual(handler.events, [("on_string", "é")])

    def test_number(self):
        handler = RecordingHandler()
        parse(io.StringIO('42'), handler)
        self.assertEqual(handler.events, [("on_number", 42)])

    def test_float(self):
        handler = RecordingHandler()
        parse(io.StringIO('3.14'), handler)
        self.assertEqual(handler.events, [("on_number", 3.14)])

    def test_boolean_true(self):
        handler = RecordingHandler()
        parse(io.StringIO('true'), handler)
        self.assertEqual(handler.events, [("on_bool", True)])

    def test_boolean_false(self):
        handler = RecordingHandler()
        parse(io.StringIO('false'), handler)
        self.assertEqual(handler.events, [("on_bool", False)])

    def test_null(self):
        handler = RecordingHandler()
        parse(io.StringIO('null'), handler)
        self.assertEqual(handler.events, [("on_null", None)])

    def test_empty_object(self):
        handler = RecordingHandler()
        parse(io.StringIO('{}'), handler)
        self.assertEqual(handler.events, [
            ("on_object_start",),
            ("on_object_end",)
        ])

    def test_empty_array(self):
        handler = RecordingHandler()
        parse(io.StringIO('[]'), handler)
        self.assertEqual(handler.events, [
            ("on_array_start",),
            ("on_array_end",)
        ])

    def test_object_with_values(self):
        handler = RecordingHandler()
        parse(io.StringIO('{"key": "value", "num": 42}'), handler)
        self.assertEqual(handler.events, [
            ("on_object_start",),
            ("on_key", "key"),
            ("on_value", "value"),
            ("on_string", "value"),
            ("on_key", "num"),
            ("on_value", 42),
            ("on_number", 42),
            ("on_object_end",)
        ])

    def test_nested_structures(self):
        handler = RecordingHandler()
        parse(io.StringIO('{"arr": [1, {"inner": true}]}'), handler)
        self.assertEqual(handler.events, [
            ("on_object_start",),
            ("on_key", "arr"),
            ("on_value", [1, {"inner": True}]),
            ("on_array_start",),
            ("on_value", 1),
            ("on_number", 1),
            ("on_object_start",),
            ("on_key", "inner"),
            ("on_value", True),
            ("on_bool", True),
            ("on_object_end",),
            ("on_array_end",),
            ("on_object_end",)
        ])

    def test_large_array_streaming(self):
        class MemoryCheckerHandler(RecordingHandler):
            def __init__(self):
                super().__init__()
                self.max_memory = 0
                self.current_memory = 0

            def on_array_start(self):
                super().on_array_start()
                self.current_memory += 1
                self.max_memory = max(self.max_memory, self.current_memory)

            def on_array_end(self):
                super().on_array_end()
                self.current_memory -= 1

            def on_object_start(self):
                super().on_object_start()
                self.current_memory += 1
                self.max_memory = max(self.max_memory, self.current_memory)

            def on_object_end(self):
                super().on_object_end()
                self.current_memory -= 1

        handler = MemoryCheckerHandler()
        json_array = "[" + ",".join(str(i) for i in range(1000)) + "]"
        parse(io.StringIO(json_array), handler)
        
        array_events = [e for e in handler.events if e[0] in ("on_array_start", "on_array_end")]
        self.assertEqual(len(array_events), 2)
        self.assertEqual(array_events[0][0], "on_array_start")
        self.assertEqual(array_events[1][0], "on_array_end")
        
        number_events = [e for e in handler.events if e[0] == "on_number"]
        self.assertEqual(len(number_events), 1000)
        
        self.assertEqual(handler.max_memory, 1, "Should not hold more than one element in memory")

class RecordingHandler:
    def __init__(self):
        self.events = []

    def on_object_start(self):
        self.events.append(("on_object_start",))

    def on_object_end(self):
        self.events.append(("on_object_end",))

    def on_array_start(self):
        self.events.append(("on_array_start",))

    def on_array_end(self):
        self.events.append(("on_array_end",))

    def on_key(self, key):
        self.events.append(("on_key", key))

    def on_value(self, value):
        self.events.append(("on_value", value))

    def on_string(self, s):
        self.events.append(("on_string", s))

    def on_number(self, n):
        self.events.append(("on_number", n))

    def on_bool(self, b):
        self.events.append(("on_bool", b))

    def on_null(self):
        self.events.append(("on_null", None))

if __name__ == '__main__':
    unittest.main()
