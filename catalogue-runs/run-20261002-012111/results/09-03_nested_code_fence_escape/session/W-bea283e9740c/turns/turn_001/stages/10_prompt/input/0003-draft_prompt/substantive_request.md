TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Create a function that accepts a code string and returns it wrapped in a markdown code block, ensuring that any backticks, backslashes, or raw triple‑backtick sequences inside the code are handled so the outer formatting is not broken. The function must correctly escape or adjust nested backticks, support inputs containing a single backtick (`), a backslash (\), and raw triple backticks (```), and produce valid markdown code block output. Additionally, provide test cases that demonstrate the function handling these edge‑case inputs.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- `
- \
- ```
