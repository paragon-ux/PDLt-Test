PARSE the source code of the tiny arithmetic language
TRANSLATE parsed statements into bytecode instructions using the defined opcodes (PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT)
BUILD a bytecode list representing the compiled program
INITIALIZE an operand stack and a variable environment for the VM
EXECUTE the bytecode list sequentially, performing stack operations and variable bindings as dictated by each opcode
HANDLE integer arithmetic operations and variable assignments via the stack and environment
OUTPUT values when encountering PRINT instructions
RUN the complete compilation and execution pipeline on the test program "let x = 3 + 4 * 2; let y = x - 1; print y" to produce the expected result
