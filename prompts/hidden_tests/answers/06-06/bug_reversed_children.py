# Wrong: iterative, but pushes children in order onto a stack, so siblings come
# out reversed.
class Node:
    def __init__(self, val, children=None):
        self.val = val
        self.children = children or []


def serialize(node):
    if node is None:
        return "null"
    out, stack = [], [("open", node)]
    while stack:
        kind, n = stack.pop()
        if kind == "close":
            out.append(")")
        elif kind == "comma":
            out.append(",")
        else:
            out.append(f"{n.val}(")
            stack.append(("close", None))
            for k, c in enumerate(n.children):
                if k:
                    stack.append(("comma", None))
                stack.append(("open", c))
    return "".join(out)
