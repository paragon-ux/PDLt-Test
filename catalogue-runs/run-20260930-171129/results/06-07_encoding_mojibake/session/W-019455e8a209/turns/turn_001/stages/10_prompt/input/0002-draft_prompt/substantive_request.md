TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the encoding round-trip corruption caused by saving text with latin-1 encoding and loading it with utf-8 encoding, identify which characters become garbled, and fix both the save_to_file and load_from_file functions to use a consistent encoding (utf-8). Provide corrected implementations and a test that writes and reads a string containing characters from at least three Unicode blocks (Latin accented characters, CJK characters, and emoji), then verify that the original and recovered strings match.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- save_to_file
- load_from_file
- text
- Latin
- CJK
- emoji
