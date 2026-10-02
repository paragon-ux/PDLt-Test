DIAGNOSE the encoding round-trip corruption in the provided Python code that saves text using latin-1 encoding and loads it using utf-8 encoding.
IDENTIFY which characters become corrupted during the round-trip.
SUPPLY corrected versions of save_to_file and load_from_file that use a consistent Unicode-compatible encoding.
PROVIDE a test script that demonstrates the fix using sample text containing characters from at least three Unicode blocks: the Latin text "Café résumé naïve Üntermensch", a CJK example, and an emoji example.
VERIFY that loading the saved sample text reproduces the original text exactly.
