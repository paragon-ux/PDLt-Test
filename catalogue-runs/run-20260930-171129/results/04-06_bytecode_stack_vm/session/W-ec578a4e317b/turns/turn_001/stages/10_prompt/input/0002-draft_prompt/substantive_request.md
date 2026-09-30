TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a stack-based bytecode virtual machine in Python for a tiny arithmetic language. The language must support integer literals, the operators +, -, *, /, variables, assignment using the syntax let x = expr, and a print statement. Create a compiler that translates source code into bytecode instructions: PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT. Build a VM that executes the bytecode using an operand stack and a variable environment. Include both the compiler (source to bytecode) and the VM (bytecode to execution). Verify with the test program: let x = 3 + 4 * 2; let y = x - 1; print y, which should output 10.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- stack-based bytecode virtual machine
- Python
- tiny arithmetic language
- integer literals
- +
- -
- *
- /
- variables
- let x = expr
- print
- PUSH_CONST
- ADD
- SUB
- MUL
- DIV
- LOAD_VAR
- STORE_VAR
- PRINT
- let x = 3 + 4 * 2; let y = x - 1; print y
