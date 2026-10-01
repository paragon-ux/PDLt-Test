CREATE a compiler in Python that parses the tiny arithmetic language supporting integer literals, the operators '+', '-', '*', '/', variables, and assignment using the syntax 'let' followed by an identifier and an expression, and also supports the 'print' statement.
TRANSLATE source code into bytecode using the instructions PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT.
BUILD a stack‑based virtual machine that executes the bytecode using an operand stack and a variable environment.
INCLUDE both the compiler (source → bytecode) and the virtual machine (bytecode → execution) in the deliverable.
PROVIDE a test example where the source code 'let x = 3 + 4 * 2; let y = x - 1; print y' evaluates to the output 10.
