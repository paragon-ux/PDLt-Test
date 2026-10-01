DEFINE a function format_code_block that accepts a string INPUT
ESCAPE any backslashes in INPUT by replacing \\ with \\\\
ESCAPE any literal backticks in INPUT by prefixing each backtick with a backslash
DETECT sequences of triple backticks within INPUT and replace them with escaped versions to prevent termination of outer code fences
WRAP the escaped INPUT with a surrounding code fence using triple backticks
RETURN the wrapped string as OUTPUT
CREATE a test suite for format_code_block
INCLUDE a test case where INPUT contains single backticks
INCLUDE a test case where INPUT contains backslashes
INCLUDE a test case where INPUT contains raw triple backticks
INCLUDE a test case with nested backtick sequences
ASSERT that each test case returns a correctly formatted code block without breaking the outer fence
