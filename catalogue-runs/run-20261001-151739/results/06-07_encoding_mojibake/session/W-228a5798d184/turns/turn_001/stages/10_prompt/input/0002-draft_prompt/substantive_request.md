TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the encoding round‑trip corruption in the provided Python code, identify which characters become corrupted and why, modify the save_to_file function and the load_from_file function to use a consistent encoding that preserves all characters, and supply a test script that writes and reads a string containing characters from at least three Unicode blocks (Latin, CJK, and emoji) to verify correct round‑trip handling.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- save_to_file
- load_from_file
