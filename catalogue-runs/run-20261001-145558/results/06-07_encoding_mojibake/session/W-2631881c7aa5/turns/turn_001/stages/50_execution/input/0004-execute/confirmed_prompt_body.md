DIAGNOSE which characters become corrupted due to mismatched encodings and EXPLAIN why the corruption occurs.
PROVIDE corrected save_to_file function that writes text using a consistent UTF-8 encoding.
PROVIDE corrected load_from_file function that reads text using the same UTF-8 encoding.
INCLUDE a test that writes and reads back text containing characters from at least three Unicode blocks (Latin, CJK, and emoji) and VERIFY that the original and recovered strings match.
USE the OPERATIVE TASK ENTITIES save_to_file and load_from_file exactly as listed.
