"""Hidden tests for 04-06: a compiler to stack bytecode and a VM that runs it.

From the prompt:
- integer literals, + - * /, variables, ``let x = expr`` and ``print``;
- statements separated by ``;`` (as in the prompt's example);
- bytecode PUSH_CONST, ADD, SUB, MUL, DIV, LOAD_VAR, STORE_VAR, PRINT;
- "let x = 3 + 4 * 2; let y = x - 1; print y" outputs 10.

The pipeline is found by name:
- a compiler (a function, or a class's compile method) feeding a VM (a class
  with run/execute, built empty or from the bytecode, or a run_bytecode-style
  function);
- otherwise a one-call runner (run, execute, interpret, ...).

What a program printed is read from stdout, from what the run returned, or from
an output list kept on the VM. Printed values compare as numbers (10 and 10.0
both pass).

When a compiler is found, its bytecode for a program that cannot be
constant-folded must use the prompt's instruction names.
"""
TEST_SECONDS = 20
_COMPILERS = ("compile", "compile_source", "compile_program", "compile_code", "compiler", "compile_to_bytecode",
              "to_bytecode", "generate_bytecode", "compile_src")
_VM_METHODS = ("run", "execute", "exec", "run_bytecode", "execute_bytecode", "interpret")
_VM_FUNCS = ("run_bytecode", "execute_bytecode", "run_vm", "vm_run", "execute", "run", "interpret_bytecode")
_RUNNERS = ("run", "execute", "run_source", "interpret", "run_program", "execute_source", "compile_and_run",
            "run_code", "evaluate", "execute_program", "run_string")
_OPCODES = ("PUSH_CONST", "ADD", "SUB", "MUL", "DIV", "LOAD_VAR", "STORE_VAR", "PRINT")


def _compilers():
    found = [(f.__name__, f) for f in functions_named(*_COMPILERS)]
    for cls in classes_with():
        for m in _COMPILERS:
            if callable(getattr(cls, m, None)):
                found.append((f"{cls.__name__}.{m}", (lambda c, m: lambda src: _call_method(c, m, src))(cls, m)))
    return found


def _call_method(cls, method, arg):
    try:
        obj = cls()
    except TypeError:
        return getattr(cls(arg), method)()
    try:
        return getattr(obj, method)(arg)
    except TypeError:
        return getattr(cls(arg), method)()


def _vms():
    found = []
    for cls in classes_with():
        if any(callable(getattr(cls, m, None)) for m in _COMPILERS):
            continue
        for m in _VM_METHODS:
            if callable(getattr(cls, m, None)):
                found.append((f"{cls.__name__}.{m}", cls, m))
                break
    found += [(f.__name__, f, None) for f in functions_named(*_VM_FUNCS)]
    return found


def _outputs(fn):
    """Run ``fn``; the printed values from stdout, the return value, or a VM's output list."""
    import contextlib
    import io

    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer):
        returned, holder = fn()
    views = [[line.strip() for line in buffer.getvalue().splitlines() if line.strip()]]
    if isinstance(returned, (list, tuple)):
        views.append(list(returned))
    elif returned is not None:
        views.append([returned])
    for name in ("output", "outputs", "printed", "out", "stdout", "prints", "output_buffer"):
        value = getattr(holder, name, None)
        if isinstance(value, (list, tuple)):
            views.append(list(value))
    return views


def _pipeline(compiler, vm):
    cname, compile_fn = compiler
    vname, target, method = vm

    def run(source):
        def go():
            code = compile_fn(source)
            if method is None:
                return target(code), None
            try:
                machine = target()
            except TypeError:
                machine = target(code)
                return getattr(machine, method)(), machine
            try:
                return getattr(machine, method)(code), machine
            except TypeError:
                machine = target(code)
                return getattr(machine, method)(), machine

        return _outputs(go)

    run.__name__ = f"{cname} -> {vname}"
    run.compile = compile_fn
    return run


def _runner(f):
    def run(source):
        return _outputs(lambda: (f(source), None))

    run.__name__ = f.__name__
    run.compile = None
    return run


def CANDIDATES():
    found = [_pipeline(c, v) for c in _compilers() for v in _vms()]
    found += [_runner(f) for f in functions_named(*_RUNNERS, params=1)]
    for cls in classes_with():
        for m in _RUNNERS:
            if callable(getattr(cls, m, None)) and not any(callable(getattr(cls, c, None)) for c in _COMPILERS):
                adapter = (lambda c, m: lambda src: _call_method(c, m, src))(cls, m)
                adapter.__name__ = f"{cls.__name__}.{m}"
                found.append(_runner(adapter))
    return found


def _number(value):
    try:
        return float(str(value).strip())
    except ValueError:
        return None


def _check(run, source, expected):
    views = run(source)
    for view in views:
        values = [_number(v) for v in view]
        if values == [float(e) for e in expected]:
            return
    raise AssertionError(f"{source!r}: expected {expected}, saw {views!r}"[:300])


def test_prompt_example(run):
    _check(run, "let x = 3 + 4 * 2; let y = x - 1; print y", [10])


def test_more_programs(run):
    _check(run, "let a = 2; let b = a * a * a; print b; print a", [8, 2])
    _check(run, "let x = 2; let x = x * x; print x", [4])
    _check(run, "let n = 10; let m = n - 3 * 2 + 1; print m", [5])
    _check(run, "let p = 20; let q = p / 4 / 5; print q", [1])
    _check(run, "let k = 7 - 2 - 1; print k", [4])
    _check(run, "let big = 1000000 * 1000; let z = big - 1; print z", [999999999])


def test_bytecode_uses_the_instruction_set(run):
    if run.compile is None:
        return
    code = run.compile("let a = 5; let b = a * a - a / a + 1; print b")
    text = repr(code)
    if hasattr(code, "__dict__"):
        text += repr(vars(code))
    names = set(NS)
    for value in NS.values():
        if isinstance(value, type):
            names |= set(dir(value))
    for op in ("PUSH_CONST", "LOAD_VAR", "STORE_VAR", "MUL", "SUB", "DIV", "ADD", "PRINT"):
        assert op in text or op in names, f"{op} is neither in the bytecode nor defined by the deliverable"


TESTS = [test_prompt_example, test_more_programs, test_bytecode_uses_the_instruction_set]
