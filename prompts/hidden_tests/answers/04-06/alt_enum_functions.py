# Correct with a different interface: compile_source() emits Instruction objects
# with an IntEnum opcode, and run_bytecode() returns the printed values as a list
# instead of printing them; division is true division.
from dataclasses import dataclass
from enum import IntEnum


class Op(IntEnum):
    PUSH_CONST = 1
    ADD = 2
    SUB = 3
    MUL = 4
    DIV = 5
    LOAD_VAR = 6
    STORE_VAR = 7
    PRINT = 8


@dataclass
class Instruction:
    op: Op
    arg: object = None


def compile_source(source):
    program = []
    for stmt in filter(None, (s.strip() for s in source.split(";"))):
        words = stmt.split(None, 1)
        if words[0] == "let":
            name, expr = words[1].split("=", 1)
            program += _expr(expr.split())
            program.append(Instruction(Op.STORE_VAR, name.strip()))
        elif words[0] == "print":
            program += _expr(words[1].split())
            program.append(Instruction(Op.PRINT))
        else:
            raise SyntaxError(stmt)
    return program


def _expr(tokens):
    # Shunting-yard to postfix, then emit.
    prec = {"+": 1, "-": 1, "*": 2, "/": 2}
    ops = {"+": Op.ADD, "-": Op.SUB, "*": Op.MUL, "/": Op.DIV}
    out, stack = [], []
    for t in tokens:
        if t in prec:
            while stack and prec[stack[-1]] >= prec[t]:
                out.append(Instruction(ops[stack.pop()]))
            stack.append(t)
        elif t.isdigit():
            out.append(Instruction(Op.PUSH_CONST, int(t)))
        else:
            out.append(Instruction(Op.LOAD_VAR, t))
    while stack:
        out.append(Instruction(ops[stack.pop()]))
    return out


def run_bytecode(program):
    stack, env, printed = [], {}, []
    for ins in program:
        if ins.op is Op.PUSH_CONST:
            stack.append(ins.arg)
        elif ins.op is Op.LOAD_VAR:
            stack.append(env[ins.arg])
        elif ins.op is Op.STORE_VAR:
            env[ins.arg] = stack.pop()
        elif ins.op is Op.PRINT:
            printed.append(stack.pop())
        else:
            b, a = stack.pop(), stack.pop()
            stack.append({Op.ADD: a + b, Op.SUB: a - b, Op.MUL: a * b, Op.DIV: a / b if b else 0}[ins.op])
    return printed
