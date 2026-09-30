DIAGNOSE the encoding round‑trip corruption caused by saving text with latin‑1 encoding and loading it with utf‑8 encoding.
IDENTIFY which characters become garbled during this process.
FIX the save_to_file function to use UTF‑8 encoding consistently.
FIX the load_from_file function to use UTF‑8 encoding consistently.
IMPLEMENT corrected versions of save_to_file and load_from_file.
CREATE a test that writes and reads a string containing characters from at least three Unicode blocks: Latin accented characters, CJK characters, and emoji.
VERIFY that the original string and the recovered string are identical.
