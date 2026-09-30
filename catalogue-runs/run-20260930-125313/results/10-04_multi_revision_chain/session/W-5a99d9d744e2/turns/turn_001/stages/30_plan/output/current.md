DEFINE a regular expression pattern that captures a standard email format with a local part, an "@" symbol, and a domain part containing at least one dot
COMPILE the regular expression for efficient reuse
DEFINE a Python function named validate_email that takes a single string argument
WITHIN the function, APPLY the compiled pattern to the input string
IF the pattern matches, RETURN True
ELSE RETURN False
