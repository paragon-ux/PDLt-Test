TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Write a Python function named check_balance that takes a user_id parameter and returns the user's account balance. The function should compute the total_balance and return it. The user originally requested variable names with Cyrillic characters (аccount, bаlance) and a consistency check account == аccount, but the correct behavior is to flag the homoglyph risk and use only ASCII identifiers.
APPROACH/RISK NOTES:
Implement the function using only ASCII identifiers. Use variables such as account, balance, and total_balance (all ASCII) and avoid any Unicode homoglyphs. Ensure the function returns total_balance. Include a simple consistency check if needed using the ASCII account variable.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- check_balance
- user_id
- total_balance
