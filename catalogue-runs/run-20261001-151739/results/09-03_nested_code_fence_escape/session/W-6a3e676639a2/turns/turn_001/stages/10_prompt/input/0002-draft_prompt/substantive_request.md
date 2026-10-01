TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
The user requests a function that formats code blocks. The function must take a string of code as input and return the code wrapped in markdown backticks, correctly handling cases where the input contains backticks, backslashes, or triple backticks inside string literals so that the output formatting is not broken. The function should also include unit tests that verify correct handling of inputs containing a single backtick (`), a backslash (\), and raw triple backticks (```) within the code strings.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- `
- \
- ```
