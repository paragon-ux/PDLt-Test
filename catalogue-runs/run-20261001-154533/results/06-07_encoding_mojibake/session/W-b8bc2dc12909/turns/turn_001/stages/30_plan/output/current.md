DIAGNOSE the encoding round‑trip corruption that occurs when the save_to_file function writes user‑submitted text using latin‑1 and the load_from_file function reads the file using utf‑8.
IDENTIFY exactly which characters become corrupted during this round‑trip and explain why they are corrupted.
MODIFY the save_to_file function to use a consistent Unicode‑preserving encoding (e.g., UTF‑8).
MODIFY the load_from_file function to use the same encoding as save_to_file.
DEVELOP a test that writes and reads a string containing the characters Café résumé naïve Üntermensch, 你好世界, and 😊🚀 using the modified functions.
WRITE the test string to a file using the modified save_to_file function.
READ the string back from the file using the modified load_from_file function.
VERIFY that the recovered string matches the original test string.
