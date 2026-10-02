DESIGN a grammar for a tiny arithmetic language supporting integer literals, +, -, *, / operators, variable identifiers, let statements, and print statements.
PARSE the source code using the grammar to build an abstract syntax tree (AST).
COMPILE the AST into a sequence of bytecode instructions: PUSH_CONST for literals, LOAD_VAR for variable reads, STORE_VAR for let assignments, ADD, SUB, MUL, DIV for arithmetic, and PRINT for output.
IMPLEMENT a stack-based virtual machine in Python that executes the bytecode using an operand stack and a variable environment, handling each instruction accordingly.
GENERATE the Python source code for the compiler and the virtual machine.
COMPILE the test program "let x = 3 + 4 * 2; let y = x - 1; print y" into bytecode using the compiler.
EXECUTE the compiled bytecode on the virtual machine.
VERIFY that the printed output equals the expected result 10.
