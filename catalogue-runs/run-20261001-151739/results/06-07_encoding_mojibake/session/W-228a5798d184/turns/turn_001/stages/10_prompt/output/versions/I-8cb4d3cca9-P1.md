DIAGNOSE the encoding round‑trip corruption present in the supplied Python code.
IDENTIFY which characters become corrupted during the save/load process and explain the cause of the corruption.
MODIFY the function save_to_file to use a consistent encoding that preserves all characters.
MODIFY the function load_from_file to read using the same consistent encoding.
PROVIDE a test script that writes a string containing characters from at least three Unicode blocks (Latin, CJK, and emoji) using save_to_file, reads the string back using load_from_file, and asserts that the read string exactly matches the original string, demonstrating correct round‑trip handling.
INCLUDE the revised definitions of save_to_file and load_from_file in the answer.
