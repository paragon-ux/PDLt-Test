READ the source program text
COMPILE the source program into bytecode instructions using the following opcodes: PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT
DEFINE a virtual machine that executes bytecode by maintaining an operand stack and a variable environment
FOR each instruction in the bytecode sequence DO
    IF instruction is PUSH_CONST THEN push the constant onto the operand stack
    ELSE IF instruction is ADD THEN pop two operands, add them, push the result
    ELSE IF instruction is SUB THEN pop two operands, subtract the second from the first, push the result
    ELSE IF instruction is MUL THEN pop two operands, multiply them, push the result
    ELSE IF instruction is DIV THEN pop two operands, divide the first by the second, push the result
    ELSE IF instruction is LOAD_VAR THEN load the variable's value onto the operand stack
    ELSE IF instruction is STORE_VAR THEN pop a value from the operand stack and store it in the variable
    ELSE IF instruction is PRINT THEN pop a value from the operand stack and output it
END FOR
EXECUTE the compiled bytecode for the test program let x = 3 + 4 * 2; let y = x - 1; print y
EXPECT the printed output to be 10
