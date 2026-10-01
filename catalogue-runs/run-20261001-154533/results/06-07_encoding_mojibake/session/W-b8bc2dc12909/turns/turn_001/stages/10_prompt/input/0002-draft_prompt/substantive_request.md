TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Diagnose the encoding round‑trip corruption that occurs when the `save_to_file` function writes user‑submitted text using encoding='latin-1' and the `load_from_file` function reads the file using encoding='utf-8', identify exactly which characters become corrupted and why, modify both functions to use a consistent Unicode‑preserving encoding, and provide a test that writes and reads a string containing characters from the Latin block (e.g. "Café résumé naïve Üntermensch"), the CJK block (e.g. "你好世界"), and an emoji block (e.g. "😊🚀"), verifying that the recovered string matches the original.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- save_to_file
- load_from_file
- latin-1
- utf-8
- Café résumé naïve Üntermensch
- 你好世界
- 😊🚀
