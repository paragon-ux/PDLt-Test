DEFINE a parse(stream, handler) function that reads the input stream incrementally
WHILE not end of stream DO
READ next chunk from stream
PROCESS characters to identify JSON tokens
IF token is object start THEN CALL handler.on_object_start()
IF token is object end THEN CALL handler.on_object_end()
IF token is array start THEN CALL handler.on_array_start()
IF token is array end THEN CALL handler.on_array_end()
IF token is key THEN CALL handler.on_key(key)
IF token is value THEN CALL handler.on_value(value)
IF token is string THEN CALL handler.on_string(string)
IF token is number THEN CALL handler.on_number(number)
IF token is boolean THEN CALL handler.on_bool(boolean)
IF token is null THEN CALL handler.on_null()
HANDLE escaped characters \\, \n, \t, \" and Unicode \uXXXX during string processing
MAINTAIN a stack to track nesting depth and allow arbitrarily deep objects and arrays
ENDWHILE
DEFINE a test that streams a JSON array of 1000 elements
CREATE a mock handler that records callback invocations
OPEN a stream that yields the large JSON array incrementally
CALL parse(stream, mock_handler)
VERIFY that callbacks fire for each element in order
VERIFY that at most one element is retained in memory at any time
