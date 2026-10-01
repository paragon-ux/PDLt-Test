DEFINE token specifications for integer literals, identifiers, operators '+', '-', '*', '/', and keywords 'let', 'print'.
DEFINE grammar rules for:
    assignment statements using 'let' identifier '=' expression ';'
    print statements using 'print' expression ';'
    expressions supporting integer literals, identifiers, and binary operators with correct precedence.
IMPLEMENT lexer that tokenizes source code according to the token specifications.
IMPLEMENT parser that consumes tokens and builds an abstract syntax tree (AST) for the program.
IMPLEMENT code generator that traverses the AST and emits bytecode instructions:
    EMIT PUSH_CONST for integer literal values.
    EMIT LOAD_VAR for variable reads.
    EMIT STORE_VAR for variable assignments.
    EMIT ADD, SUB, MUL, DIV for corresponding binary operations.
    EMIT PRINT for print statements.
IMPLEMENT stack-based virtual machine that:
    FETCHES each bytecode instruction sequentially.
    MAINTAINS an operand stack for intermediate values.
    MAINTAINS a variable environment mapping identifiers to integer values.
    EXECUTES each instruction according to its semantics (e.g., POP two values for binary ops, apply operation, PUSH result).
    OUTPUTS the result of PRINT instructions to standard output.
INTEGRATE the compiler and virtual machine into a single Python module exposing:
    a function to compile source code to bytecode.
    a function to execute bytecode.
CREATE a test example that:
    COMPILES the source program 'let x = 3 + 4 * 2; let y = x - 1; print y'.
    EXECUTES the resulting bytecode on the virtual machine.
    VALIDATES that the printed output equals 10.
DOCUMENT usage instructions and example invocation.
