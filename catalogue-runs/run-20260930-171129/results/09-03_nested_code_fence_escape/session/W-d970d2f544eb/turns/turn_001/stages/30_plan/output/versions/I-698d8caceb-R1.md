DESIGN a function signature that accepts a string containing code and returns a formatted code block string
IMPLEMENT the function to:
ESCAPE any backtick sequences in the input by wrapping the code block with a delimiter longer than any backtick run present (e.g., use triple backticks with additional backticks as needed)
PRESERVE literal backslashes and ensure they are not interpreted as escape characters
HANDLE raw triple backticks inside the input by selecting an outer delimiter that does not conflict
WRITE a suite of test cases that provide inputs containing:
SINGLE backticks
MULTIPLE consecutive backticks of varying lengths
BACKSLASH characters
TRIPLE backtick sequences embedded in the string
RUN each test, COMPARE the function output to the expected formatted block, and VERIFY that the original code structure and characters are unchanged in the output
