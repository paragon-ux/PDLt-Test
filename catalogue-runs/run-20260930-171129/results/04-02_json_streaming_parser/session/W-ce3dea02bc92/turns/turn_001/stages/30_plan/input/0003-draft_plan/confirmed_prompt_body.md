READ the request to implement a SAX-style streaming JSON parser in Python that provides a parse(stream, handler) function reading from a file-like object chunk by chunk.
DEFINE the function parse(stream, handler) to process the input stream incrementally.
FOR each JSON token encountered, CALL the corresponding handler callbacks: on_object_start, on_object_end, on_array_start, on_array_end, on_key(key), on_value(value), on_string(s), on_number(n), on_bool(b), on_null.
HANDLE escaped characters including \\, \n, \t, \" and \uXXXX correctly.
ALLOW arbitrarily deep nesting of objects and arrays.
INCLUDE a test that streams a 1000-element JSON array, verifying that all callbacks fire correctly and that no more than one element is retained in memory at any time.
