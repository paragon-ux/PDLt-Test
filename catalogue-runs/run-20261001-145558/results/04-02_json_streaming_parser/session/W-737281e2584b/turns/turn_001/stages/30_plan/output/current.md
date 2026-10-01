DESIGN a parse(stream, handler) function that reads the input stream in fixed-size chunks
READ successive chunks from the provided file‑like object
MAINTAIN a state stack tracking current JSON context (object or array) and parsing mode
TOKENIZE the incoming bytes, recognizing structural characters, literals, numbers, strings, booleans, and null
WHEN a string token begins, ACCUMULATE characters handling escape sequences (\\, \n, \t, \", \uXXXX) and invoke on_string(value) upon completion
WHEN a number token is recognized, CONVERT to numeric type and invoke on_number(value)
WHEN a boolean token is recognized, INVOKE on_bool(value)
WHEN a null token is recognized, INVOKE on_null()
WHEN a key name is parsed within an object, INVOKE on_key(key)
WHEN a value token is parsed (string, number, bool, null, object, or array), INVOKE on_value(value)
WHEN an object start character '{' is encountered, PUSH object context onto stack and INVOKE on_object_start()
WHEN an object end character '}' is encountered, POP context and INVOKE on_object_end()
WHEN an array start character '[' is encountered, PUSH array context onto stack and INVOKE on_array_start()
WHEN an array end character ']' is encountered, POP context and INVOKE on_array_end()
ENSURE that at any time only the current token and minimal buffering required for escape handling are retained, avoiding full tree construction
IMPLEMENT a test harness that constructs a JSON array containing 1000 primitive elements
CREATE a mock handler that records each callback invocation count
STREAM the test JSON through the parser without loading the entire array into memory
AFTER parsing, VERIFY that the recorded callback counts match the expected numbers for 1000 elements
CONFIRM that memory usage remains bounded to a single element during the test
