DIAGNOSE the encoding mismatch in the existing save and load implementations.
IDENTIFY the characters that become corrupted during the round‑trip.
DESIGN corrected save_to_file and load_from_file functions that use a consistent Unicode‑compatible encoding.
DEVELOP a test script that includes sample text from three Unicode blocks (Latin with diacritics, CJK, and emojis).
EXECUTE the test script to SAVE the sample text using the corrected save function, then LOAD it using the corrected load function.
VERIFY that the loaded text reproduces the original sample text exactly.
DELIVER the corrected code and test script.
