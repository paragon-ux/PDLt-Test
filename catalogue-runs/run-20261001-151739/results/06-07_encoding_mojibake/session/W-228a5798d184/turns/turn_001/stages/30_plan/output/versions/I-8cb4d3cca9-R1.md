DIAGNOSE the encoding round‑trip corruption present in the supplied Python code
IDENTIFY which characters become corrupted during the save/load process
EXPLAIN the cause of the corruption
MODIFY the function save_to_file to use a consistent encoding that preserves all characters
MODIFY the function load_from_file to read using the same consistent encoding
DEVELOP a test script that
    WRITE a string containing characters from Latin, CJK, and emoji blocks using save_to_file
    READ the string back using load_from_file
    ASSERT that the read string exactly matches the original string
COMPILE the revised definitions of save_to_file and load_from_file together with the test script for delivery
