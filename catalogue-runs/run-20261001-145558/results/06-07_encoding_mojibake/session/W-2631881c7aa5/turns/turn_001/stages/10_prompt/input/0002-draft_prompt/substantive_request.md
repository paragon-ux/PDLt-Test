TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose which characters become corrupted due to mismatched encodings, explain why the corruption occurs, and provide corrected save_to_file and load_from_file functions that use a consistent encoding. Include a test that writes and reads back text containing characters from at least three Unicode blocks (Latin, CJK, and emoji) and verifies that the original and recovered strings match.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- save_to_file
- load_from_file
