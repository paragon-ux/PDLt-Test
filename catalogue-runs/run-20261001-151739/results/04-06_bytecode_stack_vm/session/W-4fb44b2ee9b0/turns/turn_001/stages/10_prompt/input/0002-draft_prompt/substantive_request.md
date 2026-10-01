TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Implement a stack-based bytecode virtual machine in Python for a tiny arithmetic language that supports integer literals, addition (+), subtraction (-), multiplication (*), division (/), variables, and assignment using the syntax 'let x = expr', as well as a print statement. Create a compiler that translates source code into bytecode instructions: PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT. Develop a VM that executes the bytecode using an operand stack and a variable environment. Include both the compiler (source → bytecode) and the VM (bytecode → execution). Provide a test example where the source code 'let x = 3 + 4 * 2; let y = x - 1; print y' produces the output 10.
APPROACH/RISK NOTES:

OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- PUSH_CONST
- ADD
- SUB
- MUL
- DIV
- LOAD_VAR
- STORE_VAR
- PRINT
- let
- x
- y
- print
- 3
- 4
- 2
- 1
- +
- -
- *
- /
- Python
