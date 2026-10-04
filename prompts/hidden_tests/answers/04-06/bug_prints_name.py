# Wrong: a tree-walking evaluator that never compiles; print shows the variable name.
def run(source):
    env = {}
    for stmt in filter(None, (s.strip() for s in source.split(";"))):
        if stmt.startswith("let "):
            name, expr = stmt[4:].split("=", 1)
            env[name.strip()] = eval(expr, {}, dict(env))
        elif stmt.startswith("print "):
            print(stmt[6:].strip())
