TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the encoding round‑trip corruption in the provided Python code that saves text using latin-1 encoding and loads it using utf-8 encoding, identify which characters become corrupted, and supply corrected versions of both save_to_file and load_from_file that use a consistent Unicode-compatible encoding. Provide a test script that demonstrates the fix using sample text containing characters from at least three Unicode blocks: the given Latin text "Café résumé naïve Üntermensch", a CJK example, and an emoji example.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- save_to_file
- load_from_file
- latin-1
- utf-8
- text
- Café résumé naïve Üntermensch
