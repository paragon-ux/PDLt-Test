Implement a SAX-style streaming JSON parser in Python that does NOT build a complete in-memory tree:
1. parse(stream, handler): Reads from a file-like object one chunk at a time.
2. Handler receives callbacks: on_object_start(), on_object_end(), on_array_start(), on_array_end(), on_key(key), on_value(value), on_string(s), on_number(n), on_bool(b), on_null().
3. Handle strings with escape sequences (\\, \n, \t, \", \uXXXX).
4. Handle nested structures of arbitrary depth.
5. Include a test that streams a 1000-element JSON array and verifies all callbacks fire correctly without ever holding more than one element in memory.
