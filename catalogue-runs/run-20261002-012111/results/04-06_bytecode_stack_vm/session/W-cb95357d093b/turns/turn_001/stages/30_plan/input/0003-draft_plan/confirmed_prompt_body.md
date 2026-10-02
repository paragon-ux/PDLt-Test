IMPLEMENT a stack-based bytecode virtual machine in Python for a tiny arithmetic language
INCLUDE support for integer literals, the arithmetic operators +, -, *, /, variables, assignment via let statements, and print statements
PROVIDE a compiler that translates source code into bytecode instructions PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT
PROVIDE a virtual machine that executes the bytecode using an operand stack and a variable environment
INCLUDE a test program "let x = 3 + 4 * 2; let y = x - 1; print y" and VERIFY that it outputs 10
